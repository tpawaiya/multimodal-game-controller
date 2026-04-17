import speech_recognition as sr

r = sr.Recognizer()
r.dynamic_energy_threshold = True
r.energy_threshold = 300

mic = sr.Microphone()

with mic as source:
    print("Adjusting for noise...")
    r.adjust_for_ambient_noise(source, duration=2)
    print("Say one word clearly: right, left, up, or down")
    audio = r.listen(source, timeout=5, phrase_time_limit=3)

try:
    text = r.recognize_google(audio).lower()
    print("Heard:", text)
except sr.UnknownValueError:
    print("Could not understand audio")
except sr.RequestError as e:
    print("Speech recognition error:", e)