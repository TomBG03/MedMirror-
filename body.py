import requests
import argparse
from openai import OpenAI
from pathlib import Path
import os 



API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = "gpt-3.5-turbo"


client = OpenAI(api_key=API_KEY)

def audio_to_text(audio_file):
    #audio_file= open("/path/to/file/audio.mp3", "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcript.text

# Create a messages array with the system message and the user message
# This will allow a more natural converation with the chatbot
# Implement function calls to the chatbot API
# sometimes a response may not be needed from the chatbot i.e. show calendar 



def generate_response(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to provide a friendly response and help the user with tasks. When necessary updating the users medication list"},
            {"role": "user", "content": prompt}
        ]

    )

    # debug print statement
    #print(response.choices[0].message.content)

    return response.choices[0].message.content

def text_to_audio(text):
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        speed=1.0,
        input=text
    )
    # with open(speech_file_path, "wb") as file:
    #     file.write(response)
    response.write_to_file(speech_file_path)



BASE_URL = 'http://localhost:3001/api'
# FUNCTIONS FOR INTERACTING WITH API ENDPOINTS

def fetch_medications():
    response = requests.get(f'{BASE_URL}/medications')
    if response.status_code == 200:
        medications = response.json()
        for medication in medications:
            med_id = medication['_id']
            print(f"{med_id} : {medication['name']} - {medication['dosage']} - {medication['time']}")
    else:
        print("Failed to fetch medications")

def add_medication(name, dosage, time):
    medication = {'name': name, 'dosage': dosage, 'time': time}
    response = requests.post(f'{BASE_URL}/medications', json=medication)
    if response.status_code == 201:
        print("Medication added:", response.json())
    else:
        print("Failed to add medication")

def delete_medication(medication_id):
    response = requests.delete(f'{BASE_URL}/medications/{medication_id}')
    if response.status_code == 200:
        print("Medication deleted")
    else:
        print("Failed to delete medication")

def main():
    parser = argparse.ArgumentParser(description='Medications Client')
    subparsers = parser.add_subparsers(dest='command')

    # Fetch medications command
    subparsers.add_parser('fetch', help='Fetch all medications')
    
    # Generate text command
    subparsers.add_parser('generate', help='Generate text from prompt')
    
    # Transcribe audio command
    subparsers.add_parser('transcribe', help='Transcribe audio')
    

    # Text to audio command
    subparsers.add_parser('text_to_audio', help='Convert text to audio')
    

    # Add medication command
    add_parser = subparsers.add_parser('add', help='Add a new medication')
    add_parser.add_argument('name', help='Name of the medication')
    add_parser.add_argument('dosage', help='Dosage of the medication')
    add_parser.add_argument('time', help='Time of administration')

    # Delete medication command
    delete_parser = subparsers.add_parser('delete', help='Delete a medication by its ID')
    delete_parser.add_argument('id', help='The ID of the medication to delete')

    args = parser.parse_args()

    if args.command == 'fetch':
        fetch_medications()
    elif args.command == 'add':
        add_medication(args.name, args.dosage, args.time)
    elif args.command == 'delete':
        delete_medication(args.id)
    
    elif args.command == 'generate':
        prompt = input("Enter a prompt: ")
        response = generate_response(prompt)
        print(response)
        text_to_audio(str(response))
    elif args.command == 'transcribe':
        audio_file = open("speech.mp3", "rb")
        transcript = audio_to_text(audio_file)
        print(transcript)
    elif args.command == 'text_to_audio':
        text = input("Enter text to convert to audio: ")
        text_to_audio(text)
    else:
        parser.print_help()



if __name__ == '__main__':
    main()
