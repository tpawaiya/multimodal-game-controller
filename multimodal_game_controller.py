import cv2
import mediapipe as mp
import pyautogui
import time
import os
import json
import queue
import threading
import sounddevice as sd
from collections import deque
from vosk import Model, KaldiRecognizer

# -----------------------------
# Shared state
# -----------------------------
current_mode = "gesture"  # "gesture" or "voice"
current_status = "Mode: Gesture"
status_lock = threading.Lock()
last_action_time = 0
ACTION_COOLDOWN = 0.6


def set_status(text: str):
    global current_status
    with status_lock:
        current_status = text


def trigger_key(key: str, label: str = ""):
    """Press a keyboard key with a small cooldown to avoid repeated triggers."""
    global last_action_time
    now = time.time()
    if now - last_action_time < ACTION_COOLDOWN:
        return
    pyautogui.press(key)
    last_action_time = now
    if label:
        set_status(label)
    print(f"Pressed: {key}")


def set_mode(mode: str):
    global current_mode
    current_mode = mode
    set_status(f"Mode: {mode.capitalize()}")
    print(f"Mode: {mode}")


# -----------------------------
# Voice control using Vosk
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")

voice_queue = queue.Queue()
voice_model = Model(MODEL_PATH)
voice_recognizer = KaldiRecognizer(
    voice_model,
    16000,
    '["right", "left", "up", "down", "slide", "jump", "voice", "gesture"]'
)

last_voice_action = 0
VOICE_COOLDOWN = 0.4


def voice_callback(indata, frames, time_info, status):
    if status:
        print(status)
    voice_queue.put(bytes(indata))


def voice_listener():
    global last_voice_action

    print("Voice listener ready. Say: left, right, up, down, slide, gesture, or voice")

    while True:
        if current_mode != "voice":
            time.sleep(0.05)
            continue

        try:
            data = voice_queue.get()

            if voice_recognizer.AcceptWaveform(data):
                result = json.loads(voice_recognizer.Result())
                text = result.get("text", "").lower().strip()
                if text:
                    print(f"Heard: {text}")
            else:
                partial = json.loads(voice_recognizer.PartialResult()).get("partial", "").lower().strip()
                if partial:
                    print(f"Partial: {partial}")

                    now = time.time()
                    if now - last_voice_action < VOICE_COOLDOWN:
                        continue

                    if "right" in partial:
                        trigger_key("right", "Voice: Right")
                        last_voice_action = now
                    elif "left" in partial:
                        trigger_key("left", "Voice: Left")
                        last_voice_action = now
                    elif "up" in partial or "jump" in partial:
                        trigger_key("up", "Voice: Up")
                        last_voice_action = now
                    elif "down" in partial or "slide" in partial:
                        trigger_key("down", "Voice: Down")
                        last_voice_action = now
                    elif "gesture" in partial:
                        set_mode("gesture")
                        last_voice_action = now
                    elif "voice" in partial:
                        set_mode("voice")
                        last_voice_action = now

        except Exception as e:
            print(f"Voice thread error: {e}")
            time.sleep(0.2)


# -----------------------------
# Gesture control setup
# -----------------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")

pts = deque(maxlen=5)
current_gesture = ""


def process_gesture(frame):
    global current_gesture
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    h, w, _ = frame.shape

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Flip x-coordinate to match mirrored camera view
            x = w - int(hand_landmarks.landmark[8].x * w)
            y = int(hand_landmarks.landmark[8].y * h)
            pts.append((x, y))

            if len(pts) == 5 and current_mode == "gesture":
                dx = sum(pts[i + 1][0] - pts[i][0] for i in range(4)) / 4
                dy = sum(pts[i + 1][1] - pts[i][1] for i in range(4)) / 4

                if abs(dx) > 18 and abs(dx) > abs(dy):
                    if dx > 0:
                        trigger_key("right", "Gesture: Right")
                        current_gesture = "Gesture: Right"
                    else:
                        trigger_key("left", "Gesture: Left")
                        current_gesture = "Gesture: Left"

                elif abs(dy) > 18:
                    if dy < 0:
                        trigger_key("up", "Gesture: Up")
                        current_gesture = "Gesture: Up"
                    else:
                        trigger_key("down", "Gesture: Down")
                        current_gesture = "Gesture: Down"

    return frame


# -----------------------------
# Start voice stream/thread
# -----------------------------
voice_stream = sd.RawInputStream(
    samplerate=16000,
    blocksize=800,
    dtype="int16",
    channels=1,
    callback=voice_callback,
)
voice_stream.start()

voice_thread = threading.Thread(target=voice_listener, daemon=True)
voice_thread.start()

print("Controls:")
print("- Gesture mode: swipe with your hand")
print("- Voice mode: say right, left, up, down, slide, gesture, or voice")
print("- Press m in the camera window to toggle mode")
print("- Press q to quit")

while True:
    success, frame = cap.read()
    if not success:
        continue

    frame = cv2.flip(frame, 1)
    frame = process_gesture(frame)

    with status_lock:
        status = current_status

    cv2.putText(frame, status, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.putText(frame, "Press m to switch mode", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Press q to quit", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if current_gesture:
        cv2.putText(frame, current_gesture, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

    cv2.imshow("Multimodal Game Controller", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('m'):
        if current_mode == "gesture":
            set_mode("voice")
        else:
            set_mode("gesture")

cap.release()
voice_stream.stop()
voice_stream.close()
cv2.destroyAllWindows()
