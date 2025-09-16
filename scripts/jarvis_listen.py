# jarvis_listen.py

import time

def speak(text):
    # Replace with your actual TTS/voice output logic
    print(f"Jarvis: {text}")

def get_next_voice_chunk():
    # Replace with your actual streaming microphone/audio input logic
    # Should yield short audio segments (simulate for demo)
    # For demo: just input() chunks
    return input("You: ")

def transcribe_audio_chunk(chunk):
    # Replace with your actual ASR model (e.g., Vosk, etc.)
    return chunk.strip()  # Direct passthrough for demo

def is_end_of_command(text):
    # Optional: return True if end detected (e.g., silence or keyword)
    # For now, just stop after first input for demo
    return True

def interruptible_listen(timeout=8):
    """
    Listen for user command, interrupt with 'Jarvis' at any time.
    """
    print("[Jarvis] Listening (interruptible)... (type 'jarvis' to simulate interrupt)")
    start_time = time.time()
    buffer = ""
    while (time.time() - start_time) < timeout:
        chunk = get_next_voice_chunk()
        text = transcribe_audio_chunk(chunk)
        if not text:
            continue
        if "jarvis" in text.lower():
            speak("Sir.")
            print("[Jarvis] Interrupted by hotword. Resetting listen.")
            return "interrupt"
        buffer += " " + text
        if is_end_of_command(text):
            break
    return buffer.strip()

# Example usage:
if __name__ == "__main__":
    while True:
        result = interruptible_listen(timeout=8)
        if result == "interrupt":
            continue  # Listen again!
        print(f"[Jarvis] Received: {result}")
        # Call dispatcher or command handler here
        break