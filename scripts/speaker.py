# speaker.py
import os
import re
import time
import pygame
import pyttsx3
import threading

# Global lock to prevent multiple TTS from playing simultaneously
_tts_lock = threading.Lock() 

def generate_filename_from_text(text: str) -> str:
    """Converts a sentence into a standardized, safe filename."""
    if not text:
        return ""
    # Remove punctuation, convert to lowercase, and replace spaces with underscores
    clean_text = re.sub(r'[^\w\s]', '', text).lower()
    return re.sub(r'\s+', '_', clean_text).strip() + ".mp3"

def speak(text: str):
    """
    Speaks the given text using a local audio file or offline Windows TTS.
    """
    if not text:
        return

    # Use lock to prevent multiple TTS from playing simultaneously
    with _tts_lock:
        # --- 1. Find the local audio file in the 'soundboard' directory ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir) # Assumes 'scripts' is one level down
        audio_dir = os.path.join(project_root, "data", "soundboard")

        filename = generate_filename_from_text(text)
        filepath = os.path.join(audio_dir, filename)

        # --- 2. Play the file if it exists ---
        if os.path.exists(filepath):
            print(f"[Speaker] Found audio file: '{filename}'. Playing...")
            try:
                pygame.mixer.init()
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                pygame.mixer.quit()
                return
            except Exception as e:
                print(f"[Speaker] ERROR: Failed to play audio file '{filepath}'. Error: {e}")
                
        # --- 3. Fallback to offline TTS if file doesn't exist ---
        print(f"[Speaker] No local file found for '{text}'. Using system TTS.")
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[Speaker] TTS Error: {e}")