# record data into file
import pyaudio
import wave
import audioop
from pyAudioAnalysis.pyAudioAnalysis import audioTrainTest as aT
import asyncio
from os import listdir
from os.path import isfile, join

async def record_audio_to_file(output_filename, stream, silence_duration=2):
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    num_silent_frames = 0
    max_silent_frames = int(16000 / 4096 * silence_duration)  
    silence_threshold = 300
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        wf.writeframes(data)  
        is_silent = audioop.rms(data, 2) < silence_threshold 
        if is_silent:
            num_silent_frames += 1
        else:
            num_silent_frames = 0
        if num_silent_frames > max_silent_frames:
            print("Silence detected, stopping recording")
            break
    wf.close()

async def record():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    stream.start_stream()
    for i in range(8):
        print(f"Recording {i}")
        await record_audio_to_file(f"record{i}.wav", stream, silence_duration=2)

async def main():
    option = input("enter 1 to record, 2 to train model  ")
    if option == "1":
        await record()
    elif option == "2":
        train_model()
    else:
        print("invalid option")
    

        
def train_model():
    onlyfiles = [f for f in listdir("pyAudioAnalysis/pyAudioAnalysis/TomVoice") if isfile(join("pyAudioAnalysis/pyAudioAnalysis/TomVoice", f))]
    print(onlyfiles)
    aT.extract_features_and_train(["pyAudioAnalysis/pyAudioAnalysis/TomVoice"], 1.0, 1.0, aT.shortTermWindow, aT.shortTermStep, "svm", "VoiceRecog", False)
    print("model trained")
    # aT.file_classification("user_request.wav", "VoiceRecog","svm")


asyncio.run(main())