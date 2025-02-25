# OpenAI API key (replace with your actual key)

import openai
import os
import csv

# OpenAI API key (ensure this is set correctly in your environment)
os.environ["OPENAI_API_KEY"] = api_key
openai.api_key = os.getenv("OPENAI_API_KEY")

directory_path = "."  # Change this to the directory containing M4A files
output_csv = "transcriptions.csv"

data = []

# Get files sorted by creation time
files = sorted(
    [f for f in os.listdir(directory_path) if f.endswith(".m4a")],
    key=lambda x: os.path.getctime(os.path.join(directory_path, x))
)

# Loop through all M4A files in the directory in order of creation time
for filename in files:
    file_path = os.path.join(directory_path, filename)
    
    # Open the file and send it to the Whisper API
    with open(file_path, "rb") as audio_file:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    
    # Get transcribed text and split by '?'
    transcribed_text = response.text
    split_texts = transcribed_text.split("?")
    
    # Store results
    for text in split_texts:
        cleaned_text = text.strip()
        if cleaned_text:
            data.append([filename, cleaned_text])

# Save results to CSV
with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["Filename", "Segment"])
    writer.writerows(data)

print(f"Transcriptions saved to {output_csv}")