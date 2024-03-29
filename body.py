import requests
import argparse
from openai import OpenAI
from pathlib import Path
import os 
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
from playsound import playsound
import json
from termcolor import colored
import asyncio
import configparser
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph import Graph
from vosk import Model, KaldiRecognizer
import pyaudio
import wave
import audioop
from datetime import datetime

##########################################
# OPEN AI API                            #
##########################################
API_KEY = os.getenv('OPENAI_API_KEY')
##########################################

##########################################
# CHATBOT FUNCTIONS                      #
##########################################
MODEL = "gpt-3.5-turbo-1106"

client = OpenAI(api_key=API_KEY)

def audio_to_text(audio_file):
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcript.text

def generate_function_response(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice='auto'
    )
    return response.choices[0].message

def generate_chat_response(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content

def text_to_audio(text):
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        speed=1.0,
        input=text
    )
    response.write_to_file(speech_file_path)
##########################################

 
##########################################
# DEFINING WHAT FUNCTIONS FOR CHATBOT   #
#           API TO EXECUTE              #     
##########################################
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_medications",
            "description": "get user's current prescribed medications in the format 'medication_id: medication name - dosage - time'",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_medication",
            "description": "add a new prescribed medication to the user's list of medications. Each required parameter must be specified explicitly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "name of the medication",
                    },
                    "dosage": {
                        "type": "string",
                        "description": "The dosage of the medication in mg/g/ml, must be said explicitly.",
                    },
                    "time": {
                        "type": "string",
                        "description": "Time of day to take the medication",
                    }
                },
                "required": ["name", "dosage", "time"]
            },
        }
    }, 
    {
        "type": "function",
        "function": {
            "name": "delete_medication",
            "description": "delete/remove a medication from the user's list of medications by its medication_id",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_id": {
                        "type": "string",
                        "description": "ID of the medication",
                    },
                },
                "required": ["medication_id"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_conversation",
            "description": "Ends the current conversation with the user, can be inferred from users input or silence, e.g. 'goodbye', 'bye', 'stop', 'end conversation', 'that's all thank you' etc.",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": "Add an event to the user's calendar, can infer details from user's input",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Subject of the event",
                    },
                    "start": {
                        "type": "string",
                        "description": "Start time of the event, must be in format 'YYYY-MM-DDTHH:MM:SS'",
                    },
                    "end": {
                        "type": "string",
                        "description": "End time of the event, must be in format 'YYYY-MM-DDTHH:MM:SS",
                    },
                    "location": {
                        "type": "string",
                        "description": "Location of the event",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the event",
                    }
                },
                "required": ["subject", "start", "end"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Get the current date and time",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "get users calendar events in the format 'event_id: event subject - start time - end time - description - location'",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": "delete/remove a calendar event from the user's calendar by using the event_id",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "event id of the event to delete",
                    },
                },
                "required": ["medication_id"]
            },
        }
    }
    
]
##########################################

##########################################
# EXECUTING FUNCTIONS FOR CHATBOT API    #
##########################################


def execute_function_call(tool_call):
    func_name = tool_call.function.name 
    if func_name == "get_medications":
        results = get_medications()
    elif func_name == "add_medication":
        args = json.loads(tool_call.function.arguments)
        name = args["name"]
        dosage = args["dosage"]
        time = args["time"]
        results = add_medication(name, dosage, time)
    elif func_name == "delete_medication":
        args = json.loads(tool_call.function.arguments)
        medication_id = args["medication_id"]
        results = delete_medication(medication_id)




    elif func_name == "get_calendar_events":
        results = get_calendar_events()

    elif func_name == "add_calendar_event":
        args = json.loads(tool_call.function.arguments)
        subject = args["subject"]
        start = args["start"]
        end = args["end"]
        location = args.get("location", None)
        description = args.get("description", None)
        results = add_calendar_event(subject, start, end, location, description)
    elif func_name == "delete_event":
        args = json.loads(tool_call.function.arguments)
        event_id = args["event_id"]
        results = delete_calendar_event(event_id)

    elif func_name == "get_current_datetime":
        results = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    elif func_name == "end_conversation":
        results = "Conversation ended"
    else:
        results = f"Error: function {func_name} does not exist"
    return results
 
##########################################

##########################################
# HARDWARE INTERACTION FUNCTIONS        #
##########################################
# def record_audio(duration=5, fs=44100, filename='output.wav'):
#     print("Recording...")
#     myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float64')
#     sd.wait() 
#     print("Finished recording. Saving file...")
#     write(filename, fs, np.int16(myrecording * 32767))
#     print(f"File saved as {filename}")


# def listen_for_keyword(keyword="thomas", model_path = "/Users/annushka/Documents/GitHub/MedMirror-/vosk-model-en-us-0.22"):
#     model = Model(model_path)
#     rec = KaldiRecognizer(model, 16000)
#     rec.SetWords(True)

#     p = pyaudio.PyAudio()
#     stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
#     stream.start_stream()

#     print("Listening for activation keyword...")

#     frame_duration_ms = 10  # Smaller frame duration (in milliseconds)
#     frames_per_buffer = int(16000 * frame_duration_ms / 1000)

#     while True:
#         data = stream.read(frames_per_buffer, exception_on_overflow=False)
#         if rec.AcceptWaveform(data):
#             result = json.loads(rec.Result())
#             if keyword.lower() in [word['word'].lower() for word in result.get('result', [])]:
#                 print(f"Activation keyword '{keyword}' detected. Start speaking.")
#                 record_with_vad(stream, rec, model, frames_per_buffer)
#                 break


# def record_with_vad(stream, rec, model, frames_per_buffer):
#     rec = KaldiRecognizer(model, 16000)
#     rec.SetWords(True)
    
#     print("Recording... Speak now.")
#     recording = []
#     silence_counter = 0
#     silence_threshold = 300  # Adjust this for quicker response to silence

#     while True:
#         data = stream.read(frames_per_buffer, exception_on_overflow=False)
#         if rec.AcceptWaveform(data):
#             result = json.loads(rec.Result())
#             recording.append(result.get('text', ''))
#             silence_counter = 0
#         else:
#             silence_counter += 1
#             if silence_counter > silence_threshold:
#                 print("Stopping recording due to silence.")
#                 break

#     full_text = ' '.join(recording)
#     print("Recorded Text:", full_text)
#     # send the recorded audio to the chatbot



def record_audio_to_file(output_filename, stream, rec, silence_duration=2):
    # Setup wave file writer
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)

    # Initialize variables for tracking silence
    num_silent_frames = 0

    #  rate / chunk * no.seconds for no. seconds of silence
    max_silent_frames = int(16000 / 4096 * silence_duration)  
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        wf.writeframes(data)  # Write audio data to file

        # Check if the current frame is silent
        is_silent = audioop.rms(data, 2) < 1200  # You can adjust the threshold value

        if is_silent:
            num_silent_frames += 1
        else:
            num_silent_frames = 0  # Reset to 0 if noise is detected

        # Stop recording if silence has been detected for the duration specified
        if num_silent_frames > max_silent_frames:
            print("Silence detected, stopping recording")
            break

    wf.close()  # Close the wave file

def listen_for_keyword(stream, rec, keyword="activate"):
    print("Listening for activation keyword...")
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if keyword.lower() in [word['word'].lower() for word in result.get('result', [])]:
                print(f"Activation keyword '{keyword}' detected.")
                return True
    return False
##########################################




##########################################
# OUTLOOKK AI API                        #
##########################################
EMAIL_RECIPIENT = "lu21864@bristol.ac.uk"

# try:
#     function call
# except ODataError as odata_error:
#             print('Error:')
#             if odata_error.error:
#                 print(odata_error.error.code, odata_error.error.message)


# <GreetUserSnippet>
async def greet_user(graph: Graph):
    user = await graph.get_user()
    if user:
        print('Hello,', user.display_name)
        # For Work/school accounts, email is in mail property
        # Personal accounts, email is in userPrincipalName
        print('Email:', user.mail or user.user_principal_name, '\n')
# </GreetUserSnippet>

# <DisplayAccessTokenSnippet>
async def display_access_token(graph: Graph):
    token = await graph.get_user_token()
    print('User token:', token, '\n')
# </DisplayAccessTokenSnippet>

# <ListInboxSnippet>
async def list_inbox(graph: Graph):
    message_page = await graph.get_inbox()
    if message_page and message_page.value:
        # Output each message's details
        for message in message_page.value:
            print('Message:', message.subject)
            if (
                message.from_ and
                message.from_.email_address
            ):
                print('  From:', message.from_.email_address.name or 'NONE')
            else:
                print('  From: NONE')
            print('  Status:', 'Read' if message.is_read else 'Unread')
            print('  Received:', message.received_date_time)

        # If @odata.nextLink is present
        more_available = message_page.odata_next_link is not None
        print('\nMore messages available?', more_available, '\n')
# </ListInboxSnippet>


async def send_mail(graph: Graph):
    # Send mail to the signed-in user
    # Get the user for their email address
    user = await graph.get_user()
    if user:
        user_email = EMAIL_RECIPIENT
        # user_email = user.mail or user.user_principal_name

        await graph.send_mail('Testing Microsoft Graph', 'Hey Anna look at this!', user_email or '')
        print('Mail sent.\n')


# LIST CALENDAR EVENTS
async def list_calendar_events(graph: Graph):
    event_page = await graph.get_calendar_events()
    if event_page and event_page.value:
        # Output each event's details
        for event in event_page.value:
            print('Event:', event.subject)
            if (
                event.organizer and
                event.organizer.email_address
            ):
                print('  Organizer:', event.organizer.email_address.name or 'NONE')
            else:
                print('  Organizer: NONE')
                print('  Start:', event.start.date_time)
                print('  End:', event.end.date_time)

        # If @odata.nextLink is present
        more_available = event_page.odata_next_link is not None
        print('\nMore events available?', more_available, '\n') 

##########################################






##########################################
# MEDICATIONS API ENDPOINTS              #
##########################################
BASE_URL = 'http://localhost:3001/api'
def get_medications():
    meds = []
    response = requests.get(f'{BASE_URL}/medications')
    if response.status_code == 200:
        medications = response.json()
        for medication in medications:
            med_id = medication['_id']
            meds.append(f"{med_id} : {medication['name']} - {medication['dosage']} - {medication['time']}")
    return meds
    

def add_medication(name, dosage, time):
    medication = {'name': name, 'dosage': dosage, 'time': time}
    response = requests.post(f'{BASE_URL}/medications', json=medication)
    if response.status_code == 201:
        return("Medication added:", response.json())
    else:
        return("Failed to add medication")


def delete_medication(medication_id):
    response = requests.delete(f'{BASE_URL}/medications/{medication_id}')
    if response.status_code == 200:
        return("Medication deleted")
    else:
        return("Failed to delete medication, would you like me to try again?")

##########################################
# Calendar API ENDPOINTS                 #
##########################################

def get_calendar_events():
    myEvents = []
    response = requests.get(f'{BASE_URL}/calendar')
    if response.status_code == 200:
        events = response.json()
        for event in events:
            event_id = event['_id']
            if event['location']:
                myEvents.append(f"{event_id} : {event['subject']} - {event['start']} - {event['end']} - {event['location']}")
            else:
                myEvents.append(f"{event} : {event['subject']} - {event['start']} - {event['end']} - No location")
    return myEvents


def add_calendar_event(subject, start, end, location, description):
    event = {'subject': subject, 'start': start, 'end': end, 'location': location, 'description': description}
    response = requests.post(f'{BASE_URL}/calendar', json=event)
    if response.status_code == 201:
        return("Medication added:", response.json())
    else:
        return("Failed to add calendar event")

def delete_calendar_event(event_id):
    response = requests.delete(f'{BASE_URL}/calendar/{event_id}')
    if response.status_code == 200:
        return("Event deleted")
    else:
        return("Failed to delete event, would you like me to try again?")




##########################################



##########################################
# MAIN FUNCTIONS                         #
##########################################
MESSAGES = [
    {"role": "system", "content": "You are a friendly assistant here to help the user with their health and wellness needs."},
    {"role": "system", "content": "Respond in English and do not switch languages."},
    {"role": "system", "content": "You can answer questions about their medications, schedule, and general health questions."},
    {"role": "system", "content": "You can also add new medications to their list or delete existing ones."},
    {"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous, make sure the user is specifc about what they want."},
]

def generate():
    end_of_conversation = False
    while not end_of_conversation:
        global MESSAGES
        prompt = input("Enter a prompt: ")
        MESSAGES.append({"role": "user", "content": prompt})
        assistant_message = generate_function_response(MESSAGES)
        
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            print(assistant_message)
            for call in assistant_message.tool_calls:
                results = execute_function_call(call) 
                MESSAGES.append({"role": "function", "tool_call_id": call.id, "name": call.function.name, "content": str(results)})
                if "conversation ended" in str(results).lower():
                    end_of_conversation = True
            reply = generate_chat_response(MESSAGES)
            MESSAGES.append({"role": "assistant", "content": reply})
        else:
            assistant_message = generate_chat_response(MESSAGES)
            MESSAGES.append({"role": "assistant", "content": assistant_message})
        pretty_print_conversation(MESSAGES)
    
def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

def conversation():
    ACTIVATION_KEYWORD="activate"
    model_path = "/Users/annushka/Documents/GitHub/MedMirror-/vosk-model-en-us-0.22"
    output_filename = "output.wav"

    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    stream.start_stream()

    try:
        while True:
            if listen_for_keyword(stream, rec, ACTIVATION_KEYWORD):
                record_audio_to_file(output_filename, stream, rec)
                chat()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()    



# This will become the main fucntion that listens for the keyword and then starts the conversation
def tester_main():
    model_path = "/Users/annushka/Documents/GitHub/MedMirror-/vosk-model-en-us-0.22"
    output_filename = "output.wav"

    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    stream.start_stream()

    try:
        while True:
            if listen_for_keyword(stream, rec):
                end_of_conversation = False
                while not end_of_conversation:
                    record_audio_to_file(output_filename, stream, rec)
                    end_of_conversation = chat()
                
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()    


def chat():
    end_of_conversation = False
    audio_file = open("output.wav", "rb")
    transcript = audio_to_text(audio_file)
    MESSAGES.append({"role": "user", "content": transcript})
    assistant_message = generate_function_response(MESSAGES)
    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
        for call in assistant_message.tool_calls:
            results = execute_function_call(call)
            if "conversation ended" in str(results).lower():
                end_of_conversation = True 
            MESSAGES.append({"role": "function", "tool_call_id": call.id, "name": call.function.name, "content": str(results)})
        reply = generate_chat_response(MESSAGES)
        MESSAGES.append({"role": "assistant", "content": reply})
        print(reply)
        text_to_audio(str(reply))
    else:
        assistant_message = generate_chat_response(MESSAGES)
        MESSAGES.append({"role": "assistant", "content": assistant_message})
        print(assistant_message)
        text_to_audio(str(assistant_message))
    playsound("speech.mp3")
    return end_of_conversation 

############################################
# MAIN CONVERSATION FUNCTION               #
############################################








##########################################

def main():

    parser = argparse.ArgumentParser(description='Medications Client')
    subparsers = parser.add_subparsers(dest='command')

    # get outlook events
    subparsers.add_parser('calendar', help='Fetch all calendar events')

    # keyword activation
    subparsers.add_parser('keyword', help='keyword activation')

    # send a message to the chatbot
    subparsers.add_parser('chat', help='Send a message to the chatbot')

    # record user audio 
    subparsers.add_parser('record', help='Record audio')

    # add calendar event command
    subparsers.add_parser('add_event', help='add calendar event')

    #get calendar events
    subparsers.add_parser('get_events', help='Fetch all calendar events')

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

    # elif args.command == 'record':
    #     record_audio()

    elif args.command == 'chat':
        chat()
    elif args.command == 'keyword':
        tester_main()

    elif args.command == 'generate':
        generate()
    
    elif args.command == "get_events":
        events = get_calendar_events()
        print(events)

    elif args.command == 'add_event':
        subject = input("Enter event subject: ")
        start = input("Enter start time: ")
        end = input("Enter end time: ")
        location = input("Enter location: ")
        description = input("Enter description: ")
        if location == "":
            location = None
        if description == "":
            description = None
        add_calendar_event(subject, start, end, location, description)  

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




