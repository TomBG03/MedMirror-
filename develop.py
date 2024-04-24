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
from datetime import datetime, timedelta
from myAI import MyAI
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from threading import Thread
import time
import logging
from pyAudioAnalysis.pyAudioAnalysis import audioTrainTest as aT
import pytz
import re



# =============================================================================
# Global variables
# =============================================================================

system_message = """
    You are a dedicated assistant designed to help users manage their health and wellness routines effectively.
    Speak clearly in English, and focus on being as specific as possible with your requests. For any function calls, ensure all necessary details are provided.
    If unsure about what information is needed, please ask for clarity. You can manage calendar events, medications, and to-do lists, 
    tailoring responses to the user's needs. Remember, specificity is key to successful assistance. You must infer from the user whether to end the conversation or not. 
     NEVER tell the user the id of taks, events, calendars, lists. If the user implies they no longer need any more assistance then end conversaiton example of when to end conversation is when 
     the user says: 'Thats all thank you' or 'Bye', 'No'. 
    Ask the user if there is anything else they would like to do after each task is completed, if they do not start with 'yes' or 'no' ask them to do so. If they start with 'no'
    then end conversaiton.
    You have the ability 
    to do the following: 1) switch views on the user interface to display relevant informaiton 2)add, delete and edit informaiton in the user's medicaiton database 3) 
    retrieve, read and send emails for the user 4) add, delete and edit events in the user's calendar 5) view tasks in the user's to-do list 6) set reminders for 
    the user 7) end the conversation with the user, if the user implies they no longer need any more assistance end conversaiton e.g. user says: Thats all thank you. 
    Ask the user if there is anything else they would like to do after each task is completed, if they do not start with 'yes' or 'no' ask them to do so. If they start with 'no'
    end conversaiton.
    Be concise and clear in your responses, and always confirm the user's request if they ask to delete an event or update their medication list before executing it.",
"""

system_message_2 = """
Hello! As your dedicated Health and Wellness Assistant, I'm here to help you manage your calendar events, medications, to-do lists, and more.
Please communicate your needs clearly in English. If any details are missing from your request, I'll ask for clarification to ensure accuracy.

I can:

Switch views to display relevant information.
Manage your medication database—adding, deleting, and updating entries.
Handle your emails—retrieve, read, and send.
Organize your calendar—add, delete, and edit events.
Manage your to-do list and set reminders.

After completing each task, I'll check if there's anything else you need. A simple 'yes' or 'no' will guide our conversation. 
If you say 'no' or indicate you're done ('That's all, thank you', 'Bye'), I'll end our conversation. 
For any actions involving deletion or significant changes, I'll confirm with you first.

"""

MESSAGES = [
    {"role": "system", "content": system_message_2}
    ]

TOOLS = [

    # ========================================================================================================
    # CALANDER FUNCTIONS
    # ========================================================================================================

    # Get calendars
    {
        "type": "function",
        "function": {
            "name": "get_calendars",
            "description": "get list of calendars the user has, provides calendar ID and name",
        }
    },
    # get calendar events
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Obtains the event_id, title, start and end date. Can be filtered by start date and end date.",
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
                "required": ["start_year", "start_month", "start_day", "end_year", "end_month", "end_day"]
            }
        }
    },
    # add calendar event
    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": "add a new event to the user's calendar, example of request: add an hour long meeting at 2pm tomorrow to my calendar.",
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
                        "description": "The month of the start date, e.g. 01 for January, 2 for February, etc.",
                    },
                    "start_day": {
                        "type": "integer",
                        "description": "The day of the start date, e.g. 01 for the first day of the month, 2 for the second day, etc.",
                    },
                    "start_hour": {
                        "type": "integer",
                        "description": "The hour of the start date, e.g. 00 for midnight, 1 for 1am, etc.",
                    },
                    "start_minute": {
                        "type": "integer",
                        "description": "The minute of the start date, e.g. 00 for the start of the hour, 30 for half past, etc.",
                    },

                    "end_year": {
                        "type": "integer",
                        "description": "The year of the end date, e.g. 2024",
                    },
                    "end_month": {
                        "type": "integer",
                        "description": "The month of the end date, e.g. 01 for January, 2 for February, etc.",
                    },
                    "end_day": {
                        "type": "integer",
                        "description": "The day of the end date, e.g. 01 for the first day of the month, 2 for the second day, etc.",
                    },
                    "end_hour": {
                        "type": "integer",
                        "description": "The hour of the end date, e.g. 00 for midnight, 1 for 1am, etc.",
                    },
                    "end_minute": {
                        "type": "integer",
                        "description": "The minute of the end date, e.g. 00 for the start of the hour, 30 for half past, etc.",
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
                "required": ["calendar_id", "subject", "start_year","start_month", "start_day", "start_hour", "start_minute", "end_year","end_month", "end_day", "end_hour", "end_minute"]
            }
        }
    },
    #  edit calendar event
    {
        "type": "function",
        "function": {
            "name": "edit_calendar_event",
            "description": "Edits an event of the users calendar by using the event_id. If no change in values keep then use the original ones. If changing the time must specify the full start and end time. Example request, edit my meeting called Meeting with Jon tomorrow to start at 9am instead of 10am.",
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
                    "start_hour": {
                        "type": "integer",
                        "description": "The hour of the start date",
                    },
                    "start_minute": {
                        "type": "integer",
                        "description": "The minute of the start date",
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
                    "end_hour": {
                        "type": "integer",
                        "description": "The hour of the end date",
                    },
                    "end_minute": {
                        "type": "integer",
                        "description": "The minute of the end date",
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
                "required": ["event_id", "subject", "start_year", "start_month", "start_day", "start_hour", "start_minute", "end_year", "end_month", "end_day", "end_hour", "end_minute"]
            }
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
    # ========================================================================================================
    # MEDICATION FUNCTIONS
    # ========================================================================================================
    
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
    # update medication
    {
        "type": "function",
        "function": {
            "name": "update_medication",
            "description": "update an existing medication in the user's list of medications by its medication_id. Each required parameter must be specified explicitly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_id": {
                        "type": "string",
                        "description": "ID of the medication",
                    },
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
                "required": ["medication_id", "name", "dosage", "time"]
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
    # ========================================================================================================
    # REMINDER FUNCTIONS
    # ========================================================================================================
    
    # get reminders
    {
        "type": "function",
        "function": {
            "name": "get_reminders",
            "description": "get list of all scheduled reminders",
        }
    },
    # add one time reminder
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": "Adds a reminder at a specific time and date, use the message time stamp (year-month-day hour-minute-seconds) as the current time. Example request: remind me to take my medication at 2pm today (Message timestamp 2024-04-05 13:30:43.195101).",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_name": {
                        "type": "string",
                        "description": "The name of the reminder, it must be unique and can be inferred from the user's request",
                    },
                    "reminder_message": {
                        "type": "string",
                        "description": "The message to remind the user about, this can be inferred from the user's request",
                    },
                    "Year": {
                        "type": "integer",
                        "description": "The year the reminder should occur, e.g. 2024",
                    },
                    "Month": {
                        "type": "integer",
                        "description": "The month the reminder should occur, e.g. 01 for January, 2 for February, etc.",
                    },
                    "Day": {
                        "type": "integer",
                        "description": "The day the reminder should occur, e.g. 01 for the first day of the month, 2 for the second day, etc.",
                    },
                    "Hour": {
                        "type": "integer",
                        "description": "The hour the reminder should occur, e.g. 00 for midnight, 16 for 4pm, etc.",
                    },
                    "Minute": {
                        "type": "integer",
                        "description": "The minute the reminder should occur, e.g. 00 for the start of the hour, 30 for half past, etc.",
                    },
                    "Second": {
                        "type": "integer",
                        "description": "The second the reminder should occur, e.g. 00 for the start of the minute, 30 for half past, etc.",
                    }
                },
                "required": ["reminder_name","reminder_message", "year", "month", "day", "hour", "minute", "second"]
            }
        }
    },
    # add interval reminder
    {
        "type": "function",
        "function": {
            "name": "add_interval_reminder",
            "description": "Creates a reminder to repeat at a specific interval, if no end has been specified set it to be 100 years from now Example request: remind me to take my medication every morning at 8am, starting tomorrow",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_name": {
                        "type": "string",
                        "description": "The name of the reminder, it must be unique and can be inferred from the user's request",
                    },
                    "reminder_message": {
                        "type": "string",
                        "description": "The message to remind the user about, this can be inferred from the user's request",
                    },
                    "weeks": {
                        "type": "integer",
                        "description": "How many weeks between each reminder interval",
                    },
                    "days": {
                        "type": "integer",
                        "description": "How many days between each reminder interval",
                    },
                    "hours": {
                        "type": "integer",
                        "description": "How many hours between each reminder interval",
                    },
                    "minutes": {
                        "type": "integer",
                        "description": "How many minutes between each reminder interval",
                    },
                    "seconds": {
                        "type": "integer",
                        "description": "How many seconds between each reminder interval",
                    },
                    "start_year": {
                        "type": "integer",
                        "description": "The year the reminder should start, e.g. 2024",
                    },
                    "start_month": {
                        "type": "integer",
                        "description": "The month the reminder should start, e.g. 01 for January, 2 for February, etc.",
                    },
                    "start_day": {
                        "type": "integer",
                        "description": "The day the reminder should start, e.g. 01 for the first day of the month, 2 for the second day, etc.",
                    },
                    "start_hour": {
                        "type": "integer",
                        "description": "The hour the reminder should start, e.g. 00 for midnight, 16 for 4pm, etc.",
                    },
                    "start_minute": {
                        "type": "integer",
                        "description": "The minute the reminder should start, e.g. 00 for the start of the hour, 30 for half past, etc.",
                    },
                    "start_second": {
                        "type": "integer",
                        "description": "The second the reminder should start, e.g. 00 for the start of the minute, 30 for half past, etc.",
                    },
                    "end_year": {
                        "type": "integer",
                        "description": "The year the reminder should end, e.g. 2024",
                    },
                    "end_month": {
                        "type": "integer",
                        "description": "The month the reminder should end, e.g. 01 for January, 2 for February, etc.",
                    },
                    "end_day": {
                        "type": "integer",
                        "description": "The day the reminder should end, e.g. 01 for the first day of the month, 2 for the second day, etc.",
                    },
                    "end_hour": {
                        "type": "integer",
                        "description": "The hour the reminder should end, e.g. 00 for midnight, 16 for 4pm, etc.",
                    },
                    "end_minute": {
                        "type": "integer",
                        "description": "The minute the reminder should end, e.g. 00 for the start of the hour, 30 for half past, etc.",
                    },
                    "end_second": {
                        "type": "integer",
                        "description": "The second the reminder should end, e.g. 00 for the start of the minute, 30 for half past, etc.",
                    }

                },
                "required": ["reminder_name","reminder_message", "weeks", "days", "hours", "minutes", "seconds", "start_year", "start_month", "start_day", "start_hour", "start_minute", "start_second", "end_year", "end_month", "end_day", "end_hour", "end_minute", "end_second"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_all_reminders",
            "description": "deletes all reminders",
        }
    },
    
    # ========================================================================================================
    # LOCAL FUNCTIONS
    # ========================================================================================================

    # end_conversation
    {
        "type": "function",
        "function": {
            "name": "end_conversation",
            "description": "Ends the current conversation with the user, can be inferred from users input or silence, e.g. 'goodbye', 'bye', 'stop', 'end conversation', 'that's all thank you' etc.",
        }
    },
     # ========================================================================================================
     # UI functions 
    # ========================================================================================================

    # display welcome screen
    {
        "type": "function",
        "function": {
            "name": "show_welcome_screen",
            "description": "display welcome screen on user interface",
        }
    },
    # display mirror
    {
        "type": "function",
        "function": {
            "name": "show_mirror",
            "description": "display mirror on user interface",
        }
    },
    # display medications
    {
        "type": "function",
        "function": {
            "name": "show_medications",
            "description": "display medicaitons on the user interface",
        }

    },
    # # display calendar events
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "show_calendar",
    #         "description": "display calendar events on user interface",
    #     }

    # },
    # display to-do tasks
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "show_todo_tasks",
    #         "description": "display to-do tasks on user interface",
    #     }

    # },
    # Display day view
    {
        "type": "function",
        "function": {
            "name": "display_day_view",
            "description": "display users calendar events for a specific day",
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
                "required": ["start_year", "start_month", "start_day", "end_year", "end_month", "end_day"]
            }
        }
    },

]

# =============================================================================
# Reminder Class
# =============================================================================

class myScheduler:
    def __init__(self, ai):
        self.scheduler = AsyncIOScheduler(job_defaults={"coalesce": True, "max_instances": 2, "misfire_grace_time": 60*60})
        self.scheduler.start()
        self.ai = ai

        self.have_jobs_to_execute = False
        self.jobs_to_execute = []
        self.timezone = pytz.timezone('Europe/London')
   
    def create_reminder(self, date, reminder_name, reminder_message='Reminder'):
        self.scheduler.add_job(self.remind_me, 'date', run_date=date, timezone = self.timezone, args=[reminder_message], id=reminder_name)
        return "successfully created reminder"
    def create_interval_reminder(self, reminder_name, weeks, days, hours, minutes, seconds, start_date, end_date, reminder_message='Reminder'):
        self.scheduler.add_job(self.remind_me, 'interval', weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds, start_date=start_date, end_date=end_date, timezone = self.timezone, args=[reminder_message], id=reminder_name)
        return "successfully created interval reminder"
    def edit_interval_reminder(self, job_id, new_weeks, new_days,new_hours, new_minutes, new_seconds, new_start_date, new_end_date, reminder_message=None):
        self.scheduler.reschedule_job(job_id, trigger='interval', weeks=new_weeks, days=new_days, hours=new_hours, minutes=new_minutes, seconds=new_seconds, start_date=new_start_date, end_date=new_end_date, args=[reminder_message])
        return "successfully edited interval reminder"
    def edit_reminder(self, job_id, date, reminder_message=None):
        self.scheduler.reschedule_job(job_id, trigger='date', run_date=date, args=[reminder_message])
        return "successfully edited reminder"
    def remove_reminder(self, job_id):
        self.scheduler.remove_job(job_id)
    
    def clear_all_reminders(self):
        try:
            self.scheduler.remove_all_jobs()
            return "successfully cleared all reminders"
        except Exception as e:
            return "Failed to clear all reminders"
    
    def stop(self):
        self.scheduler.shutdown()
    
    def remind_me(self, reminder_message):
        # reminder = self.ai.create_mp3(reminder_message, path_to_mp3)
        self.have_jobs_to_execute = True
        self.jobs_to_execute.append(reminder_message)
    
    def execute_reminders(self):
        playsound('ding.mp3')
        amount = int(len(self.jobs_to_execute))
        if amount > 1:
            body = f" you have {amount} new reminders."
        else:
            body = "you have 1 new reminder."
        for i, reminder in enumerate(self.jobs_to_execute):
            if amount > 1:
                body += f"Reminder {i+1}: {reminder}"
            else:
                body += f"{reminder}"
        self.ai.add_message('assistant', body)
        reminder = self.ai.create_mp3(body, 'reminder.mp3')
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
# Reminder helper functions
# =============================================================================

def listen_for_reminders(scheduler):
    while True:
        if scheduler.have_jobs_to_execute:
            return True

async def check_and_execute_reminders(scheduler, conversation_state):
    while True:
        await asyncio.sleep(1) 
        if not conversation_state.in_conversation and scheduler.have_jobs_to_execute:
            scheduler.execute_reminders()
  
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
        is_silent = audioop.rms(data, 2) < 4000 
        if is_silent:
            num_silent_frames += 1
        else:
            num_silent_frames = 0
        if num_silent_frames > max_silent_frames:
            print("Silence detected, stopping recording")
            break
    wf.close()

async def listen_for_keyword(stream, rec, keyword="activate"):
    loop = asyncio.get_running_loop()
    while True:
        data = await loop.run_in_executor(None, stream.read, 4096, False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if keyword.lower() in [word['word'].lower() for word in result.get('result', [])]:
                print(f"Activation keyword '{keyword}' detected.")
                return True
        await asyncio.sleep(0.1)  # Prevent this loop from hogging the CPU


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
        return f"Current medicaitons in format medicaiton_id, name, dosage, time: {meds}"
    else:
        return "Failed to get medications"
    
async def add_medication(name, dosage, time):
    medication = {'name': name, 'dosage': dosage, 'time': time}
    response = requests.post(f'{BASE_URL}/medications', json=medication)
    if response.status_code == 201:
        return("Medication successfully added")
    else:
        return("Failed to add medication")

async def delete_medication(medication_id):
    response = requests.delete(f'{BASE_URL}/medications/{medication_id}')
    if response.status_code == 200:
        return("Medication successfully deleted")
    else:
        return("Failed to delete medication, would you like me to try again?")

async def update_medication(medication_id, name, dosage, time):
    medication = {'name': name, 'dosage': dosage, 'time': time}
    response = requests.put(f'{BASE_URL}/medications/{medication_id}', json=medication)
    if response.status_code == 200:
        return("Medication successfully updated")
    else:
        return("Failed to update medication, would you like me to try again?")

async def display_view(view):
    data = {'viewName': view}
    try:
        response = requests.post(f'{BASE_URL}/view', json=data)
        if response.status_code == 200:
            return f"successfullly displaying {view}"
        else:
            return f"Failed to display view, status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Request failed"

async def display_day_view(graph: Graph, top: int, start_date: str, end_date: str, just_events = 'yes'):
    response = requests.delete(f'{BASE_URL}/events')
    if response.status_code == 500:
        return "Failed to clear events"
        
    print(f"Get day view events: {start_date} - {end_date}")
    events = await get_calendar_events(graph, top, start_date, end_date, just_events)
    event_subjects = [str(event[0]) for event in events]
    for event in events:
        # print(f"subject: {str(event[0])} - start: {str(event[1])} - end: {str(event[2])} - location: {str(event[3])} - body: {str(event[4])}")
        event = {'subject': str(event[0]), 'start': str(event[1]), 'end': str(event[2]), 'location': str(event[3])}
        response = requests.post(f'{BASE_URL}/events', json=event)
        if response.status_code != 201:
            return "Failed to display events"
        
    
  
    results = await display_view("calendar-view")
    return f"{results} with the events: {event_subjects} " 

async def record_usage(feature):
    data = {'featureName': feature}
    response = requests.post(f'{BASE_URL}/featureUsage', json=data)
    if response.status_code == 201:
        return "Usage recorded successfully"
    else:
        return "Failed to record usage"

# =============================================================================
# Calls to OUTLOOK API
# =============================================================================

async def get_user(graph: Graph):
    user = await graph.get_user()
    if user:
        return user
    else:
        return "Unable to get user info"

# =============================================================================

async def get_emails(graph: Graph, filter_by_unread: bool = False, filter_by_sender: str = None, filter_by_subject: str = None, filter_by_received_date: str = None, filter_by_received_time: str = None, top: int = 3):
    try:
        result = await graph.get_inbox(filter_by_unread, filter_by_sender, filter_by_subject, filter_by_received_date, filter_by_received_time, top)
        return result
    except Exception as e:
        return "Failed to get emails"

async def read_email(graph: Graph, email_id: str):
    try:
        result = await graph.read_email(email_id)
        return result
    except Exception as e:
        return "Failed to read email"

async def send_email(graph: Graph, recipient: str, subject: str, body: str):
    try:    
        result = await graph.send_mail(subject=subject, body=body, recipient=recipient)
        return result
    except Exception as e:
        return "Failed to send email"

# =============================================================================
async def get_ToDo_lists(graph: Graph):
    try:
        lists = await graph.get_ToDo_lists()
        for list in lists.value:
            if list.display_name == "Tasks":
                result = f"Your to-do list is id:{list.id} - {list.display_name}"
        return result
    except Exception as e:
        return "Failed to get to-do lists"
    
async def get_ToDo_tasks(graph: Graph, list_id: str):
    try:
        result = await graph.get_ToDo_tasks(list_id)
        return result
    except Exception as e:
        return "Failed to get tasks"

async def add_ToDo_task(graph: Graph, list_id: str, title: str, due_date: str, body: str, reminder_date: str):
    # (self, list_id: str, title: str, due_date: str, body: str = None, reminder_date: datetime = None):
    try:
        result = await graph.create_task(list_id, title, due_date, body, reminder_date)
        return result
    except Exception as e:
        return "Failed to add task"
    
async def edit_ToDo_task(graph: Graph, list_id: str, task_id: str, title: str, due_date: str, body: str):
    try:
        result = await graph.edit_task(list_id, task_id, title, due_date, body)
    # edit_task(self, list_id: str, task_id: str, title: str = None, due_date: str = None, body: str = None):
        return result
    except Exception as e:
        return "Failed to edit task"
    
async def delete_ToDo_task(graph: Graph, task_id: str):
    try:
        result = await graph.delete_task(task_id)
        return result
    except Exception as e:
        return "Failed to delete task"

# =============================================================================

async def get_calendars(graph: Graph):
    try:
        calendars = await graph.get_calendars()
        for calendar in calendars.value:
                if calendar.is_default_calendar:
                    results = f"Successfully retrieved user calendar. calendar_id: {calendar.id} - calendar_name: {calendar.name}"
                    break
        return results
    except Exception as e:
        return "Failed to get calendars"
    
async def get_calendar_events(graph: Graph, top: int, start_date: str, end_date: str, just_events = 'no'):
    try:
        # result = await graph.get_calendar_events(top=top, start_date=start_date, end_date=end_date)
        response = await graph.list_calendar_view(start_date=start_date, end_date=end_date)
        
        event_data = response.json()
        events = []
        if just_events == 'yes':
            for event in event_data['value']:
                events.append([event['subject'], event['start']['dateTime'], event['end']['dateTime'], event.get('location', 'N/A'), event.get('body', {}).get('content', 'N/A')])
            return events
        else:
            for event in event_data['value']:
                events.append(f"(event_id:{event['id']}) Event: {event['subject']} - Start: {event['start']['dateTime']} - End: {event['end']['dateTime']} - Location: {event.get('location', 'N/A')} - Body: {event.get('body', {}).get('content', 'N/A')}")
            return f"Successfully retrieved calendar events: {events}"
        
        # return f"succesfully retrieved calendar events: {result}"
    except Exception as e:
        return "Failed to get calendar events"

async def add_calendar_event(graph: Graph, calendar_id: str, subject: str, start: str, end: str, location: str, body: str, isOnline: bool):
    try:
        result = await graph.create_event(calendar_id, subject, start, end, location, body, is_online=isOnline)
        return result
    except Exception as e:
        return "Failed to add event"
    
async def edit_calendar_event(graph: Graph, event_id: str, subject: str, start_date: str, end_date: str, location: str, body: str, isOnline: bool):
    try:
        result = await graph.edit_event(event_id, subject, start_date, end_date, location, body, is_online=isOnline)
        return result
    except Exception as e:
        return "Failed to edit event"

async def delete_calendar_event(graph: Graph, event_id: str):
    try:
        result = await graph.delete_event(event_id)
        return result
    except Exception as e:
        return "failed to delete event"
    

# ============================================================================= #
# Execution of fuction calls                                                    #           
# ============================================================================= #
  
async def execute_function_call(graph, schedular, tool_call):
    try:
        # See if we need to update the user's data for 
        # - Medications - Events - Reminders
        NEED_TO_UPDATE = [0,0,0]
        
        # Get the name of function to call
        
        func_name = tool_call.function.name 
        args = json.loads(tool_call.function.arguments)
        
        # ================================================
        # Assisting function calls

        if func_name == "end_conversation":
            results = "End Conversation"
        
        # ================================================
        # Outlook API calls
        # ================================================
        # # calendar functions
        
        elif func_name == "get_calendars":
            results = await get_calendars(graph)

        elif func_name == "get_calendar_events":
            start_year = args.get("start_year")
            start_month = args.get("start_month")
            start_day = args.get("start_day")
            end_year = args.get("end_year")
            end_month = args.get("end_month")
            end_day = args.get("end_day")
            top = None
            start_date = f"{start_year}-{start_month}-{start_day}T00:00:00"
            end_date = f"{end_year}-{end_month}-{end_day}T23:59:59"
            print(f"GET: start_date: {start_date}, end_date: {end_date}")
            results = await get_calendar_events(graph, top, start_date, end_date)
            await record_usage("calendar")
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
            isOnline = args.get("isOnline", False)
            # start_date = datetime(start_year, start_month, start_day, start_hour, start_minute)
            # end_date = datetime(end_year, end_month, end_day, end_hour, end_minute)
            start_date = (f"{start_year}-{start_month}-{start_day} {start_hour}:{start_minute}:00")
            end_date = (f"{end_year}-{end_month}-{end_day} {end_hour}:{end_minute}:00")
            print(f"ADD: start_date: {start_date}, end_date: {end_date}")
            results = await add_calendar_event(graph, calendar_id, subject, start_date, end_date, location, body, isOnline)
            NEED_TO_UPDATE[1] = 1
            await record_usage("calendar")
        elif func_name == "edit_calendar_event":
            event_id = args.get("event_id")
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
            start_date = (f"{start_year}-{start_month}-{start_day} {start_hour}:{start_minute}:00")
            end_date = (f"{end_year}-{end_month}-{end_day} {end_hour}:{end_minute}:00")
            print(f"EDIT: start_date: {start_date}, end_date: {end_date}")
            results = await edit_calendar_event(graph, event_id, subject, start_date, end_date, location, body, isOnline)
            NEED_TO_UPDATE[1] = 1
            await record_usage("calendar")
        elif func_name == "delete_calendar_event":
            event_id = args.get("event_id")
            results = await delete_calendar_event(graph, event_id)
            NEED_TO_UPDATE[1] = 1
            await record_usage("calendar")
        # # email functions
            
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
        
        # # to-do functions
            
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
            # due_date = datetime(due_year, due_month, due_day)
            due_date = f"{due_year}-{due_month}-{due_day} 00:00:00"
            body = args.get("body")
            reminder_year = args.get("reminder_year")
            reminder_month = args.get("reminder_month")
            reminder_day = args.get("reminder_day")
            reminder_hour = args.get("reminder_hour")
            reminder_minute = args.get("reminder_minute")
            #  NEED TO ADD MINUTES FOR REMINDER
            if reminder_year is not None and reminder_month is not None and reminder_day is not None:
                reminder_date = f"{reminder_year}-{reminder_month}-{reminder_day} {reminder_hour}:{reminder_minute}:00"
                # reminder_date = datetime(reminder_year, reminder_month, reminder_day)
                print(reminder_date)
            print(f"add task: {title} due: {due_date}")
            results = await add_ToDo_task(graph, list_id, title, due_date, body, reminder_date)
        elif func_name == "edit_todo_task":
            list_id = args.get("list_id")
            task_id = args.get("task_id")
            title = args.get("title")
            due_year = args.get("due_year")
            due_month = args.get("due_month")
            due_day = args.get("due_day")
            # due_date = datetime(due_year, due_month, due_day)
            due_date = f"{due_year}-{due_month}-{due_day} 00:00:00"
            body = args.get("body")
            results = await edit_ToDo_task(graph, list_id, task_id, title, due_date, body)
        elif func_name == "delete_todo_task":
            task_id = args.get("task_id")
            results = await delete_ToDo_task(graph, task_id)

        # ================================================
        # Backend API calls
        # ================================================
        # # medication functions
        
        elif func_name == "get_medications":
            results = await get_medications()
            await record_usage("medication")
        elif func_name == "add_medication":
            name = args.get("name")
            dosage = args.get("dosage")
            time = args.get("time")
            results = await add_medication(name, dosage, time)
            NEED_TO_UPDATE[0] = 1
            await record_usage("medication")
        elif func_name == "update_medication":
            medication_id = args.get("medication_id")
            name = args.get("name")
            dosage = args.get("dosage")
            time = args.get("time")
            results = await update_medication(medication_id, name, dosage, time)
            NEED_TO_UPDATE[0] = 1
            await record_usage("medication")
        elif func_name == "delete_medication":
            medication_id = args.get("medication_id")
            results = await delete_medication(medication_id)
            NEED_TO_UPDATE[0] = 1
            await record_usage("medication")
        # # UI functions
            
        elif func_name == "display_day_view":
            top = None
            start_year = args.get("start_year")
            start_month = args.get("start_month")
            start_day = args.get("start_day")
            end_year = args.get("end_year")
            end_month = args.get("end_month")
            end_day = args.get("end_day")
            start_date = f"{start_year}-{start_month}-{start_day}T00:00:00"
            end_date = f"{end_year}-{end_month}-{end_day}T23:59:59"
            results = await display_day_view(graph, top, start_date, end_date, just_events='yes')
            await record_usage("UI")
        elif func_name == "show_welcome_screen":
            results = await display_view("welcome-view")
            await record_usage("UI")
        elif func_name == "show_mirror":
            results = await display_view("mirror-view")
            await record_usage("UI")
        elif func_name== "show_medications":
            results = await display_view("medications-view")
            await record_usage("UI")
        elif func_name == "show_todo_tasks":
            results = await display_view("todos-view")
            await record_usage("UI")
        
        # ================================================
        # Reminder function calls
        # ================================================
            
        elif func_name == "get_reminders":
            results = schedular.get_reminders()
        elif func_name == "add_reminder":
            reminder_name = args.get("reminder_name")
            reminder_message = args.get("reminder_message", "No message")
            year = args.get("Year")
            month = args.get("Month")
            day = args.get("Day")
            hour = args.get("Hour")
            minute = args.get("Minute")
            second = args.get("Second")
            date = datetime(year, month, day, hour, minute, second)      
            results = schedular.create_reminder(date, reminder_name, reminder_message)
            NEED_TO_UPDATE[2] = 1
            await record_usage("reminder")
        elif func_name == "add_interval_reminder":
            reminder_name = args.get("reminder_name")
            reminder_message = args.get("reminder_message", "No message")
            weeks = args.get("weeks")
            days = args.get("days")
            hours = args.get("hours")
            minutes = args.get("minutes")
            seconds = args.get("seconds")
            start_year = args.get("start_year")
            start_month = args.get("start_month")
            start_day = args.get("start_day")
            start_hour = args.get("start_hour")
            start_minute = args.get("start_minute")
            start_second = args.get("start_second")
            end_year = args.get("end_year")
            end_month = args.get("end_month")
            end_day = args.get("end_day")
            end_hour = args.get("end_hour")
            end_minute = args.get("end_minute")
            end_second = args.get("end_second")
            start_date = datetime(start_year, start_month, start_day, start_hour, start_minute, start_second)
            end_date = datetime(end_year, end_month, end_day, end_hour, end_minute, end_second)
            results = schedular.create_interval_reminder(reminder_name, weeks, days, hours, minutes, seconds, start_date, end_date, reminder_message)
            NEED_TO_UPDATE[2] = 1
            await record_usage("reminder")
        elif func_name == "clear_all_reminders":
            results = schedular.clear_all_reminders()
            NEED_TO_UPDATE[2] = 1
            await record_usage("reminder")
        # ================================================
        else:
            results = f"Error: function {func_name} does not exist"
        
        return results, NEED_TO_UPDATE
    

    except Exception as e:
        return f"Unable to execute function call. Error: {e}", [0,0,0]
# =============================================================================
# Conversation 
# =============================================================================
class ConversationState:
    def __init__(self):
        self.in_conversation = False

    def start_conversation(self):
        self.in_conversation = True

    def end_conversation(self):
        self.in_conversation = False

async def listen_and_respond(stream, rec, myAI, graph, scheduler, UserMedications, UserCalendar, UserReminders, conversation_state, output_filename="output.wav"):
    try:
        while True:
            print("Listening for activation keyword...")
            # Assume here you adapt the keyword listening for async and it now sets the conversation state
            keyword_detected = await listen_for_keyword(stream, rec, "activate")
            if keyword_detected:
                end_of_conversation = False
                conversation_state.start_conversation()
                authorized = await confirm_user_identity(output_filename, stream, rec, myAI)
                if not authorized:
                    not_authorized_message = myAI.create_mp3("I'm sorry, I cannot confirm your identity. Goodbye.", "not_authorized.mp3")
                    if not_authorized_message is not None:
                        playsound(not_authorized_message)
                    end_of_conversation = True
                    conversation_state.end_conversation()
                    continue
                else:
                    authorized_message = myAI.create_mp3("Identity confirmed. How can I help you today?", "authorized.mp3")
                    if authorized_message is not None:
                        playsound(authorized_message)
                while not end_of_conversation:
                    end_of_conversation, need_to_update = await conversation(output_filename, stream, rec, myAI, graph, scheduler)
                    if end_of_conversation:
                        myAI.reset_messages()
                        myAI.add_message("system", system_message_2)
                        user_info =  f"{UserCalendar}, {UserMedications}, active reminders: {UserReminders}"
                        myAI.add_message("assistant", user_info)
                    if need_to_update[0]:
                        UserMedications = await get_medications()
                    if need_to_update[2]:
                        UserReminders = scheduler.get_reminders()
                conversation_state.end_conversation()
    except Exception as e:
        print(f"Error during conversation: {e}")

async def conversation(output_filename, stream, rec, myAI, graph, scheduler):
    need_to_update = [0,0,0]
    #  Give visual prompt to user
    end_of_conversation = False
    print("Listening for user input...")
    await record_audio_to_file(output_filename, stream, rec)
    # use speaker recognition to identify user
    # if user is identified
    # continue else go to security questions

    audio_file = open(output_filename, "rb")
    user_prompt = await myAI.speech_to_text(audio_file)
    print(f"User prompt: {user_prompt}")
    if "end conversation" in user_prompt.lower():
        end_of_conversation = True
    time_stamp = datetime.now()
    myAI.add_message("user", f"{user_prompt} (Message timestamp: {time_stamp})")
    assistant_message = await myAI.generate_function_response()
    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
        for call in assistant_message.tool_calls:
            results, need_to_update = await execute_function_call(graph, scheduler, call)
            myAI.add_func_message("function", call.id, call.function.name, str(results))
            if "End Conversation" in str(results).lower():
                end_of_conversation = True
    reply = await myAI.generate_chat_response()
    myAI.add_message("assistant", reply)
    print(f"Assistant reply: {reply}")
    path = await myAI.text_to_speech(str(reply))
    if path is not None:
        playsound(path)
    time.sleep(0.5)
    return end_of_conversation, need_to_update

async def confirm_user_identity(output_filename, stream, rec, myAI):
    confirm = await myAI.text_to_speech("Please confirm your identity by saying your pass phrase")
    if confirm is not None:
        playsound(confirm)
    time.sleep(0.5)
    await record_audio_to_file(output_filename, stream, rec)
    audio_file = open(output_filename, "rb")
    with open('Secret_Phrase', 'r') as file:
        secret_phrase = file.read().replace('\n', '')
    
    user_prompt = await myAI.speech_to_text(audio_file)
    if secret_phrase.lower() in user_prompt.lower():
        return True

    


# =============================================================================
# Main event loop 
# =============================================================================

async def main():
    logging.basicConfig()
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    
    # Configure the outlook settings
    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']
    graph: Graph = Graph(azure_settings)


    # Configure the Vosk settings
    model_path = "/Users/annushka/Documents/GitHub/MedMirror-/vosk-model-en-us-0.22"
    output_filename = "output.wav"
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    stream.start_stream()

   
    # Get user info and greet the user
    keyword = "activate"
    user = await get_user(graph)
    
    
    # Initialise openAI chatbot
    myAI = MyAI(TOOLS, MESSAGES)
    
    # Initialise the scheduler
    scheduler = myScheduler(myAI)
    # print(scheduler.get_state())
    
    # UserToDoLists = await get_ToDo_lists(graph)
    UserMedications = await get_medications()
    UserReminders = scheduler.get_reminders()
    UserCalendar = await get_calendars(graph)
   
    
    #  user info message 
    user_info =  f"{UserCalendar}, {UserMedications}, active reminders: {UserReminders}"
    myAI.add_message("assistant", user_info)

    # intiialise UI
    # switch_view = await display_view("welcome-view")
    results = await display_view("calendar-view")
    
    # greet user 
    greeting = "Hello " + (user.display_name).split(" ")[0] + ". I will be the voice behind the mirror,\
                 If you need any help just say the keyword 'activate' and I will be here to help you. If you would like to leave the conversation\
                just say 'end conversation'."
    
    myAI.add_message("assistant", greeting)
    path_to_greeting = await myAI.text_to_speech(greeting)
    if path_to_greeting is not None:
        playsound(path_to_greeting)
    

    # Initialise the conversation state
    conversation_state = ConversationState()

    # Create test reminder
    # scheduler.create_reminder(datetime.now() + timedelta(seconds = 30), "This is a test reminder")
    # scheduler.create_interval_reminder(0, 0, 0, 1, 0, datetime.now() + timedelta(seconds = 15), datetime.now() + timedelta(minutes = 10), "This is a test interval reminder for every minute")
    
    # Start the main conversation loop
    conversation_task = asyncio.create_task(listen_and_respond(stream, rec, myAI, graph, scheduler, UserMedications, UserCalendar, UserReminders, conversation_state))
    reminder_task = asyncio.create_task(check_and_execute_reminders(scheduler, conversation_state))
    
    await asyncio.gather(conversation_task, reminder_task)
    print("End of main function")
# ============================================================================= #
#                           Run the main function                               #
# ============================================================================= #
        
asyncio.run(main())


