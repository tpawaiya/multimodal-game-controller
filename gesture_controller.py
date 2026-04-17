import cv2
import mediapipe as mp
import pyautogui
import time
from collections import deque

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Webcam
cap = cv2.VideoCapture(0)

# Store last positions
pts = deque(maxlen=5)

# Cooldown to avoid multiple triggers
last_action_time = time.time()
gesture_cooldown = 0.8

current_gesture = ""

def trigger_key(key, label):
    global last_action_time, current_gesture
    pyautogui.press(key)
    current_gesture = label
    last_action_time = time.time()
    print(f"Pressed: {key}")

while True:
    success, frame = cap.read()
    if not success:
        continue

    # Mirror camera
    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    h, w, _ = frame.shape
    current_time = time.time()

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get index finger tip
            x = w - int(hand_landmarks.landmark[8].x * w)
            y = int(hand_landmarks.landmark[8].y * h)

            pts.append((x, y))

            if len(pts) == 5 and current_time - last_action_time > gesture_cooldown:

                # Calculate average movement
                dx = sum(pts[i+1][0] - pts[i][0] for i in range(4)) / 4
                dy = sum(pts[i+1][1] - pts[i][1] for i in range(4)) / 4

                # Horizontal swipe
                if abs(dx) > 15 and abs(dx) > abs(dy):
                    if dx > 0:
                        trigger_key('right', 'Swipe Right')
                    else:
                        trigger_key('left', 'Swipe Left')

                # Vertical swipe
                elif abs(dy) > 15:
                    if dy < 0:
                        trigger_key('up', 'Jump')
                    else:
                        trigger_key('down', 'Slide')

    # Show gesture text
    if current_gesture:
        cv2.putText(frame, current_gesture, (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        if time.time() - last_action_time > 1.5:
            current_gesture = ""

    cv2.imshow("Gesture Controller", frame)

    # Press q to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()