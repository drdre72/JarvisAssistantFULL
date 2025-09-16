"""
text_to_speech.py - Text-to-Speech using Windows SAPI and local voices
Implements Jamie voice fallback and local voice management
"""

import os
import pyttsx3
import threading
import time
from pathlib import Path
import subprocess

class JarvisTTS:
    def __init__(self):
        """Initialize TTS engine with Windows SAPI and local voices"""

        # Get paths relative to portable structure
        self.base_path = Path(__file__).parent.parent
        self.voices_path = self.base_path / "models" / "voices"

        # Initialize Windows SAPI TTS engine
        self.sapi_engine = None
        self.is_speaking = False
        self.speech_lock = threading.Lock()

        self._initialize_sapi()
        self._load_voice_profiles()

    def _initialize_sapi(self):
        """Initialize Windows SAPI TTS engine"""
        try:
            self.sapi_engine = pyttsx3.init()

            # Configure voice settings
            voices = self.sapi_engine.getProperty('voices')
            if voices:
                # Prefer male voice if available
                male_voice = None
                for voice in voices:
                    if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                        male_voice = voice
                        break

                if male_voice:
                    self.sapi_engine.setProperty('voice', male_voice.id)
                    print(f"[JarvisTTS] Using SAPI voice: {male_voice.name}")
                else:
                    # Use first available voice
                    self.sapi_engine.setProperty('voice', voices[0].id)
                    print(f"[JarvisTTS] Using SAPI voice: {voices[0].name}")

            # Set speech rate and volume
            self.sapi_engine.setProperty('rate', 180)  # Slightly faster than default
            self.sapi_engine.setProperty('volume', 0.9)

            print("[JarvisTTS] Windows SAPI TTS initialized successfully")

        except Exception as e:
            print(f"[JarvisTTS] Warning: Could not initialize SAPI TTS: {e}")
            self.sapi_engine = None

    def _load_voice_profiles(self):
        """Load available local voice models"""
        self.local_voices = {}

        if self.voices_path.exists():
            for voice_file in self.voices_path.glob("*.bin"):
                voice_name = voice_file.stem
                self.local_voices[voice_name] = voice_file
                print(f"[JarvisTTS] Found local voice: {voice_name}")

        if self.local_voices:
            print(f"[JarvisTTS] Loaded {len(self.local_voices)} local voice models")
        else:
            print("[JarvisTTS] No local voice models found, using SAPI fallback")

    def speak(self, text, voice="auto", async_mode=False):
        """
        Speak text using best available voice

        Args:
            text: Text to speak
            voice: Voice preference ("jamie", "sapi", "auto")
            async_mode: Speak asynchronously if True

        Returns:
            Success status
        """

        if not text or not text.strip():
            return False

        with self.speech_lock:
            if self.is_speaking:
                print("[JarvisTTS] Already speaking, queuing...")

        if async_mode:
            thread = threading.Thread(target=self._speak_sync, args=(text, voice))
            thread.daemon = True
            thread.start()
            return True
        else:
            return self._speak_sync(text, voice)

    def _speak_sync(self, text, voice):
        """Synchronous speech implementation"""

        with self.speech_lock:
            self.is_speaking = True

        try:
            # Determine best voice to use
            if voice == "auto":
                if "jamie-voice" in self.local_voices:
                    voice = "jamie"
                else:
                    voice = "sapi"

            # Try local voice first (if specified and available)
            if voice == "jamie" and "jamie-voice" in self.local_voices:
                success = self._speak_local_voice(text, "jamie-voice")
                if success:
                    return True
                else:
                    print("[JarvisTTS] Local voice failed, falling back to SAPI")

            # Fall back to Windows SAPI
            return self._speak_sapi(text)

        finally:
            with self.speech_lock:
                self.is_speaking = False

    def _speak_local_voice(self, text, voice_name):
        """Speak using local voice model (placeholder for future implementation)"""

        # This is a placeholder for local voice synthesis
        # In a full implementation, this would use the local voice models
        # For now, we'll fall back to SAPI

        print(f"[JarvisTTS] Local voice synthesis not yet implemented for {voice_name}")
        return False

    def _speak_sapi(self, text):
        """Speak using Windows SAPI"""

        if not self.sapi_engine:
            print("[JarvisTTS] SAPI engine not available")
            return False

        try:
            print(f"[JarvisTTS] Speaking with SAPI: '{text[:50]}...'")
            self.sapi_engine.say(text)
            self.sapi_engine.runAndWait()
            return True

        except Exception as e:
            print(f"[JarvisTTS] SAPI speech error: {e}")
            return False

    def stop_speaking(self):
        """Stop current speech"""
        if self.sapi_engine:
            try:
                self.sapi_engine.stop()
            except:
                pass

        with self.speech_lock:
            self.is_speaking = False

    def is_busy(self):
        """Check if currently speaking"""
        return self.is_speaking

    def get_available_voices(self):
        """Get list of available voices"""
        voices = []

        # Add SAPI voices
        if self.sapi_engine:
            sapi_voices = self.sapi_engine.getProperty('voices')
            for voice in sapi_voices:
                voices.append({
                    "name": voice.name,
                    "type": "sapi",
                    "id": voice.id
                })

        # Add local voices
        for voice_name in self.local_voices:
            voices.append({
                "name": voice_name,
                "type": "local",
                "path": str(self.local_voices[voice_name])
            })

        return voices

    def set_voice_settings(self, rate=None, volume=None):
        """Adjust voice settings"""
        if self.sapi_engine:
            if rate is not None:
                self.sapi_engine.setProperty('rate', rate)
            if volume is not None:
                self.sapi_engine.setProperty('volume', volume)

# Global instance for easy access
_tts_engine = None

def get_tts_engine():
    """Get global TTS engine instance"""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = JarvisTTS()
    return _tts_engine

def speak(text, **kwargs):
    """Convenience function for speaking text"""
    engine = get_tts_engine()
    return engine.speak(text, **kwargs)

def stop_speaking():
    """Convenience function to stop speech"""
    engine = get_tts_engine()
    engine.stop_speaking()

# Compatibility with existing speaker.py
def say(text):
    """Compatibility function for existing code"""
    return speak(text)

if __name__ == "__main__":
    # Test the TTS engine
    engine = JarvisTTS()
    engine.speak("Hello, I am JARVIS. Text to speech is working properly.")
    print("Available voices:", engine.get_available_voices())