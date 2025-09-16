"""
speech_recognition.py - Speech-to-Text using faster-whisper
Replaces Vosk with faster-whisper Python library for better Windows compatibility
"""

import os
import tempfile
import wave
import time
from pathlib import Path
import pyaudio
import threading
import numpy as np

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("[WhisperSTT] Warning: faster-whisper not available, STT will be disabled")

class WhisperSTT:
    def __init__(self, model_size="small", language="en", device="cpu"):
        """Initialize Whisper speech recognition with faster-whisper"""

        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError("faster-whisper is not available")

        # Get paths relative to portable structure
        self.base_path = Path(__file__).parent.parent
        self.models_path = self.base_path / "models"

        self.model_size = model_size
        self.language = language
        self.device = device

        # Initialize faster-whisper model
        self.model = None

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16

        self._initialize_model()

    def _initialize_model(self):
        """Initialize the faster-whisper model"""
        try:
            print(f"[WhisperSTT] Loading {self.model_size} model...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8"  # Use quantized model for speed
            )
            print(f"[WhisperSTT] Model loaded successfully")
        except Exception as e:
            print(f"[WhisperSTT] Failed to load model: {e}")
            self.model = None

    def transcribe_audio_file(self, audio_file_path):
        """
        Transcribe audio file using faster-whisper

        Args:
            audio_file_path: Path to audio file

        Returns:
            Transcribed text string
        """

        if not self.model:
            print("[WhisperSTT] Model not loaded")
            return ""

        try:
            # Transcribe using faster-whisper
            segments, info = self.model.transcribe(
                str(audio_file_path),
                language=self.language,
                beam_size=5
            )

            # Combine all segments into single text
            transcription_parts = []
            for segment in segments:
                transcription_parts.append(segment.text.strip())

            transcription = ' '.join(transcription_parts).strip()
            return transcription

        except Exception as e:
            print(f"[WhisperSTT] Transcription error: {e}")
            return ""

    def listen_and_transcribe(self, duration=5, silence_threshold=25):
        """
        Record audio from microphone and transcribe

        Args:
            duration: Maximum recording duration in seconds
            silence_threshold: Audio level threshold for silence detection (increased default)

        Returns:
            Transcribed text string
        """

        # Add delay to avoid picking up TTS output
        time.sleep(1.5)

        print(f"[WhisperSTT] Listening for {duration} seconds...")

        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        try:
            # Open microphone stream
            stream = audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            frames = []
            silent_chunks = 0
            max_silent_chunks = int(self.sample_rate / self.chunk_size * 2)  # 2 seconds of silence

            for _ in range(int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size)
                frames.append(data)

                # Improved silence detection using RMS level
                audio_data = np.frombuffer(data, dtype=np.int16)
                # Handle edge case that causes sqrt warning
                mean_square = np.mean(audio_data**2)
                rms_level = np.sqrt(max(mean_square, 0))

                # Debug logging for audio levels (remove after testing)
                if rms_level > silence_threshold * 0.1:  # Only log when there's some audio
                    print(f"[WhisperSTT] Audio level: {rms_level:.1f} (threshold: {silence_threshold})")

                if rms_level < silence_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0

                # Stop if we've had enough silence
                if silent_chunks > max_silent_chunks and len(frames) > self.sample_rate / self.chunk_size:
                    print("[WhisperSTT] Silence detected, stopping recording")
                    break

            stream.stop_stream()
            stream.close()

            # Save audio to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

                # Write WAV file
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(audio.get_sample_size(self.audio_format))
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(b''.join(frames))

            # Check if we actually recorded meaningful audio
            if len(frames) < self.sample_rate / self.chunk_size * 0.5:  # Less than 0.5 seconds of audio
                print("[WhisperSTT] Insufficient audio data, skipping transcription")
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return ""

            # Calculate overall audio level to verify actual speech
            all_audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            overall_mean_square = np.mean(all_audio_data**2)
            overall_rms = np.sqrt(max(overall_mean_square, 0))

            if overall_rms < 10:  # Fixed threshold based on your actual audio levels (20-60 range)
                print(f"[WhisperSTT] Audio too quiet (RMS: {overall_rms:.1f}), likely no speech")
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return ""

            print(f"[WhisperSTT] Processing audio (RMS: {overall_rms:.1f})")

            # Transcribe the recorded audio
            transcription = self.transcribe_audio_file(temp_path)

            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass

            # Additional validation on transcription result
            if transcription:
                # Filter out common phantom transcriptions
                phantom_phrases = [
                    "thank you", "thank you for your time", "thanks", "bye", "goodbye",
                    "you", "the", "a", "an", "and", "or", "but", "so", ".",
                    "uh", "um", "hmm", "ah", "oh", "well"
                ]
                transcription_lower = transcription.lower().strip()

                # If transcription is too short or matches phantom phrases, ignore it
                if len(transcription.strip()) < 3:
                    print(f"[WhisperSTT] Transcription too short: '{transcription}'")
                    return ""

                if transcription_lower in phantom_phrases:
                    print(f"[WhisperSTT] Filtering phantom transcription: '{transcription}'")
                    return ""

                print(f"[WhisperSTT] Valid transcription: '{transcription}'")

            return transcription

        except Exception as e:
            print(f"[WhisperSTT] Recording error: {e}")
            return ""

        finally:
            audio.terminate()

    def is_available(self):
        """Check if speech recognition is available"""
        return FASTER_WHISPER_AVAILABLE and self.model is not None

# Global instance for easy access
_stt_engine = None

def get_stt_engine():
    """Get global STT engine instance"""
    global _stt_engine
    if _stt_engine is None:
        _stt_engine = WhisperSTT()
    return _stt_engine

def listen_and_transcribe(**kwargs):
    """Convenience function for speech recognition"""
    engine = get_stt_engine()
    return engine.listen_and_transcribe(**kwargs)

def transcribe_file(file_path):
    """Convenience function for file transcription"""
    engine = get_stt_engine()
    return engine.transcribe_audio_file(file_path)

if __name__ == "__main__":
    # Test the speech recognition
    engine = WhisperSTT()
    print("Say something...")
    text = engine.listen_and_transcribe(duration=5)
    print(f"You said: '{text}'")