import os

REALTIME_AUDIO_API_URL = os.getenv(
    "REALTIME_AUDIO_API_URL",
    "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
)

print(REALTIME_AUDIO_API_URL)
