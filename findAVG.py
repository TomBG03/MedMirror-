import asyncio
import configparser
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph import Graph
from vosk import Model, KaldiRecognizer
import pyaudio
import wave
import audioop
from datetime import datetime 
start = datetime.now()

async def find_avg_th(output_filename, stream, silence_duration=2):
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    num_silent_frames = 0
    max_silent_frames = int(16000 / 4096 * silence_duration) 
    n = 0
    X = 0 
    max_x = 0
    while True:
        end = datetime.now()
        diff = end - start
        if diff.seconds > 120:
            break
        data = stream.read(4096, exception_on_overflow=False)
        wf.writeframes(data)  


        x = audioop.rms(data, 2)
        X += x
        n += 1
        if x > max_x:
            max_x = x
    avg = X / n
    print(avg)
    print(max_x)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
stream.start_stream()      
asyncio.run(find_avg_th('output.wav', stream))