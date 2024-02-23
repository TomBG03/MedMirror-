# Code to combine Outlook API and OpenAI API 

#####################################################
# IMPORT LIBRARIES                                  #
#####################################################
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
#####################################################
# MAIN FUNCTIONS                                    #
#####################################################

async def main():
    print('Configuring mirror settings \n')

    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']
    graph: Graph = Graph(azure_settings)
    myAI = MyAI(TOOLS, MESSAGES)
    await greet_user(graph)

    # model_path = "/Users/annushka/Documents/GitHub/MedMirror-/vosk-model-en-us-0.22"
    # output_filename = "output.wav"

    # model = Model(model_path)
    # rec = KaldiRecognizer(model, 16000)
    # rec.SetWords(True)

    # p = pyaudio.PyAudio()
    # stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    # stream.start_stream()

    calendars, to_do_lists = await get_user_info(graph)
    myAI.add_message("user", "my calendars are " + str(calendars))
    myAI.add_message("user", "my to do lists are " + str(to_do_lists))
    end_of_conversation = False
    while not end_of_conversation:
        timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = input("Enter a prompt: ")
        myAI.add_message("user", prompt + " current date and time: " + timeStamp)
        assistant_message = await myAI.generate_function_response()
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            print(assistant_message.tool_calls)
            for call in assistant_message.tool_calls:
                results = await execute_function_call(graph, call) 
                myAI.add_func_message("function", call.id, call.function.name, str(results))
                if "conversation ended" in str(results).lower():
                    end_of_conversation = True
            reply = await myAI.generate_chat_response()
            myAI.add_message("assistant", reply)
            
        else:
            reply = await myAI.generate_chat_response()
            myAI.add_message("assistant", reply)
        
        myAI.display_messages()

        path = await myAI.text_to_speech(str(reply))
        if path is not None:
            playsound(path)
    

    # try:
    #     while True:
    #         # listen for keyword 
    #         if listen_for_keyword(stream, rec):
    #             end_of_conversation = False
    #             while not end_of_conversation:
    #                 # record audio and save it to file 
    #                 record_audio_to_file(output_filename, stream, rec)
    #                 # end of conversation defined by chat()
    #                 end_of_conversation = await chat()
                
            
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    # finally:
    #     stream.stop_stream()
    #     stream.close()
    #     p.terminate()



def record_audio_to_file(output_filename, stream, rec, silence_duration=2):
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)

    num_silent_frames = 0

    max_silent_frames = int(16000 / 4096 * silence_duration)  
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        wf.writeframes(data)  
        
        is_silent = audioop.rms(data, 2) < 1200 
        if is_silent:
            num_silent_frames += 1
        else:
            num_silent_frames = 0

        if num_silent_frames > max_silent_frames:
            print("Silence detected, stopping recording")
            break

    wf.close()

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


async def chat():
    end_of_conversation = False
    audio_file = open("output.wav", "rb")
    transcript = await MyAI.speech_to_text(audio_file)
    MyAI.add_message("user", transcript)
    assistant_message =await MyAI.generate_function_response()
    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
        for call in assistant_message.tool_calls:
            # set variable to ensure all fucntions are executed before ending conversation
            results = execute_function_call(call)
            if "conversation ended" in str(results).lower():
                end_of_conversation = True 
            MyAI.add_message("function", call.id, call.function.name, str(results))
        reply = await MyAI.generate_chat_response()
        MyAI.add_message("assistant", reply)
        # print(reply)
        MyAI.text_to_speech(str(reply))
    else:
        assistant_message = await MyAI.generate_chat_response(MESSAGES)
        MyAI.add_message("assistant", assistant_message)
        # print(assistant_message)
        MyAI.text_to_speech(str(assistant_message))
    MyAI.display_messages()
    playsound("speech.mp3")
    return end_of_conversation 



async def greet_user(graph: Graph):
    user = await graph.get_user()
    if user:
        print('Hello,', user.display_name)
        # For Work/school accounts, email is in mail property
        # Personal accounts, email is in userPrincipalName
        print('Email:', user.mail or user.user_principal_name, '\n')

async def display_access_token(graph: Graph):
    token = await graph.get_user_token()
    print('User token:', token, '\n')

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

async def send_mail(graph: Graph, subject: str = 'Hello World', body: str = 'Sent from a Python script', recipient: str = 'lu21864@bristol.ac.uk'):
    # Send mail to the signed-in user
    # Get the user for their email address
    user = await graph.get_user()
    print(user,subject,body,recipient)
    if user:
        user_email = recipient

        await graph.send_mail(subject, body, user_email)
        
        return "Email sent successfully"
        

async def get_calendar_events(graph: Graph, top: int = 5):
    event_list = []
    events = await graph.get_calendar_events(top)
    if events and events.value:
        for event in events.value:
            event_list.append(f"{event.id}: {event.subject} - {event.start.date_time} - {event.end.date_time}")
    return event_list

async def create_event(graph: Graph, calendar_id: str, subject: str, start: str, end: str, location: str = None, body: str = None, attendees: list = None, is_online : bool = False):
    await graph.create_event(calendar_id, subject, start, end, location, body, attendees, is_online)
    return "Event created successfully"

async def get_calendars(graph: Graph):
    result = await graph.get_calendars()
    return result

async def get_ToDo_lists(graph: Graph):
    result = await graph.get_ToDo_lists()
    return result

async def get_ToDo_tasks(graph: Graph, list_id: str):
    result = await graph.get_ToDo_tasks(list_id)
    return result


async def get_user_info(graph: Graph):
    calendars = await graph.get_calendars()
    to_do_lists = await graph.get_ToDo_lists()

    return calendars, to_do_lists  

async def execute_function_call(graph, tool_call):
    func_name = tool_call.function.name 
    if func_name == "get_calendars":
        results = await get_calendars(graph)
        # print(results)
    elif func_name == "get_users":
        results = await graph.get_users()
        # print(results)
    elif func_name == "get_current_datetime":
        results = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif func_name == "get_outlook_caledar_events":
        args = json.loads(tool_call.function.arguments)
        top = args.get("top", 5)
        results = await get_calendar_events(graph, top)
    elif func_name == "create_calendar_event":
        args = json.loads(tool_call.function.arguments)
        calendar_id = args["calendar_id"]
        subject = args["subject"]
        start = args["start"]
        end = args["end"]
        location = args.get("location", None)
        body = args.get("body", None)
        attendees = args.get("attendees", None)
        is_online = args.get("is_online", False)
        results = await create_event(graph, calendar_id, subject, start, end, location, body, attendees, is_online)
    elif func_name == "send_email":
        args = json.loads(tool_call.function.arguments)
        subject = args["subject"]
        body = args["body"]
        recipient = args["recipient"]
        results = await send_mail(graph, subject, body, recipient)
    elif func_name == "get_ToDo_lists":
        results = await get_ToDo_lists(graph)
    elif func_name == "get_ToDo_tasks":
        args = json.loads(tool_call.function.arguments)
        list_id = args["list_id"]
        results = await get_ToDo_tasks(graph, list_id)
    else:
        results = f"Error: function {func_name} does not exist"
    return results













# TOOLS = [
#     {
#         "type": "function",
#         "function": {
#             "name": "get_medications",
#             "description": "get user's current prescribed medications in the format 'medication_id: medication name - dosage - time'",
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "add_medication",
#             "description": "add a new prescribed medication to the user's list of medications. Each required parameter must be specified explicitly.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "name": {
#                         "type": "string",
#                         "description": "name of the medication",
#                     },
#                     "dosage": {
#                         "type": "string",
#                         "description": "The dosage of the medication in mg/g/ml, must be said explicitly and must be specific.",
#                     },
#                     "time": {
#                         "type": "string",
#                         "description": "Time of day to take the medication, must be specific",
#                     }
#                 },
#                 "required": ["name", "dosage", "time"]
#             },
#         }
#     }, 
#     {
#         "type": "function",
#         "function": {
#             "name": "delete_medication",
#             "description": "delete/remove a medication from the user's list of medications by its medication_id",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "medication_id": {
#                         "type": "string",
#                         "description": "ID of the medication",
#                     },
#                 },
#                 "required": ["medication_id"]
#             },
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "end_conversation",
#             "description": "Ends the current conversation with the user, can be inferred from users input or silence, e.g. 'goodbye', 'bye', 'stop', 'end conversation', 'that's all thank you' etc.",
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "add_calendar_event",
#             "description": "Add an event to the user's calendar, can infer details from user's input",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "subject": {
#                         "type": "string",
#                         "description": "Subject of the event",
#                     },
#                     "start": {
#                         "type": "string",
#                         "description": "Start time of the event, must be in format 'YYYY-MM-DDTHH:MM:SS'",
#                     },
#                     "end": {
#                         "type": "string",
#                         "description": "End time of the event, must be in format 'YYYY-MM-DDTHH:MM:SS",
#                     },
#                     "location": {
#                         "type": "string",
#                         "description": "Location of the event",
#                     },
#                     "description": {
#                         "type": "string",
#                         "description": "Description of the event",
#                     }
#                 },
#                 "required": ["subject", "start", "end"]
#             }
#         }
#     },

#     {
#         "type": "function",
#         "function": {
#             "name": "get_current_datetime",
#             "description": "Get the current date and time",
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "get_calendar_events",
#             "description": "get users calendar events in the format 'event_id: event subject - start time - end time - description - location'",
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "delete_event",
#             "description": "delete/remove a calendar event from the user's calendar by using the event_id",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "event_id": {
#                         "type": "string",
#                         "description": "event id of the event to delete",
#                     },
#                 },
#                 "required": ["medication_id"]
#             },
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "get_outlook_caledar_events",
#             "description": "get events from outlook calendar",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "top": {
#                         "type": "integer",
#                         "description": "number of events to retrieve",
#                     },
#                 },
#             },
#         }
#     }
    
# ]

# def execute_function_call(tool_call):
# ## DEFINE FUNCTION CALL FOR RETREIVING CALENDAR EVENTS FROM OUTLOOK API 

#     func_name = tool_call.function.name 
#     if func_name == "get_medications":
#         results = get_medications()
#     elif func_name == "add_medication":
#         args = json.loads(tool_call.function.arguments)
#         name = args["name"]
#         dosage = args["dosage"]
#         time = args["time"]
#         results = add_medication(name, dosage, time)
#     elif func_name == "delete_medication":
#         args = json.loads(tool_call.function.arguments)
#         medication_id = args["medication_id"]
#         results = delete_medication(medication_id)



#     elif func_name == "get_calendar_events":
#         results = get_calendar_events()

#     elif func_name == "add_calendar_event":
#         args = json.loads(tool_call.function.arguments)
#         subject = args["subject"]
#         start = args["start"]
#         end = args["end"]
#         location = args.get("location", None)
#         description = args.get("description", None)
#         results = add_calendar_event(subject, start, end, location, description)

#     elif func_name == "delete_event":
#         args = json.loads(tool_call.function.arguments)
#         event_id = args["event_id"]
#         results = delete_calendar_event(event_id)

#     elif func_name == "get_current_datetime":
#         results = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     elif func_name == "end_conversation":
#         results = "Conversation ended"
#     else:
#         results = f"Error: function {func_name} does not exist"
#     return results










MESSAGES = [
    {"role": "system", "content": "You are a friendly assistant here to help the user with their health and wellness needs. Respond in English and do not switch languages. You can answer questions about their medications, schedule, and general health questions. You can also add new medications to their list or delete existing ones.Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous, make sure the user is specifc about what they want. You must decide when to perfrom multiple functions in a single response, and when to ask the user for more information. You can also end the conversation if the user says goodbye or if there is silence for a long time"},
]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendars",
            "description": "gets the users calendars and their information including the calendar_id and name",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_users",
            "description": "gets the users and their information including the user_id and name",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_outlook_caledar_events",
            "description": "get events from outlook calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "top": {
                        "type": "integer",
                        "description": "number of events to retrieve",
                    },
                },
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "send an email from the user's email account, must specify the subject, body and recipient",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "subject of the email",
                    },
                    "body": {
                        "type": "string",
                        "description": "contents of the email, can generate from user input",
                    },
                    "recipient": {
                        "type": "string",
                        "description": "email address of the recipient",
                    },
                },
                "required": ["subject", "body", "recipient"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "add new events to the user's calendar, must specify the subject, start and end times",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "ID of the calendar to add the event to",
                    },
                    "subject": {
                        "type": "string",
                        "description": "subject of the email",
                    },
                     "start": {
                        "type": "string",
                        "description": "Start time of the event, convert to format 'YYYY-MM-DDTHH:MM:SS'",
                    },
                    "end": {
                        "type": "string",
                        "description": "End time of the event, convert to format 'YYYY-MM-DDTHH:MM:SS",
                    },
                    "location": {
                        "type": "string",
                        "description": "Location of the event",
                    },
                    "body": {
                        "type": "string",
                        "description": "Body of the event",
                    },
                    "attendees": {
                        "type": "array",
                        "description": "List of attendees email addresses and names",
                        "items": {
                            "email": "string",
                            "name": "string"
                        }
                    },
                    "is_online": {
                        "type": "boolean",
                        "description": "Whether the event is online or not",
                    }
                },
                "required": ["calendar_id", "subject", "start", "end"]
            },
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "get_current_datetime",
    #         "description": "Get the current date and time in format (%Y-%m-%d %H:%M:%S)",
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "get_ToDo_lists",
            "description": "gets the users To-Do lists and their information including the list_id and name",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ToDo_tasks",
            "description": "gets the users To-Do tasks and their information including the task_id and name",
            "parameters": {
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "ID of the To-Do list",
                    },
                },
                "required": ["list_id"]
            },
        }
    }
]
asyncio.run(main())