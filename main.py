import asyncio
import base64
import importlib
import json
import os
import ssl

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import Connect, VoiceResponse

from config import REALTIME_AUDIO_API_URL

# Create an SSL context (for development purposes only)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 8080))

LOG_EVENT_TYPES = [
    "error",
    "response.content.done",
    "rate_limits.updated",
    "response.done",
    "input_audio_buffer.committed",
    "input_audio_buffer.speech_stopped",
    "input_audio_buffer.speech_started",
    "session.created",
    "response.function_call_arguments.done",
    "conversation.item.created",
    "response.audio_transcript.done",
    "response.output_item.added",
    "response.content_part.done",
    "response.content_part.added",
]
SHOW_TIMING_MATH = False

INSTRUCTIONS = ""
GREETING_TEXT = ""
VOICE = ""
INTRO = ""
ADVANCED_SETTINGS = {}
TOOLS_SCHEMA = []
TOOLS = []

PARAM_TYPE = ""
PARAM_INTERMEDIATE = False
PARAM_DB = ""
PARAM_RE_RANK = False
PARAM_HYBRID_SEARCH = False
PARAM_HYBRID_SEARCH_WEIGHT = 0
PARAM_TOP_K = 0
PARAM_ENABLE_FIELDS = False
PARAM_CONTEXT_LIMIT = 0


if not OPENAI_API_KEY:
    raise ValueError("Missing the OpenAI API key. Please set it in the .env file.")

app = FastAPI()


@app.get("/", response_class=JSONResponse)
async def index_page():
    load_metadata(
        type="rag",
        intermediate=False,
        db="pg",
        re_rank=False,
        hybrid_search=False,
        hybrid_search_weight=0.5,
        top_k=10,
        enable_fields=False,
        context_limit=6000,
    )
    return {"message": INTRO}


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(
    request: Request,
    # common
    type: str = "rag",
    intermediate: bool = False,
    # rag
    db: str = "pg",
    re_rank: bool = False,
    hybrid_search: bool = False,
    hybrid_search_weight: float = 0.5,
    top_k: int = 10,
    # api
    enable_fields: bool = False,
    context_limit: int = 6000,
):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    load_metadata(
        type,
        intermediate,
        db,
        re_rank,
        hybrid_search,
        hybrid_search_weight,
        top_k,
        enable_fields,
        context_limit,
    )
    # <Say> punctuation to improve text-to-speech flow
    if INTRO:
        response.say(INTRO)
        response.pause(length=1)
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f"wss://{host}/media-stream")
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    try:
        print(
            f"Client connected with params. type: {PARAM_TYPE}, intermediate: {PARAM_INTERMEDIATE}, db: {PARAM_DB}, re_rank: {PARAM_RE_RANK}, hybrid_search: {PARAM_HYBRID_SEARCH}, hybrid_search_weight: {PARAM_HYBRID_SEARCH_WEIGHT}, top_k: {PARAM_TOP_K}, enable_fields: {PARAM_ENABLE_FIELDS}, context_limit: {PARAM_CONTEXT_LIMIT}"
        )
        TOOL_MAP = {tool.name: tool for tool in TOOLS}
        print(f"Current tools: {TOOL_MAP} \n schema: {TOOLS_SCHEMA}")

        await websocket.accept()
        responses = []

        async with websockets.connect(
            REALTIME_AUDIO_API_URL,
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
            ssl=ssl_context,
        ) as openai_ws:
            await initialize_session(openai_ws)

            # Connection specific state
            stream_sid = None
            latest_media_timestamp = 0
            last_assistant_item = None
            mark_queue = []
            response_start_timestamp_twilio = None

            async def receive_from_twilio():
                """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
                nonlocal stream_sid, latest_media_timestamp
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        if data["event"] == "media" and openai_ws.open:
                            latest_media_timestamp = int(data["media"]["timestamp"])
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data["media"]["payload"],
                            }
                            await openai_ws.send(json.dumps(audio_append))
                        elif data["event"] == "start":
                            stream_sid = data["start"]["streamSid"]
                            print(f"Incoming stream has started {stream_sid}")
                            response_start_timestamp_twilio = None
                            latest_media_timestamp = 0
                            last_assistant_item = None
                        elif data["event"] == "mark":
                            if mark_queue:
                                mark_queue.pop(0)
                except WebSocketDisconnect:
                    print("Client disconnected.")
                    if openai_ws.open:
                        await openai_ws.close()

            async def send_to_twilio():
                """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
                nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
                try:
                    async for openai_message in openai_ws:
                        response = json.loads(openai_message)
                        response_type = response.get("type", "")
                        if response_type in LOG_EVENT_TYPES:
                            print(f"Received event: {response_type}", response)

                        if (
                            response_type == "response.audio.delta"
                            and "delta" in response
                        ):
                            audio_payload = base64.b64encode(
                                base64.b64decode(response["delta"])
                            ).decode("utf-8")
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": audio_payload},
                            }
                            await websocket.send_json(audio_delta)

                            if response_start_timestamp_twilio is None:
                                response_start_timestamp_twilio = latest_media_timestamp
                                if SHOW_TIMING_MATH:
                                    print(
                                        f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms"
                                    )

                            # Update last_assistant_item safely
                            if response.get("item_id"):
                                last_assistant_item = response["item_id"]

                            await send_mark(websocket, stream_sid)

                        # if (
                        #     response_type
                        #     == "response.function_call_arguments.delta"
                        #     and "delta" in response
                        # ):

                        #     # Path to your .mp3 file
                        #     file_path = "./usecases/maintenance/custom-audio.wav"

                        #     # Read the .mp3 file in binary mode
                        #     with open(file_path, "rb") as audio_file:
                        #         # Encode the file content to Base64
                        #         audio_payload = base64.b64encode(
                        #             audio_file.read()
                        #         ).decode("utf-8")

                        #         audio_delta = {
                        #             "event": "media",
                        #             "streamSid": stream_sid,
                        #             "media": {"payload": audio_payload},
                        #         }

                        #         await websocket.send_json(audio_delta)
                        # if response_type == "response.function_call_arguments.done":

                        if response_type == "response.created":
                            responses.append(
                                {
                                    "event_id": response.get("event_id", ""),
                                    "response_id": response.get("response", {}).get(
                                        "id", ""
                                    ),
                                    "response_status": response.get("response", {}).get(
                                        "status", ""
                                    ),
                                }
                            )

                        if response_type == "response.done":
                            event_id = response.get("event_id", "")
                            current_response = response.get("response", {})
                            response_id = current_response.get("id", "")
                            status = current_response.get("status", "")

                            # Update the response in the responses list
                            for resp in responses:
                                if resp["response_id"] == response_id:
                                    resp["response_status"] = status
                                    break
                            else:
                                # If response_id not found, add a new response
                                responses.append(
                                    {
                                        "event_id": event_id,
                                        "response_id": response_id,
                                        "response_status": status,
                                    }
                                )

                            if status == "completed":
                                current_response_output = current_response.get(
                                    "output", []
                                )
                                last_response_result = (
                                    current_response_output[-1]
                                    if current_response_output
                                    else None
                                )

                                print(
                                    "Log: ",
                                    current_response,
                                    last_response_result,
                                    responses,
                                )

                                if last_response_result:
                                    try:
                                        call_id = last_response_result.get("call_id")
                                        function_name = last_response_result.get("name")
                                        args = json.loads(
                                            last_response_result.get("arguments", "{}")
                                        )

                                        intermediate_messages = [
                                            "I'm processing your request, this will just take a moment...",
                                            "Working on getting that information for you...",
                                            "Almost there, retrieving the data you need...",
                                            "Just a few more seconds while I gather the details...",
                                            "Processing your request, thank you for your patience...",
                                        ]

                                        tool_to_invoke = TOOL_MAP.get(function_name)

                                        if tool_to_invoke:
                                            message_index = 0
                                            result = None

                                            async def send_intermediate_messages():
                                                nonlocal message_index, result, responses
                                                if PARAM_INTERMEDIATE:
                                                    is_last_response_active = (
                                                        responses[-1]["response_status"]
                                                        == "in_progress"
                                                    )
                                                    print(
                                                        f"Intermediate messages enabled. {is_last_response_active}"
                                                    )

                                                    while result is None:
                                                        # Wait for 3 second to see if the result is ready
                                                        await asyncio.sleep(3)
                                                        if (
                                                            not result
                                                            and not is_last_response_active
                                                        ):
                                                            current_msg = f"Respond to the user with waiting message to avoid silence: {intermediate_messages[message_index % len(intermediate_messages)]}"
                                                            await send_conversation_item(
                                                                openai_ws,
                                                                current_msg,
                                                                is_last_response_active,
                                                            )
                                                            message_index += 1
                                                            break  # Exit the loop after sending the message

                                            # Run intermediate message sender and tool invocation concurrently
                                            message_task = asyncio.create_task(
                                                send_intermediate_messages()
                                            )
                                            try:
                                                if PARAM_TYPE == "rag":
                                                    args["db"] = PARAM_DB
                                                    args["re_rank"] = PARAM_RE_RANK
                                                    args["hybrid_search"] = (
                                                        PARAM_HYBRID_SEARCH
                                                    )
                                                    args["hybrid_search_weight"] = (
                                                        PARAM_HYBRID_SEARCH_WEIGHT
                                                    )
                                                    args["top_k"] = PARAM_TOP_K
                                                elif PARAM_TYPE == "api":
                                                    args["enable_fields"] = (
                                                        PARAM_ENABLE_FIELDS
                                                    )
                                                    args["context_limit"] = (
                                                        PARAM_CONTEXT_LIMIT
                                                    )
                                                print("Args to invoke tool:", args)
                                                result = await asyncio.to_thread(
                                                    tool_to_invoke.func, **args
                                                )
                                            finally:
                                                message_task.cancel()  # Stop intermediate messages

                                            if result:
                                                print(
                                                    f"Received function call result: {result}"
                                                )
                                                # Send the final response
                                                function_output_event = {
                                                    "type": "conversation.item.create",
                                                    "item": {
                                                        "type": "function_call_output",
                                                        "call_id": call_id,
                                                        "output": result,
                                                    },
                                                }
                                                await openai_ws.send(
                                                    json.dumps(function_output_event)
                                                )

                                                # Send final response
                                                response_create_event = {
                                                    "type": "response.create",
                                                    "response": {
                                                        "modalities": ["text", "audio"],
                                                        "instructions": f"Formulate an answer strictly based on the provided context chunks without adding external knowledge or assumptions. context: {result}. Be concise and friendly.",
                                                    },
                                                }
                                                await openai_ws.send(
                                                    json.dumps(response_create_event)
                                                )

                                    except Exception as e:
                                        print(
                                            "Error processing question via Assistant:",
                                            e,
                                        )
                                        await send_conversation_item(
                                            openai_ws,
                                            f"Respond to the user with apologetic message. ' apologize, but I'm having trouble processing your request right now. Is there anything else I can help you with?'",
                                        )

                        # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                        if response_type == "input_audio_buffer.speech_started":
                            print("Speech started detected.")
                            if last_assistant_item:
                                print(
                                    f"Interrupting response with id: {last_assistant_item}"
                                )
                                await handle_speech_started_event()

                        if response_type == "error":
                            print("Error from OpenAI:", response["error"]["message"])

                except Exception as e:
                    print(f"Error in send_to_twilio: {e}")

            async def handle_speech_started_event():
                """Handle interruption when the caller's speech starts."""
                nonlocal response_start_timestamp_twilio, last_assistant_item
                print("Handling speech started event.")
                if mark_queue and response_start_timestamp_twilio is not None:
                    elapsed_time = (
                        latest_media_timestamp - response_start_timestamp_twilio
                    )
                    if SHOW_TIMING_MATH:
                        print(
                            f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms"
                        )

                    if last_assistant_item:
                        if SHOW_TIMING_MATH:
                            print(
                                f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms"
                            )

                        truncate_event = {
                            "type": "conversation.item.truncate",
                            "item_id": last_assistant_item,
                            "content_index": 0,
                            "audio_end_ms": elapsed_time,
                        }
                        await openai_ws.send(json.dumps(truncate_event))

                    await websocket.send_json(
                        {"event": "clear", "streamSid": stream_sid}
                    )

                    mark_queue.clear()
                    last_assistant_item = None
                    response_start_timestamp_twilio = None

            async def send_mark(connection, stream_sid):
                if stream_sid:
                    mark_event = {
                        "event": "mark",
                        "streamSid": stream_sid,
                        "mark": {"name": "responsePart"},
                    }
                    await connection.send_json(mark_event)
                    mark_queue.append("responsePart")

            await asyncio.gather(receive_from_twilio(), send_to_twilio())

    except WebSocketDisconnect:
        print("WebSocket disconnected by the client.")
    except Exception as e:
        print(f"Unexpected error in media stream: {e}")
    finally:
        await websocket.close()


def load_metadata(
    type,
    intermediate,
    db,
    re_rank,
    hybrid_search,
    hybrid_search_weight,
    top_k,
    enable_fields,
    context_limit,
):
    module_name = f"usecases.{type}.config"
    module = importlib.import_module(module_name)

    global INTRO
    global INSTRUCTIONS
    global GREETING_TEXT
    global VOICE
    global ADVANCED_SETTINGS
    global TOOLS_SCHEMA
    global TOOLS
    global PARAM_TYPE
    global PARAM_INTERMEDIATE
    global PARAM_DB
    global PARAM_RE_RANK
    global PARAM_HYBRID_SEARCH
    global PARAM_HYBRID_SEARCH_WEIGHT
    global PARAM_TOP_K
    global PARAM_ENABLE_FIELDS
    global PARAM_CONTEXT_LIMIT

    INTRO = module.INTRO_TEXT
    INSTRUCTIONS = module.SYSTEM_INSTRUCTIONS
    GREETING_TEXT = module.GREETING_TEXT
    VOICE = module.VOICE
    ADVANCED_SETTINGS = module.ADVANCED_SETTINGS
    TOOLS_SCHEMA = module.TOOLS_SCHEMA
    TOOLS = module.TOOLS
    PARAM_TYPE = type
    PARAM_INTERMEDIATE = intermediate
    PARAM_DB = db
    PARAM_RE_RANK = re_rank
    PARAM_HYBRID_SEARCH = hybrid_search
    PARAM_HYBRID_SEARCH_WEIGHT = hybrid_search_weight
    PARAM_TOP_K = top_k
    PARAM_ENABLE_FIELDS = enable_fields
    PARAM_CONTEXT_LIMIT = context_limit


async def send_conversation_item(ws, text, is_last_response_active=False):
    """Send initial conversation item if AI talks first."""
    if is_last_response_active:
        print(
            "Skipping conversation item creation as last response is active. Text:",
            text,
        )
        return

    await ws.send(
        json.dumps(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}],
                },
            }
        )
    )

    await ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": ADVANCED_SETTINGS["turn_detection"]
            or {"type": "server_vad"},
            "input_audio_format": ADVANCED_SETTINGS["input_audio_format"]
            or "g711_ulaw",
            "output_audio_format": ADVANCED_SETTINGS["output_audio_format"]
            or "g711_ulaw",
            "voice": VOICE,
            "instructions": INSTRUCTIONS,
            "modalities": ADVANCED_SETTINGS["modalities"] or ["text", "audio"],
            "temperature": ADVANCED_SETTINGS["temperature"] or 0.8,
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto",
        },
    }
    print("Sending session update:", json.dumps(session_update))
    await ws.send(json.dumps(session_update))

    # Uncomment the next line to have the AI speak first
    await send_conversation_item(ws, GREETING_TEXT)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
