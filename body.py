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
            "description": "returns a list of user's current prescribed medication in format 'medication_id: medication name - dosage - time'",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_medication",
            "description": "add a new prescribed medication to the user's list of medications",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "name of the medication",
                    },
                    "dosage": {
                        "type": "string",
                        "description": "The dosage of the medication in mg/g/ml",
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
            "description": "delete a medication from the user's list of medications by its ID",
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
    }
]

##########################################

##########################################
# EXECUTING FUNCTIONS FOR CHATBOT API    #
##########################################
def execute_function_call(tool_call):
    # Assume tool_call is a single ChatCompletionMessageToolCall object
    func_name = tool_call.function.name  # Directly access the function name

    # Process the function call based on its name
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
    else:
        results = f"Error: function {func_name} does not exist"

    return results
 

##########################################

##########################################
# HARDWARE INTERACTION FUNCTIONS        #
##########################################
def record_audio(duration=5, fs=44100, filename='output.wav'):
    print("Recording...")
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait() 
    print("Finished recording. Saving file...")
    write(filename, fs, np.int16(myrecording * 32767))
    print(f"File saved as {filename}")
##########################################




##########################################
# OUTLOOKK AI API                        #
##########################################

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
        return("Failed to delete medication")

##########################################



##########################################
# MAIN FUNCTIONS                         #
##########################################
MESSAGES = [
    {"role": "system", "content": "You are a friendly assistant here to help you with your health and wellness needs."},
    {"role": "system", "content": "You can ask me about your medications, schedule, and general health questions."},
    {"role": "system", "content": "You can also add new medications to your list or delete existing ones."},
    {"role": "system", "content": "You can also ask me to schedule appointments for you."},
    {"role": "system", "content": "If you need to exit, just say 'exit'"},
    {"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous, do not make a funciton call if the user does not provide required informaiton to do so"},
]


KEEP_CHATTING = True

def generate():
    while True:
        global MESSAGES
        prompt = input("Enter a prompt: ")
        if prompt.lower() == "exit":
            break
        
        MESSAGES.append({"role": "user", "content": prompt})
        assistant_message = generate_function_response(MESSAGES)
        
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for call in assistant_message.tool_calls:
                results = execute_function_call(call)  # Adjust this function to accept an individual tool call
                # Here, ensure you're appending results correctly to MESSAGES
                MESSAGES.append({"role": "function", "tool_call_id": call.id, "name": call.function.name, "content": str(results)})
            
            # Generate and append the assistant's reply after processing all tool calls
            reply = generate_chat_response(MESSAGES)
            MESSAGES.append({"role": "assistant", "content": reply})
        else:
            # Directly generate a chat response for prompts that don't result in tool calls
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
    
##########################################


def chat():
    while True:
        record_audio()
        audio_file = open("output.wav", "rb")
        transcript = audio_to_text(audio_file)
        MESSAGES.append({"role": "user", "content": transcript})
        assistant_message = generate_function_response(MESSAGES)
        if assistant_message.tool_calls:
            for call in assistant_message.tool_calls:
                print(call)
                print(assistant_message.tool_calls[0].function)
                assistant_message.content = str(assistant_message.tool_calls[0].function)
                MESSAGES.append({"role": assistant_message.role, "content": assistant_message.content})
                results = execute_function_call(assistant_message)
                MESSAGES.append({"role": "function", "tool_call_id": assistant_message.tool_calls[0].id, "name": assistant_message.tool_calls[0].function.name, "content": str(results)})
            reply = generate_chat_response(MESSAGES)
            MESSAGES.append({"role": "assistant", "content": reply})
            print(reply)
            text_to_audio(str(reply))
        else:
            assistant_message = generate_chat_response(MESSAGES)
            MESSAGES.append({"role": "assistant", "content": assistant_message})
            print(assistant_message)
            text_to_audio(str(assistant_message))
        #pretty_print_conversation(MESSAGES)
        playsound("speech.mp3")
        if KEEP_CHATTING == False:
            break

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




