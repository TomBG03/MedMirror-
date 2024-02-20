
import asyncio
from openai import OpenAI
from pathlib import Path
import os 
import numpy as np
from datetime import datetime

class MyAI():
    def __init__(self, TOOLS, MESSAGES):
        self.messages = MESSAGES
        self.TOOLS = TOOLS
        self.model = "gpt-3.5-turbo-1106"
        self.key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.key)
    
    
    async def speech_to_text(self, audio_file):
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcript.text

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

    
    def add_message(self, role, content):
        new_msg = {"role": role, "content": content}
        self.messages.append(new_msg)
    
    def add_func_message(self, role, tool_call_id, name, content):
        self.messages.append({"role": role, "tool_call_id": tool_call_id, "name": name, "content": content})
    