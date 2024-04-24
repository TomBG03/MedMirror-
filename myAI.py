
import asyncio
from openai import OpenAI
from pathlib import Path
import os 
import numpy as np
from datetime import datetime
from termcolor import colored
import whisper
from dotenv import load_dotenv
load_dotenv()



#  USE WHISPER LOCALLY TO TRANSCRIBE AUDIO FILES

#  CHANGE TO CHAT GPT 3.5

class MyAI():
    def __init__(self, TOOLS, MESSAGES):
        self.init_messages = MESSAGES
        self.messages = MESSAGES
        self.TOOLS = TOOLS
        self.model = 'gpt-3.5-turbo'
        # self.model = "gpt-4-0125-preview"
        self.whisper_model = whisper.load_model("base")
        self.key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.key)
    
    
    async def speech_to_text(self, audio_file):
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            language="en",
        )
        return transcript.text


    # async def speech_to_text(self, audio_file):
    #     # load audio and pad/trim it to fit 30 seconds
    #     audio = whisper.load_audio(audio_file)
    #     audio = whisper.pad_or_trim(audio)
    #     # make log-Mel spectrogram and move to the same device as the model
    #     mel = whisper.log_mel_spectrogram(audio).to(self.whisper_model.device)
    #     # detect the spoken language
    #     _, probs = self.whisper_model.detect_language(mel)
    #     print(f"Detected language: {max(probs, key=probs.get)}")
    #     # decode the audio
    #     options = whisper.DecodingOptions()
    #     result = whisper.decode(self.whisper_model, mel, options)
    #     # print the recognized text
    #     return result.text
    
    async def generate_function_response(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.TOOLS,
            tool_choice='auto'
        )
        return response.choices[0].message

    async def generate_chat_response(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
        )
        return response.choices[0].message.content

    async def text_to_speech(self, text):
        speech_file_path = Path(__file__).parent / "speech.mp3"
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            speed=1.0,
            input=text
        )
        try:
            response.write_to_file(speech_file_path)
            return speech_file_path
        except Exception as e:
            return None
        
    def create_mp3(self, reminder_message, filename):
        speech_file_path = Path(__file__).parent / filename
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            speed=1.0,
            input=reminder_message
        )
        try:
            response.write_to_file(speech_file_path)
            return speech_file_path
        except Exception as e:
            return None
        
    def add_message(self, role, content):
        new_msg = {"role": role, "content": content}
        self.messages.append(new_msg)
    
    def add_func_message(self, role, tool_call_id, name, content):
        self.messages.append({"role": role, "tool_call_id": tool_call_id, "name": name, "content": content})
    
    def display_messages(self):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        
        for message in self.messages:
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

    def reset_messages(self):
        self.messages = []