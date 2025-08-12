# jarvis_commands.py
import subprocess
import os
import sys
import json
from datetime import datetime
import speech_recognition as sr
import ollama
from vosk import KaldiRecognizer

# Add current directory to path to find other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Import shared modules
import config
from speaker import speak

# --- (Helper functions run_applescript and update_memory are unchanged) ---
def run_applescript(script: str):
    """Executes an AppleScript string."""
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"AppleScript Error: {e}")

def update_memory(log_data: dict, filename: str):
    """Appends a log entry to a specified file in the 'memory' subdirectory."""
    log_dir = os.path.join(script_dir, "memory")
    os.makedirs(log_dir, exist_ok=True)
    filepath = os.path.join(log_dir, filename)
    with open(filepath, "a") as f:
        f.write(f"--- Log Entry: {datetime.now().isoformat()} ---\n")
        for key, value in log_data.items():
            f.write(f"{key.capitalize()}: {value}\n")
        f.write("\n")

# --- CONVERSATIONAL MODE HELPERS ---

def listen_for_input():
    """
    A dedicated listener for conversational input.
    Returns the transcribed text, or None if the listener times out.
    """
    r = sr.Recognizer()
    r.pause_threshold = 1.2
    
    with sr.Microphone() as source:
        print("[Conversation] Listening for voice input...")
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = r.listen(source, timeout=25, phrase_time_limit=15)
            audio_data = audio.get_raw_data()
            
            if config.vosk_model:
                recognizer = KaldiRecognizer(config.vosk_model, audio.sample_rate)
                if recognizer.AcceptWaveform(audio_data):
                    result_json = json.loads(recognizer.Result())
                    text = result_json.get('text', '')
                    if text:
                        print(f"You (voice): {text}")
                    return text
            return ""
        except sr.WaitTimeoutError:
            print("[Conversation] Listener timed out waiting for speech to start.")
            return None  # Return a specific signal for timeout
        except Exception as e:
            print(f"[Conversation] Error during listening: {e}")
            return ""

def listen_for_input_vad(has_spoken_before=False):
    """
    A dedicated listener for conversational input that uses Voice Activity Detection (VAD)
    to determine when the user has stopped speaking.
    
    Args:
        has_spoken_before: If True, uses tighter timeout for faster conversation flow
    """
    r = sr.Recognizer()
    # Lower this for more responsive VAD. This is the number of seconds of non-speaking
    # audio before a phrase is considered complete.
    r.pause_threshold = 1.2 
    
    # This helps distinguish between background noise and speech.
    r.dynamic_energy_threshold = True

    # Smart timeout system
    if has_spoken_before:
        initial_timeout = 5   # Tighter timeout after first speech (5 seconds)
        phrase_limit = 8      # Max 8 seconds for response
        print("[Conversation VAD] Listening... (faster timeout after speech)")
    else:
        initial_timeout = 30  # Generous timeout for first speech (30 seconds)
        phrase_limit = 15     # Max 15 seconds for initial response
        print("[Conversation VAD] Listening... (30 second timeout)")

    with sr.Microphone() as source:
        # Adjust for ambient noise
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            # Listen with smart timeout
            audio = r.listen(source, timeout=initial_timeout, phrase_time_limit=phrase_limit)
            
            # Try Vosk first if available, otherwise fall back to macOS speech recognition
            if config.vosk_model:
                audio_data = audio.get_raw_data()
                recognizer = KaldiRecognizer(config.vosk_model, audio.sample_rate)
                if recognizer.AcceptWaveform(audio_data):
                    result_json = json.loads(recognizer.Result())
                    text = result_json.get('text', '')
                    if text:
                        print(f"You (VAD): {text}")
                        return text
            else:
                # Use local-only speech recognition options
                try:
                    # Try PocketSphinx (local, offline)
                    text = r.recognize_sphinx(audio)
                    if text:
                        print(f"You (VAD-Sphinx): {text}")
                        return text
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    pass
                except Exception:
                    # If Sphinx fails, try macOS built-in dictation
                    try:
                        # Use macOS built-in speech recognition via AppleScript
                        import tempfile
                        import subprocess
                        
                        # Save audio to temporary file
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                            temp_file.write(audio.get_wav_data())
                            temp_path = temp_file.name
                        
                        # Use macOS say command for basic recognition (placeholder)
                        # This is a simplified approach - in a real implementation you'd use
                        # macOS Speech Recognition APIs via PyObjC
                        print("You (VAD-Local): [Voice detected but transcription unavailable]")
                        os.unlink(temp_path)  # Clean up temp file
                        return "voice input"  # Basic fallback
                    except Exception as e:
                        print(f"[VAD] Local speech recognition error: {e}")
                        pass
            return ""
        except sr.WaitTimeoutError:
            # Timeout occurred - return special signal to indicate timeout
            print(f"[Conversation VAD] Timeout - no speech detected")
            return "TIMEOUT"
        except sr.UnknownValueError:
            # This can happen if there's a short noise that isn't speech.
            # We can just ignore it and listen again.
            return ""
        except Exception as e:
            print(f"[Conversation VAD] Error during listening: {e}")
            return ""

def create_jarvis_persona_prompt():
    """Creates the system prompt that defines Jarvis's conversational personality."""
    return """
    You are a helpful AI assistant.
    """

# --- COMMAND FUNCTIONS ---

def conversation_mode(args: dict):
    """Activates a conversational mode that uses VAD."""
    speak("Of course, sir. I am here to assist.")
    
    client = ollama.Client()
    messages = [{'role': 'system', 'content': create_jarvis_persona_prompt()}]
    
    while True:
        user_input = listen_for_input_vad()
        
        if not user_input:
            continue

        # Check for exit phrases to leave the conversational mode
        if any(phrase in user_input.lower() for phrase in ["that's all for now", "exit conversation", "end conversation"]):
            speak("Very good, sir. Standing by.")
            break
        
        messages.append({'role': 'user', 'content': user_input})
        
        try:
            response = client.chat(model='llama3:8b', messages=messages)
            assistant_response = response['message']['content']
            messages.append({'role': 'assistant', 'content': assistant_response})
            speak(assistant_response)
        except Exception as e:
            print(f"Error during LLM chat: {e}")
            speak("I seem to be having trouble connecting to my core reasoning module, sir.")

    return 'CONTINUE_LOOP' # Ensure we continue listening after conversation.

def write_this_down(args: dict):
    """Saves provided text content to a notes file."""
    content_to_save = args.get("content")
    if not content_to_save:
        return "Sir, what would you like me to write down?"
    try:
        log_entry = {"command": "write_this_down", "content": content_to_save}
        update_memory(log_entry, "notes_log.txt")
        return "Note taken, sir."
    except Exception as e:
        print(f"[COMMAND] ERROR in write_this_down: {e}")
        return "I'm sorry, sir. I encountered an error while trying to take that note."

def clear_workspace(args):
    """Quits common applications."""
    apps_to_quit = ["Safari", "Mail", "Calendar", "Music", "Preview", "Messages"]
    for app in apps_to_quit:
        run_applescript(f'tell application "{app}" to quit')
    return "At once, sir."

def open_dev_environment(args):
    """Opens VS Code and Terminal."""
    try:
        run_applescript('tell application "Visual Studio Code" to activate')
        run_applescript('tell application "Terminal" to activate')
        return "Initiating development protocols."
    except Exception as e:
        return f"I encountered an error opening the dev environment: {e}"

def security_lockdown(args):
    """Example function to trigger a custom audio file."""
    print("[COMMAND] Initiating security lockdown procedures.")
    return "Affirmative sir, security lockdown initiated."

def take_screenshot(args):
    """Takes a screenshot and saves it to the desktop and Photos."""
    try:
        # Create a unique filename with a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Save directly to Desktop first (more reliable)
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", f"JARVIS_Screenshot_{timestamp}.png")
        
        # Use the built-in screencapture utility on macOS to take a non-interactive screenshot
        subprocess.run(["screencapture", "-C", desktop_path], check=True)
        
        # Try to import to Photos (optional, won't fail if Photos is unavailable)
        try:
            applescript = f'''
                set theImage to POSIX file "{desktop_path}"
                tell application "Photos"
                    activate
                    import theImage
                end tell
            '''
            run_applescript(applescript)
            return f"Screenshot captured and saved to Desktop and Photos, sir. File: JARVIS_Screenshot_{timestamp}.png"
        except:
            return f"Screenshot captured and saved to Desktop, sir. File: JARVIS_Screenshot_{timestamp}.png"
            
    except Exception as e:
        print(f"[COMMAND] ERROR in take_screenshot: {e}")
        return "I'm sorry, sir. I was unable to capture the screen."

def open_application(args: dict):
    """Opens a specified application by name."""
    app_name = args.get("app_name")
    if not app_name:
        return "Sir, which application would you like to open?"
    try:
        # Use AppleScript to activate the application
        run_applescript(f'tell application "{app_name}" to activate')
        return f"Opening {app_name}, sir."
    except Exception as e:
        print(f"[COMMAND] ERROR in open_application: {e}")
        return f"I'm sorry, sir. I was unable to open {app_name}."

def start_avatar_video(args: dict):
    """Start the JARVIS avatar video playback."""
    try:
        # Import and use the AppleScript avatar video player
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        
        from jarvis_avatar_applescript import play_jarvis_avatar
        success = play_jarvis_avatar()
        
        if success:
            return "Avatar video activated, sir. I am now visible on your screen."
        else:
            return "I'm sorry, sir. I was unable to start the avatar video."
    except Exception as e:
        print(f"[COMMAND] ERROR in start_avatar_video: {e}")
        return "Avatar video system encountered an error, sir."

def stop_avatar_video(args: dict):
    """Stop the JARVIS avatar video playback."""
    try:
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        
        from jarvis_avatar_applescript import stop_jarvis_avatar
        success = stop_jarvis_avatar()
        
        if success:
            return "Avatar video deactivated, sir. I remain at your service."
        else:
            return "Avatar video system is already offline, sir."
    except Exception as e:
        print(f"[COMMAND] ERROR in stop_avatar_video: {e}")
        return "I encountered an issue with the avatar video system, sir."

# --- UNIFIED COMMAND DICTIONARY ---
commands = {
    "speak freely": conversation_mode,
    "clear the workspace": clear_workspace,
    "open dev environment": open_dev_environment,
    "write this down": write_this_down,
    "security lockdown": security_lockdown,
    "take a screenshot": take_screenshot,
    "open_application": open_application,
    "show yourself": start_avatar_video,
    "activate avatar": start_avatar_video,
    "start avatar video": start_avatar_video,
    "hide yourself": stop_avatar_video,
    "deactivate avatar": stop_avatar_video,
    "stop avatar video": stop_avatar_video,
}