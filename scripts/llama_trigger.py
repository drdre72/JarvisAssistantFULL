# llama_trigger.py
import sys
import os
import time
import json
import random
import datetime
from vosk import Model, KaldiRecognizer
import speech_recognition as sr
import asyncio
import websockets

# --- ROBUST PATHING SETUP ---
# Get the absolute path of the directory containing this script (e.g., .../JarvisAssistant/scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Add the script's directory to the Python path to ensure it can find sibling modules
sys.path.insert(0, script_dir)

# Now that the path is set, we can import our local modules
import config
from dispatcher import process
from speaker import speak

# --- Load the Vosk model ONCE at startup using an absolute path ---
print("Loading Vosk model into memory... (This may take a moment)")

# Get the parent directory of the script's directory (e.g., .../JarvisAssistant)
project_root = os.path.dirname(script_dir)
# Construct the absolute path to the model folder
MODEL_PATH = os.path.join(project_root, "models", "vosk-model-en-us-0.42-gigaspeech")

if not os.path.exists(MODEL_PATH):
    print(f"FATAL: Vosk model not found at the calculated path: '{MODEL_PATH}'.")
    print("Please ensure your project structure is: JarvisAssistant/models/vosk-model...")
    sys.exit(1)

# Load the model into the shared config variable
config.vosk_model = Model(MODEL_PATH)
print("Vosk model loaded.")

# --- WebSocket Server Setup ---
clients = set()

async def register(websocket):
    clients.add(websocket)

async def unregister(websocket):
    clients.remove(websocket)

async def send_to_clients(message):
    if clients:
        await asyncio.wait([client.send(json.dumps(message)) for client in clients])

async def ws_handler(websocket, path):
    await register(websocket)
    try:
        await websocket.wait_closed()
    finally:
        await unregister(websocket)

async def start_ws_server():
    server = await websockets.serve(ws_handler, "localhost", 8765)
    await server.wait_closed()

# --- Main Application Logic ---

def get_greeting():
    """Returns a time-appropriate greeting."""
    current_hour = datetime.datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def listen_for_command():
    """
    Listens for a command and uses the pre-loaded Vosk model for transcription.
    """
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    with sr.Microphone(sample_rate=16000) as source:
        print("[Jarvis] Listening...")

        try:
            audio = r.listen(source, timeout=12, phrase_time_limit=10)
            
            print("[Jarvis] Recognizing speech with Vosk...")
            audio_data = audio.get_raw_data()
            
            # Create a recognizer using the shared model
            rec = KaldiRecognizer(config.vosk_model, audio.sample_rate)
            rec.SetWords(True)
            
            rec.AcceptWaveform(audio_data)
            result = rec.FinalResult()
            result_json = json.loads(result)
            command_text = result_json.get('text', '').strip()

            if not command_text:
                print("[DEBUG] Vosk returned an empty string.")
                return ""

            print(f"You said: {command_text}")
            return command_text

        except sr.WaitTimeoutError:
            print("[Jarvis] Timeout waiting for command.")
            return "TIMEOUT"
            
        except sr.UnknownValueError:
            speak("I am sorry, I could not understand the audio.")
            return ""
        except (KeyboardInterrupt, EOFError):
            return "shutdown"

async def main_loop():
    """
    The main operational loop for Jarvis.
    """
    greeting = get_greeting()
    await send_to_clients({"type": "status", "message": f"{greeting}, sir. Awaiting orders."})
    speak(f"{greeting}, sir. Awaiting orders.")
    
    timeout_counter = 0

    while True:
        command_text = listen_for_command()

        if command_text == "TIMEOUT":
            timeout_counter += 1
            if timeout_counter == 1:
                response = "I'm here if you need me, sir."
                speak(response)
                await send_to_clients({"type": "status", "message": response})
            elif timeout_counter == 5:
                responses = ["Sir?", "I'm here, sir.", "Sir, I have updates on your schedule if you'd like to hear them."]
                response = random.choice(responses)
                speak(response)
                await send_to_clients({"type": "status", "message": response})
            continue
        
        timeout_counter = 0

        if command_text:
            if "never mind" in command_text.lower():
                response = "Of course, sir. Standing by."
                speak(response)
                await send_to_clients({"type": "jarvis_response", "message": response})
                break
            
            shutdown_phrases = ["shutdown", "goodbye jarvis", "exit", "goodnight jarvis", "go to sleep"]
            if any(phrase in command_text.lower() for phrase in shutdown_phrases):
                response = "Goodnight, sir."
                speak(response)
                await send_to_clients({"type": "jarvis_response", "message": response})
                break
            
            # Process the command and get the loop status
            status = process(command_text)
            
            if status == 'EXIT_LOOP':
                break # Exit and go to sleep
            else:
                # If status is 'CONTINUE_LOOP', do nothing and let the loop restart
                print("[LlamaTrigger] Conversation ended. Returning to listen.")
                speak("Awaiting orders.") # Re-prompt after a conversation
                continue
        else:
            continue

async def main():
    # Start the WebSocket server in the background
    ws_server_task = asyncio.create_task(start_ws_server())
    
    # Run the main application logic
    await main_loop()

    # Allow time for final messages to be sent before shutdown
    await asyncio.sleep(1)

if __name__ == "__main__":
    print("🚀 Initializing J.A.R.V.I.S. with WebSocket server...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔌 Shutting down...")
