import queue
import json
import os
import sounddevice as sd
from vosk import Model, KaldiRecognizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")

q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(bytes(indata))

print("Loading model...")
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

print("Say: left, right, up, or down")

with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                       channels=1, callback=callback):
    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            if text:
                print("Heard:", text)
        else:
            partial = json.loads(recognizer.PartialResult()).get("partial", "")
            if partial:
                print("Partial:", partial)