#===============================================================================
# The running script for the project of MedMirror
#===============================================================================
import asyncio
import configparser
# from msgraph.generated.models.o_data_errors.o_data_error import ODataError
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

MESSAGES = [
    {"role": "system", "content": "You are a friendly assistant here to help the user with their health and wellness needs.\
      Respond in English and do not switch languages. You can answer questions about their medications, \
     schedule, and general health questions. You can also add new medications to their list or delete existing ones.\
     Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous, \
     make sure the user is specifc about what they want. You must decide when to perfrom multiple functions in a single response,\
     and when to ask the user for more information. You can also end the conversation if the user says goodbye \
     or if there is silence for a long time"},
]

TOOLS = [
    # get calendar events
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
    # add calendar event
    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": "add a new event to the user's calendar, e.g. an appointment, meeting, etc. Each required parameter must be specified explicitly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "ID of the calendar",
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject of the event",
                    },
                    "start_year": {
                        "type": "integer",
                        "description": "The year of the start date, e.g. 2024",
                    },
                    "start_month": {
                        "type": "integer",
                        "description": "The month of the start date, e.g. 1 for January, 2 for February, etc.",
                    },
                    "start_day": {
                        "type": "integer",
                        "description": "The day of the start date, e.g. 1 for the first day of the month, 2 for the second day, etc.",
                    },
                    "start_hour": {
                        "type": "integer",
                        "description": "The hour of the start date, e.g. 0 for midnight, 1 for 1am, etc.",
                    },
                    "start_minute": {
                        "type": "integer",
                        "description": "The minute of the start date, e.g. 0 for the start of the hour, 30 for half past, etc.",
                    },

                    "end_year": {
                        "type": "integer",
                        "description": "The year of the end date, e.g. 2024",
                    },
                    "end_month": {
                        "type": "integer",
                        "description": "The month of the end date, e.g. 1 for January, 2 for February, etc.",
                    },
                    "end_day": {
                        "type": "integer",
                        "description": "The day of the end date, e.g. 1 for the first day of the month, 2 for the second day, etc.",
                    },
                    "end_hour": {
                        "type": "integer",
                        "description": "The hour of the end date, e.g. 0 for midnight, 1 for 1am, etc.",
                    },
                    "end_minute": {
                        "type": "integer",
                        "description": "The minute of the end date, e.g. 0 for the start of the hour, 30 for half past, etc.",
                    },
                    "location": {
                        "type": "string",
                        "description": "The location of the event, e.g. '123 Main St, New York, NY'",
                    },
                    "body": {
                        "type": "string",
                        "description": "The body of the event, e.g. 'This is a reminder to take your medication'",
                    },
                    "isOnline": {
                        "type": "boolean",
                        "description": "Whether the event is online or not",
                    }
                },
                "required": ["calendar_id", "subject", "start_year","start_month", "start_day", "start_hour", "start_minute", "end_year","end_month", "end_day", "end_hour", "end_minute","location", "body", "isOnline"]
            }
        }
    },
    # display view
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
    # get to-do lists
    {
        "type": "function",
        "function": {
            "name": "get_todo_lists",
            "description": "get list of all todo lists and their IDs",
        }
    },
    # get to-do tasks
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
    # end_conversation
    {
        "type": "function",
        "function": {
            "name": "end_conversation",
            "description": "Ends the current conversation with the user, can be inferred from users input or silence, e.g. 'goodbye', 'bye', 'stop', 'end conversation', 'that's all thank you' etc.",
        }
    },
    # add one time reminder
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
    # get reminders
    {
        "type": "function",
        "function": {
            "name": "get_reminders",
            "description": "get list of all scheduled reminders",
        }
    },
    #  get medicaitons
    {
        "type": "function",
        "function": {
            "name": "get_medications",
            "description": "get user's current prescribed medications in the format 'medication_id: medication name - dosage - time'",
        }
    },
    # add medication
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
    # delete medication
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
    # delete calendar event
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": "delete/remove an event from the user's calendar by its event_id",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the event",
                    },
                },
                "required": ["event_id"]
            },
        }
    },
    #  edit calendar event
    {
        "type": "function",
        "function": {
            "name": "edit_calendar_event",
            "description": "edit an existing event in the user's calendar by its event_id",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the event",
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject of the event",
                    },
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
                    },
                    "location": {
                        "type": "string",
                        "description": "The location of the event",
                    },
                    "body": {
                        "type": "string",
                        "description": "The body of the event",
                    },
                    "isOnline": {
                        "type": "boolean",
                        "description": "Whether the event is online or not",
                    }
                },
                "required": ["event_id"]
            }
        }
    },


    # read emails 
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": "read the content of an email by its email_id",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "ID of the email",
                    },
                },
                "required": ["email_id"]
            }
        }
    },
    # get emails
    {
        "type": "function",
        "function": {
            "name": "get_emails",
            "description": "get list of emails from the user's inbox and their email ID, can be filtered by unread, sender, subject, received date, received time, and number of emails to return",
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
    # send email
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "send an email to a recipient",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "The recipient's email address",
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject of the email",
                    },
                    "body": {
                        "type": "string",
                        "description": "The body of the email",
                    }
                },
                "required": ["recipient", "subject", "body"]
            }
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
         
    def add_reminder(self, seconds, reminder_message='Time to take a break!'):
        self.scheduler.add_job(self._play_sound, 'interval', seconds=seconds, args=[reminder_message])
    
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
    result = await graph.send_mail(subject=subject, body=body, recipient=recipient)
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

async def get_calendar_events(graph: Graph, top: int, start_date: datetime, end_date: datetime):
    result = await graph.get_calendar_events(top=top, start_date=start_date, end_date=end_date)
    return result
async def add_calendar_event(graph: Graph, calendar_id: str, subject: str, start: datetime, end: datetime, location: str, body: str, isOnline: bool):
    result = await graph.create_event(calendar_id, subject, start, end, location, body, is_online=isOnline)
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
        top = None
        start_date = datetime(start_year, start_month, start_day)
        end_date = datetime(end_year, end_month, end_day)
        results = await get_calendar_events(graph, top, start_date, end_date)
    elif func_name == "add_calendar_event":
        calendar_id = args.get("calendar_id")
        subject = args.get("subject")
        start_year = args.get("start_year")
        start_month = args.get("start_month")
        start_day = args.get("start_day")
        start_hour = args.get("start_hour")
        start_minute = args.get("start_minute")
        end_year = args.get("end_year")
        end_month = args.get("end_month")
        end_day = args.get("end_day")
        end_hour = args.get("end_hour")
        end_minute = args.get("end_minute")
        location = args.get("location")
        body = args.get("body")
        isOnline = args.get("isOnline")
        start_date = datetime(start_year, start_month, start_day, start_hour, start_minute)
        end_date = datetime(end_year, end_month, end_day, end_hour, end_minute)
        results = await add_calendar_event(graph, calendar_id, subject, start_date, end_date, location, body, isOnline)
    elif func_name == "edit_calendar_event":
        event_id = args.get("event_id")
        subject = args.get("subject")
        start_year = args.get("start_year")
        start_month = args.get("start_month")
        start_day = args.get("start_day")
        end_year = args.get("end_year")
        end_month = args.get("end_month")
        end_day = args.get("end_day")
        location = args.get("location")
        body = args.get("body")
        isOnline = args.get("isOnline")
        start_date = datetime(start_year, start_month, start_day)
        end_date = datetime(end_year, end_month, end_day)
        results = await edit_calendar_event(graph, event_id, subject, start_date, end_date, location, body, isOnline)
    elif func_name == "delete_calendar_event":
        event_id = args.get("event_id")
        results = await delete_calendar_event(graph, event_id)
    
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
    elif func_name == "read_email":
        email_id = args.get("email_id")
        results = await read_email(graph, email_id)
    elif func_name == "send_email":
        recipient = args.get("recipient")
        subject = args.get("subject")
        body = args.get("body")
        results = await send_email(graph, recipient=recipient, subject=subject, body=body)
    
    
    elif func_name == "get_todo_lists":
        results = await get_ToDo_lists(graph)
    elif func_name == "get_todo_tasks":
        list_id = args.get("list_id")
        results = await get_ToDo_tasks(graph ,list_id)
    elif func_name == "add_todo_task":
        list_id = args.get("list_id")
        title = args.get("title")
        due_year = args.get("due_year")
        due_month = args.get("due_month")
        due_day = args.get("due_day")
        due_date = datetime(due_year, due_month, due_day)
        body = args.get("body")
        reminder_year = args.get("reminder_year")
        reminder_month = args.get("reminder_month")
        reminder_day = args.get("reminder_day")
        reminder_date = datetime(reminder_year, reminder_month, reminder_day)
        results = await add_ToDo_task(graph, list_id, title, due_date, body, reminder_date)
    elif func_name == "edit_todo_task":
        task_id = args.get("task_id")
        title = args.get("title")
        due_year = args.get("due_year")
        due_month = args.get("due_month")
        due_day = args.get("due_day")
        due_date = datetime(due_year, due_month, due_day)
        reminder_year = args.get("reminder_year")
        reminder_month = args.get("reminder_month")
        reminder_day = args.get("reminder_day")
        reminder_date = datetime(reminder_year, reminder_month, reminder_day)
        results = await edit_ToDo_task(graph, task_id, title, due_date, reminder_date)
    elif func_name == "delete_todo_task":
        task_id = args.get("task_id")
        results = await delete_ToDo_task(graph, task_id)



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


    # 3.) Configure the Vosk settings

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
    
       
    User_Requests = [
        # {"role": "user", "content": "Can you please get my last unread emails?"},
        # {"role": "user", "content": "Can you please send an email to 'tburtgray@gmail.com' saying hey there tom this works, with subject test?"},
        # {"role": "user", "content": "Can you please read my most recent email"},

        {"role": "user", "content": "Can you please get my calendar events for today?"},
        {"role": "user", "content": "can you please create a new event in my calendar for tomorrow at 3pm? durarion 1 hour, subject Meeting, location MVB, body This is a test event"},
        {"role": "user", "content": "can you please edit the event with the subject Meeting to be 2 hours long?"},
        {"role": "user", "content": "can you please delete the event with the subject Meeting?"},

        {"role": "user", "content": "Can you please get my todo lists?"},
        {"role": "user", "content": "Can you please get the tasks in my todo list"},
        {"role": "user", "content": "Can you please add a new task to my todo list for tomorrow at 3pm?, title: Task, body: This is a test task"},
        {"role": "user", "content": "Can you please edit the task with the title Task to be due in 2 days?"},
        {"role": "user", "content": "Can you please delete the task with the title Task?"},

        {"role": "user", "content": "Can you please get my medications?"},
        {"role": "user", "content": "Can you please add a new medication to my list?"},
    ]
    for i, message in enumerate(User_Requests):
        myAI.add_message(message["role"], message["content"])
        response = await myAI.generate_function_response()
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for call in response.tool_calls:
                        
                results = await execute_function_call(graph, scheduler, call) 
                           

                myAI.add_func_message("function", call.id, call.function.name, str(results))
        print("completed request:", i)             
        reply = await myAI.generate_chat_response()
        myAI.add_message("assistant", reply)
    myAI.display_messages()


# ============================================================================= #
#                           Run the main function                               #
# ============================================================================= #

asyncio.run(main())