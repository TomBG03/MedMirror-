#===============================================================================
# The running script for the project of MedMirror
#===============================================================================
import asyncio
import configparser
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph import Graph
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
from myAI import MyAI
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from threading import Thread
import time
import logging



# =============================================================================
# Global variables
# =============================================================================


system_message = """
You are a friendly assistant here to help the user with their health and wellness needs.
Respond in English and do not switch languages. You can answer questions about their medications,
schedule, and general health questions. You can also add new medications to their list or delete existing ones.
Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous,
make sure the user is specifc about what they want. You must decide when to perfrom multiple functions in a single response,
and when to ask the user for more information. You can also end the conversation if the user says goodbye, or if there is silence, you must 
infer the end of the conversation. You can also display views to the user, such as the medication view, calendar view, or todo view.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "get list of calendar events for the user, can be filtered by start date and end date",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_year": {
                        "type": "integer",
                        "description": "The year of the start date",
                    },
                    "start_month": {
                        "type": "integer",
                        "description": "The month of the start date",
                    },
                    "start_day": {
                        "type": "integer",
                        "description": "The day of the start date",
                    },
                    "end_year": {
                        "type": "integer",
                        "description": "The year of the end date",
                    },
                    "end_month": {
                        "type": "integer",
                        "description": "The month of the end date",
                    },
                    "end_day": {
                        "type": "integer",
                        "description": "The day of the end date",
                    }
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_emails",
            "description": "get list of emails from the user's inbox, can be filtered by unread, sender, subject, received date, received time, and number of emails to return",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_by_unread": {
                        "type": "boolean",
                        "description": "Filter by unread emails",
                    },
                    "filter_by_sender": {
                        "type": "string",
                        "description": "Filter by sender's email address",
                    },
                    "filter_by_subject": {
                        "type": "string",
                        "description": "Filter by email subject",
                    },
                    "top": {
                        "type": "integer",
                        "description": "Number of emails to return",
                    },
                    "year": {
                        "type": "integer",
                        "description": "The year of the email, if the user wants to filter by received date",
                    },
                    "month": {
                        "type": "integer",
                        "description": "The month of the email, if the user wants to filter by received date",
                    },
                    "day": {
                        "type": "integer",
                        "description": "The day of the email, if the user wants to filter by received date",
                    },
                    "hour": {
                        "type": "integer",
                        "description": "The hour of the email, if the user wants to filter by received time",
                    },
                    "minute": {
                        "type": "integer",
                        "description": "The minute of the email, if the user wants to filter by received time",
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "display_view",
            "description": "display/ show information to the user, shows them medicaiton view, calendar view, or todo view.",
            "parameters": {
                "type": "object",
                "properties": {
                    "view": {
                        "type": "string",
                        "description": "The view to display to the user, caqn be one of the following: medications-view, calendar-view, todos-view",
                    },
                },
                "required": ["view"]
            }
        }

    },
    {
        "type": "function",
        "function": {
            "name": "get_todo_lists",
            "description": "get list of all todo lists and their IDs",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_todo_tasks",
            "description": "get list of all tasks in a todo list",
            "parameters": {
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "ID of the todo list",
                    },
                },
                "required": ["list_id"]
            }
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
            "name": "add_one_time_reminder",
            "description": "Adds a single reminder at a specific time and date",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_name":{
                        "type": "string",
                        "description": "A single word to describe the reminder can be inferred from user, e.g. 'medication', 'appointment1', 'appointment2', etc.",
                    },
                    "reminder_message": {
                        "type": "string",
                        "description": "The message to remind the user about",
                    },
                    "Year": {
                        "type": "integer",
                        "description": "The year the reminder should occur, e.g. 2024",
                    },
                    "Month": {
                        "type": "integer",
                        "description": "The month the reminder should occur, e.g. 1 for January, 2 for February, etc.",
                    },
                    "Day": {
                        "type": "integer",
                        "description": "The day the reminder should occur, e.g. 1 for the first day of the month, 2 for the second day, etc.",
                    },
                    "Hour": {
                        "type": "integer",
                        "description": "The hour the reminder should occur, e.g. 0 for midnight, 1 for 1am, etc.",
                    },
                    "Minute": {
                        "type": "integer",
                        "description": "The minute the reminder should occur, e.g. 0 for the start of the hour, 30 for half past, etc.",
                    },
                    "Second": {
                        "type": "integer",
                        "description": "The second the reminder should occur, e.g. 0 for the start of the minute, 30 for half past, etc.",
                    }
                },
                "required": ["reminder_name","reminder_message", "year", "month", "day", "hour", "minute", "second"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_reminders",
            "description": "get list of all scheduled reminders",
        }
    },
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
                        "description": "The dosage of the medication e.g. mg/g/ml, must be said explicitly.",
                    },
                    "time": {
                        "type": "string",
                        "description": "Time of day to take the medication, e.g. 8am or 8pm",
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
]

# =============================================================================
# Reminder functions
# =============================================================================

class myScheduler:
    def __init__(self, ai):
        self.scheduler = AsyncIOScheduler(job_defaults={"coalesce": True, "max_instances": 2, "misfire_grace_time": 60*60})
        self.scheduler.start()
        self.ai = ai

        self.have_jobs_to_execute = False
        self.jobs_to_execute = []
         
    def add_reminder(self, seconds, path_to_mp3, reminder_message='Time to take a break!'):
        self.scheduler.add_job(self._play_sound, 'interval', seconds=seconds, args=[reminder_message, path_to_mp3])
    
    def add_single_reminder(self, date, path_to_mp3, reminder_message='Time to take a break!'):
        try:
            self.scheduler.add_job(self._play_sound, 'date', run_date=date, args=[reminder_message, path_to_mp3])
            return "Reminder added"
        except Exception as e:
            return(f"Error: {e}")

    def edit_reminder(self, job_id, seconds, reminder_message='Time to take a break!'):
        self.scheduler.reschedule_job(job_id, trigger='interval', seconds=seconds, args=[reminder_message])
    def edit_single_reminder(self, job_id, date, reminder_message='Time to take a break!'):
        self.scheduler.reschedule_job(job_id, trigger='date', run_date=date, args=[reminder_message])
    def remove_reminder(self, job_id):
        self.scheduler.remove_job(job_id)
    def clear_all_reminders(self):
        self.scheduler.remove_all_jobs()
    def stop(self):
        self.scheduler.shutdown()
    
    def remind_me(self, reminder_message, path_to_mp3):
        reminder = self.ai.create_mp3(reminder_message, path_to_mp3)
        self.have_jobs_to_execute = True
        self.jobs_to_execute.append(reminder)
    
    def execute_reminders(self):
        playsound('ding.mp3')
        for reminder in self.jobs_to_execute:
            playsound(reminder)
        self.have_jobs_to_execute = False
        self.jobs_to_execute = []

    def _play_sound(self, reminder_message, path_to_mp3):
        playsound('ding.mp3')
        reminder = self.ai.create_mp3(reminder_message, path_to_mp3)
        playsound(reminder)
    def get_reminders(self):
        return self.scheduler.get_jobs()
    def get_state(self):
        return self.scheduler.state
    
# =============================================================================
# Audio functions
# =============================================================================

async def record_audio_to_file(output_filename, stream, rec, silence_duration=2):
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    num_silent_frames = 0
    max_silent_frames = int(16000 / 4096 * silence_duration)  
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        wf.writeframes(data)  
        is_silent = audioop.rms(data, 2) < 300 
        if is_silent:
            num_silent_frames += 1
        else:
            num_silent_frames = 0
        if num_silent_frames > max_silent_frames:
            print("Silence detected, stopping recording")
            break
    wf.close()

def listen_for_keyword(stream, rec, keyword="activate"):
    # print("Listening for activation keyword...")
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if keyword.lower() in [word['word'].lower() for word in result.get('result', [])]:
                print(f"Activation keyword '{keyword}' detected.")
                return True

# =============================================================================
# Calls to BACKEND API
# =============================================================================
BASE_URL = 'http://localhost:3001/api'
async def get_medications():
    meds = []
    response = requests.get(f'{BASE_URL}/medications')
    if response.status_code == 200:
        medications = response.json()
        for medication in medications:
            med_id = medication['_id']
            meds.append(f"{med_id} : {medication['name']} - {medication['dosage']} - {medication['time']}")
    return meds
    
async def add_medication(name, dosage, time):
    medication = {'name': name, 'dosage': dosage, 'time': time}
    response = requests.post(f'{BASE_URL}/medications', json=medication)
    if response.status_code == 201:
        return("Medication added:", response.json())
    else:
        return("Failed to add medication")

async def delete_medication(medication_id):
    response = requests.delete(f'{BASE_URL}/medications/{medication_id}')
    if response.status_code == 200:
        return("Medication deleted")
    else:
        return("Failed to delete medication, would you like me to try again?")

async def display_view(view):
    data = {'viewName': view}
    try:
        response = requests.post(f'{BASE_URL}/view', json=data)
        if response.status_code == 200:
            return "View displayed"
        else:
            return f"Failed to display view, status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

# =============================================================================
# Calls to OUTLOOK API
# =============================================================================

async def get_user(graph: Graph):
    user = await graph.get_user()
    if user:
        return user
    else:
        return "Unable to get user info"



async def get_emails(graph: Graph, filter_by_unread: bool = False, filter_by_sender: str = None, filter_by_subject: str = None, filter_by_received_date: str = None, filter_by_received_time: str = None, top: int = 3):
    result = await graph.get_inbox(filter_by_unread, filter_by_sender, filter_by_subject, filter_by_received_date, filter_by_received_time, top)
    return result
async def read_email(graph: Graph, email_id: str):
    result = await graph.read_email(email_id)
    return result
async def send_email(graph: Graph, recipient: str, subject: str, body: str):
    result = await graph.send_email(recipient, subject, body)
    return result


async def get_ToDo_lists(graph: Graph):
    result = await graph.get_ToDo_lists()
    return result
async def get_ToDo_tasks(graph: Graph, list_id: str):
    result = await graph.get_ToDo_tasks(list_id)
    return result
async def add_ToDo_task(graph: Graph, list_id: str, title: str, due_date: datetime, body: str, reminder_date: datetime):
    result = await graph.create_task(list_id, title, due_date, body, reminder_date)
    return result
async def edit_ToDo_task(graph: Graph, task_id: str, title: str, due_date: datetime, reminder_date: datetime):
    result = await graph.edit_task(task_id, title, due_date, reminder_date)
    return result
async def delete_ToDo_task(graph: Graph, task_id: str):
    result = await graph.delete_task(task_id)
    return result

async def get_calendar_events(graph: Graph, start_date: datetime, end_date: datetime):
    result = await graph.get_calendar_events(start_date, end_date)
    return result
async def add_calendar_event(graph: Graph, calendar_id: str, subject: str, start_date: datetime, end_date: datetime, location: str, body: str, isOnline: bool):
    result = await graph.create_event(calendar_id, subject, start_date, end_date, location, body, is_online=isOnline)
    return result
async def edit_calendar_event(graph: Graph, event_id: str, subject: str, start_date: datetime, end_date: datetime, location: str, body: str, isOnline: bool):
    result = await graph.edit_event(event_id, subject, start_date, end_date, location, body, is_online=isOnline)
    return result
async def delete_calendar_event(graph: Graph, event_id: str):
    result = await graph.delete_event(event_id)
    return result
# ============================================================================= #
# Execution of fuction calls                                                    #           
# ============================================================================= #

        
async def execute_function_call(graph, schedular, tool_call):
    # Get the name of function to call
    func_name = tool_call.function.name 
    args = json.loads(tool_call.function.arguments)
    
    # ================================================
    # Assisting function calls
    if func_name == "end_conversation":
        results = "Conversation ended. Goodbye!"
    
    
    # ================================================
    # Outlook API calls
    elif func_name == "get_calendar_events":
        start_year = args.get("start_year")
        start_month = args.get("start_month")
        start_day = args.get("start_day")
        end_year = args.get("end_year")
        end_month = args.get("end_month")
        end_day = args.get("end_day")
        start_date = datetime(start_year, start_month, start_day)
        end_date = datetime(end_year, end_month, end_day)
        results = await get_calendar_events(graph, start_date, end_date)
    elif func_name == "get_emails":
        filter_by_unread = args.get("filter_by_unread", False)
        filter_by_sender = args.get("filter_by_sender", None)
        filter_by_subject = args.get("filter_by_subject", None)
        filter_by_received_date = args.get("filter_by_received_date", None)
        filter_by_received_time = args.get("filter_by_received_time", None)
        year = args.get("year", None)
        month = args.get("month", None)
        day = args.get("day", None)
        hour = args.get("hour", None)
        minute = args.get("minute", None)
        top = args.get("top", 3)
        if year and month and day:
            filter_by_received_date = datetime(year, month, day)
        if hour and minute:
            filter_by_received_time = datetime(year, month, day, hour, minute)
        results = await get_emails(graph, filter_by_unread, filter_by_sender, filter_by_subject, filter_by_received_date, filter_by_received_time, top)
    
    
    
    elif func_name == "get_todo_lists":
        results = await get_ToDo_lists(graph)
    elif func_name == "get_todo_tasks":
        list_id = args.get("list_id")
        results = await get_ToDo_tasks(graph ,list_id)



    # ================================================
    # Backend API calls
        
    elif func_name == "get_medications":
        results = await get_medications()
    elif func_name == "add_medication":
        name = args.get("name")
        dosage = args.get("dosage")
        time = args.get("time")
        results = await add_medication(name, dosage, time)

    elif func_name == "delete_medication":
        medication_id = args.get("medication_id")
        results = await delete_medication(medication_id)

    elif func_name == "display_view":
        view = args.get("view")
        results = await display_view(view)
        
    # ================================================
    # Reminder function calls
        
    elif func_name == "get_reminders":
        results = schedular.get_reminders()
        

    elif func_name == "add_one_time_reminder":
        reminder_message = args.get("reminder_message", "No message")
        name = args.get("reminder_name")
        year = args.get("Year")
        month = args.get("Month")
        day = args.get("Day")
        hour = args.get("Hour")
        minute = args.get("Minute")
        second = args.get("Second")
        date = datetime(year, month, day, hour, minute, second)
        path_to_mp3 = f"{name}.mp3"        
        results = schedular.add_single_reminder(date, path_to_mp3, reminder_message)
    
    # ================================================
    else:
        results = f"Error: function {func_name} does not exist"
    
    return results


# ============================================================================= #
# Main function                                                                 #
# ============================================================================= #
  # Initialize the Mirror Settings by:
    # 1.)  Configure the outlook settings
    # 2.)  Initialise openAI chatbot
    # 3.)  Configure the Vosk settings
    # 4.)  Get user info and greet the user
    ## INITIALISE THE SCHEDULER
    #  THEN 
    # 5.)  Start listening for the activation keyword
    # 6.)  Start the conversation with the user
        # 6.1)  Get the user's input
        # 6.2)  Transcribe input and generate a response
        # 6.3)  Execute the function calls
        # 6.4)  Generate a response
        # 6.5)  Do appropriate actions
        # 6.6)  Convert the response to speech
        # 6.7)  Play the speech
    # 7.)  Wait for conversaiton to end
# =============================================================================
MESSAGES = [
    {"role": "system", "content": system_message},
]

async def main():
    logging.basicConfig()
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    # 1.)  Configure the outlook settings
    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']
    graph: Graph = Graph(azure_settings)


    # 2.) Initialise openAI chatbot
    myAI = MyAI(TOOLS, MESSAGES)

    await display_view('welcome-view')
    

    # 3.) Configure the Vosk settings
    model_path = "/Users/annushka/Documents/GitHub/MedMirror-/vosk-model-en-us-0.22"
    output_filename = "output.wav"
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    stream.start_stream()
    display_view('welcome-view')

    # 4.) Get user info and greet the user
    user = await get_user(graph)
    greeting = "Hello " + (user.display_name).split(" ")[0] + ", I will be the voice behind the mirror,\
                 If you need any help just say the keyword 'activate' and I will be here to help you."
    
    myAI.add_message("assistant", greeting)
    path_to_greeting = await myAI.text_to_speech(greeting)
    if path_to_greeting is not None:
        playsound(path_to_greeting)
    
    # INITIALISE THE SCHEDULER
    scheduler = myScheduler(myAI)
    print(scheduler.get_state())
    # 5.) Start listening for the activation keyword
    
    try:
        while True:
            loop = asyncio.get_running_loop()
            keyword_listener = loop.run_in_executor(None, listen_for_keyword, stream, rec, "activate")
            print("Listening for activation keyword...")
            if await keyword_listener:


                # 6.) Start the conversation with the user
                end_of_conversation = False
                while not end_of_conversation:
                    print("Listening for user input...")
                    await record_audio_to_file(output_filename, stream, rec)
                    audio_file = open(output_filename, "rb")
                    user_prompt = await myAI.speech_to_text(audio_file)
                    if "end conversation" in user_prompt.lower():
                        end_of_conversation = True
                        myAI.reset_messages()
                        continue
                    day_of_week = datetime.now().strftime("%c")
                    myAI.add_message("user", user_prompt + " {Message Locale's Date and Timestamp: " + day_of_week + "}")
                    print("added user request")
                    assistant_message = await myAI.generate_function_response()
                    print("generated response")
                    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                        print("Tool calls detected. Executing...")
                        for call in assistant_message.tool_calls:
                            print(f"Function call: {call.function.name}")
                            results = await execute_function_call(graph, scheduler, call) 
                            print(f"Funciton executed, {results}")

                            myAI.add_func_message("function", call.id, call.function.name, str(results))
                            if "conversation ended" in str(results).lower():
                                end_of_conversation = True
                    if not end_of_conversation:
                        print("Creating message for user after function calls") 
                        reply = await myAI.generate_chat_response()
                        myAI.add_message("assistant", reply)
                        path = await myAI.text_to_speech(str(reply))
                        if path is not None:
                            playsound(path)
                    myAI.display_messages()
                    time.sleep(1)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()    


# ============================================================================= #
#                           Run the main function                               #
# ============================================================================= #

asyncio.run(main())