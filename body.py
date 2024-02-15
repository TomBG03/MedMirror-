import requests
import argparse
from openai import OpenAI
from pathlib import Path
import os 
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
from playsound import playsound

API_KEY = os.getenv('OPENAI_API_KEY')
# client_id = os.getenv('CLIENT_ID')
# client_secret = os.getenv('CLIENT_SECRET')
# tennant_id = os.getenv('TENANT_ID')
CLIENT_ID = "a5b0dcf9-41c8-455c-bfac-c7cfa4a4cf8b"
TENNANT_ID = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"
CLIENT_SECRET = "xdU8Q~LreG4f.pVTirI7uguXsAUiS-pL_rkJkau-"
client_id = CLIENT_ID
client_secret = CLIENT_SECRET
tennant_id = TENNANT_ID
MODEL = "gpt-3.5-turbo"
MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant designed to provide a friendly response and help the user with questions. The medications provided are the medications prescribed by the doctor which the user shoudl take. The dosage and time have been set by a medical professional. When asked about medication please refer to provided info"},
    ]

client = OpenAI(api_key=API_KEY)


def get_access_token(client_id, tenant_id, client_secret):
    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {
        "client_id": client_id,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=body)
    response_json = response.json()
    print(response_json)
    access_token = response_json.get("access_token")
    return access_token

def get_outlook_events(access_token):
    url = "https://graph.microsoft.com/v1.0/me/events"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    events = response.json()
    print(events)
    return events

def audio_to_text(audio_file):
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcript.text


# Create a messages array with the system message and the user message
# This will allow a more natural converation with the chatbot
# Implement function calls to the chatbot API
# sometimes a response may not be needed from the chatbot i.e. show calendar 


def generate_response():
    response = client.chat.completions.create(
        model=MODEL,
        messages=MESSAGES,
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

def get_info():
    meds = get_medications()

    # Update system with new information when needed 
    # For example: A new medication has been added 

def add_event(title, startTime, endTime, description=None, location=None, attendees=None):
    
    event = {'Title': title, 'description': description, 'location': location, 'startTime': startTime, 'endTime': endTime, 'attendees': attendees}
    response = requests.post(f'{BASE_URL}/calendar', json=event)
    if response.status_code == 201:
        print("Event added:", response.json())
    else:
        print("Failed to add event")



def get_medications():
    meds = []
    response = requests.get(f'{BASE_URL}/medications')
    if response.status_code == 200:
        medications = response.json()
        for medication in medications:
            meds.append(medication)
    #         med_id = medication['_id']
    #         #print(f"{med_id} : {medication['name']} - {medication['dosage']} - {medication['time']}")
    #         meds.append(f"{med_id} : {medication['name']} - {medication['dosage']} - {medication['time']}")
    # else:
    #     return (f"You have no medications")
    # return meds
    return meds
    

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


def record_audio(duration=5, fs=44100, filename='output.wav'):
    """
    Record audio from the microphone and save it to a file.
    
    Parameters:
    - duration: Length of the recording in seconds
    - fs: Sampling frequency
    - filename: Name of the file where the recording will be saved
    """
    print("Recording...")
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()  # Wait until recording is finished
    print("Finished recording. Saving file...")
    write(filename, fs, np.int16(myrecording * 32767))
    print(f"File saved as {filename}")


def get_calendar_events():
    access_token = get_access_token(client_id, tennant_id, client_secret)
    print(f"ACCESS TOKEN: {access_token}")
    events = get_outlook_events(access_token)
    print(events)

def generate():
    prompt = input("Enter a prompt: ")
    if "medication" in prompt:
        med_info = "current medications (in format name - dosage - time)"
        medications = get_medications()
        for medication in medications:
            #print(f"{medications['_id']} : {medication['name']} - {medication['dosage']} - {medication['time']}")
            med_info = med_info + f"{medication['name']} - {medication['dosage']} - {medication['time']}"
        MESSAGES.append({"role": "user", "content": prompt + med_info})
    else:
        MESSAGES.append({"role": "user", "content": prompt})
    response = generate_response()
    print(response)
    text_to_audio(str(response))
    
def chat():
    while True:
        record_audio()
        audio_file = open("output.wav", "rb")
        transcript = audio_to_text(audio_file)
        if "exit" in transcript.lower():
            break
        MESSAGES.append({"role": "user", "content": transcript})
        response = generate_response()
        text_to_audio(str(response))
        MESSAGES.append({"role": "assistant", "content": response})
        playsound("speech.mp3")

def main():
    parser = argparse.ArgumentParser(description='Medications Client')
    subparsers = parser.add_subparsers(dest='command')

    # get outlook events
    subparsers.add_parser('calendar', help='Fetch all calendar events')

    # send a message to the chatbot
    subparsers.add_parser('chat', help='Send a message to the chatbot')

    # record user audio 
    subparsers.add_parser('record', help='Record audio')

    # add calendar event command
    subparsers.add_parser('add_event', help='add calendar event')

    # Fetch medications command
    subparsers.add_parser('fetch', help='Fetch all medications')
    
    # Add medication command
    add_parser = subparsers.add_parser('add', help='Add a new medication')
    add_parser.add_argument('name', help='Name of the medication')
    add_parser.add_argument('dosage', help='Dosage of the medication')
    add_parser.add_argument('time', help='Time of administration')

    # Delete medication command
    delete_parser = subparsers.add_parser('delete', help='Delete a medication by its ID')
    delete_parser.add_argument('id', help='The ID of the medication to delete')
    


    # Generate text command
    subparsers.add_parser('generate', help='Generate text from prompt')
    
    # Transcribe audio command
    subparsers.add_parser('transcribe', help='Transcribe audio')
    
    # Text to audio command
    subparsers.add_parser('text_to_audio', help='Convert text to audio')



    args = parser.parse_args()

    if args.command == 'fetch':
        get_medications()
    elif args.command == 'add':
        add_medication(args.name, args.dosage, args.time)
    elif args.command == 'delete':
        delete_medication(args.id)
    
    elif args.command == 'calendar':
        get_calendar_events()

    elif args.command == 'add_event':
        title = input('Name of event')
        startTime = input('start time')
        endTime = input('end time')
        add_event(title=title, startTime=startTime, endTime=endTime)


    elif args.command == 'record':
        record_audio()

    elif args.command == 'chat':
        chat()

    elif args.command == 'generate':
        generate()

    elif args.command == 'transcribe':
        audio_file = open("input.mp3", "rb")
        transcript = audio_to_text(audio_file)
        print(transcript)
    elif args.command == 'text_to_audio':
        text = input("Enter text to convert to audio: ")
        text_to_audio(text)
    else:
        parser.print_help()



if __name__ == '__main__':
    main()




