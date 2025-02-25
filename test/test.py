import openai
import os

# OpenAI API key (replace with your actual key)
# api_key ="

os.environ["OPENAI_API_KEY"] = api_key
openai.api_key = api_key

directory_path = "."  # Change this to the directory containing M4A files

# Loop through all M4A files in the directory
for filename in os.listdir(directory_path):
    if filename.endswith(".m4a"):
        file_path = os.path.join(directory_path, filename)
        
        # Open the file and send it to the Whisper API using the new method
        with open(file_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Print the transcribed text
        print(f"Transcription for {filename}:")
        print(response.text)
        print("-" * 40)
