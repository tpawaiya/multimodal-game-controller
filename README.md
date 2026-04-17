# Multimodal Game Controller

A real-time system that enables control of browser-based games using either hand gestures or voice commands.

## Overview

This project implements a multimodal input pipeline that processes visual and audio data in real time and maps them to keyboard actions. It supports two interaction modes:

* Gesture-based control using computer vision
* Voice-based control using offline speech recognition

The system is designed to operate with low latency and switch dynamically between input modes.

## Features

* Real-time hand tracking and gesture detection using MediaPipe
* Offline voice command recognition using Vosk
* Event-driven architecture for handling input signals
* Mode switching between gesture and voice control
* Integration with keyboard events via PyAutoGUI

## System Design

The application processes inputs through two independent pipelines:

1. **Gesture Pipeline**

   * Captures webcam frames using OpenCV
   * Detects hand landmarks using MediaPipe
   * Computes directional motion using temporal smoothing
   * Triggers corresponding keyboard actions

2. **Voice Pipeline**

   * Captures audio input via SoundDevice
   * Performs offline speech recognition using Vosk
   * Uses partial recognition for low-latency command detection
   * Filters commands based on a restricted vocabulary

Both pipelines feed into a shared control layer responsible for executing system-level actions.

## Tech Stack

* Python
* OpenCV
* MediaPipe
* Vosk
* PyAutoGUI
* SoundDevice

## Controls

* Press `m` to toggle between gesture and voice mode
* Press `q` to terminate the application

### Voice Commands

* `left`
* `right`
* `up` or `jump`
* `down` or `slide`

## Setup and Installation

1. Clone the repository:

```bash
git clone <your-repository-url>
cd hand_gesture_game_controller
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download the Vosk model:

* https://alphacephei.com/vosk/models
* Extract and place the folder inside the project directory:

```
vosk-model-small-en-us-0.15/
```

4. Run the application:

```bash
python multimodal_game_controller.py
```

## Notes

* Microphone access must be enabled in system settings
* The browser window must remain in focus for input to register correctly
* Gesture mode generally provides lower latency than voice mode

## Future Work

* Improve gesture classification using additional hand states
* Add a graphical interface for mode selection
* Extend the system for use in other applications beyond gaming

## Author

Tushar Singh Pawaiya 
