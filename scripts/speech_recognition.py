"""
speech_recognition.py - Speech-to-Text using faster-whisper
Replaces Vosk with faster-whisper Python library for better Windows compatibility
"""

import os
import tempfile
import wave
import time
from collections import deque
from dataclasses import dataclass
from math import ceil
from pathlib import Path
import pyaudio
import numpy as np

from runtime_log import get_runtime_logger


@dataclass(frozen=True)
class CaptureMetrics:
    stop_reason: str
    seconds: float
    rms: float
    normalized_rms: float
    clipped_fraction: float


def pcm16_metrics(data):
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)
    if not samples.size:
        return 0.0, 0.0
    rms = float(np.sqrt(np.mean(samples * samples)))
    clipped = float(np.count_nonzero(np.abs(samples) >= 32760) / samples.size)
    return rms, clipped

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
        self.base_path = Path(
            os.environ.get("JARVIS_BASE_PATH", Path(__file__).resolve().parent.parent)
        )
        self.models_path = self.base_path / "models"

        self.model_size = model_size
        self.model_path = self.models_path / f"whisper-{model_size}"
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
        if not all(
            (self.model_path / filename).is_file()
            for filename in ("model.bin", "config.json")
        ):
            raise FileNotFoundError(
                f"Offline Whisper model missing from {self.model_path} "
                "(requires model.bin and config.json)"
            )

        try:
            print(f"[WhisperSTT] Loading local model from {self.model_path}...")
            self.model = WhisperModel(
                str(self.model_path),
                device=self.device,
                compute_type="int8",  # Use quantized model for speed
                local_files_only=True,
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
            self.last_transcription_status = "model_unavailable"
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
            self.last_transcription_status = "ok" if transcription else "empty"
            return transcription

        except Exception as e:
            print(f"[WhisperSTT] Transcription error: {e}")
            self.last_transcription_status = "failed"
            return ""

    def listen_and_transcribe(self, duration=5, silence_threshold=25, max_speech_seconds=12):
        """
        Wait for speech, then record until a pause or a bounded speech deadline.

        Args:
            duration: Maximum time to wait for speech to begin, in seconds
            silence_threshold: Provisional raw PCM16 RMS activity threshold;
                requires calibration against real recordings.
            max_speech_seconds: Maximum recording time after detected activity.

        Returns:
            Transcribed text string
        """

        if duration <= 0 or max_speech_seconds <= 0 or silence_threshold < 0:
            raise ValueError("Audio capture limits must be positive")

        self.last_capture = None
        self.last_transcription_status = "not_attempted"
        # Add delay to avoid picking up TTS output
        time.sleep(1.5)

        print(f"[WhisperSTT] Waiting up to {duration} seconds for speech...")
        audio = None
        stream = None
        temp_path = None
        stage = "capture"
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            frames = []
            pre_roll = deque(maxlen=max(1, ceil(0.3 * self.sample_rate / self.chunk_size)))
            waited_chunks = 0
            waiting_energy = 0.0
            waiting_samples = 0
            waiting_clipped = 0.0
            silent_chunks = 0
            wait_chunks = ceil(self.sample_rate * duration / self.chunk_size)
            speech_chunks = ceil(self.sample_rate * max_speech_seconds / self.chunk_size)
            pause_chunks = ceil(self.sample_rate * 2 / self.chunk_size)
            stop_reason = "no_activity"
            while True:
                data = stream.read(self.chunk_size)
                rms_level, clipped_fraction = pcm16_metrics(data)
                if not frames:
                    if rms_level > silence_threshold:
                        frames.extend(pre_roll)
                        frames.append(data)
                        pre_roll.clear()
                    else:
                        pre_roll.append(data)
                        waited_chunks += 1
                        sample_count = len(data) // 2
                        waiting_energy += rms_level * rms_level * sample_count
                        waiting_clipped += clipped_fraction * sample_count
                        waiting_samples += sample_count
                        if waited_chunks >= wait_chunks:
                            break
                    continue
                frames.append(data)
                if rms_level > silence_threshold:
                    silent_chunks = 0
                else:
                    silent_chunks += 1
                if silent_chunks >= pause_chunks:
                    stop_reason = "trailing_silence"
                    break
                if len(frames) >= speech_chunks:
                    stop_reason = "max_speech_duration"
                    break

            stream.stop_stream()
            stream.close()
            stream = None

            recorded = b"".join(frames)
            overall_rms, clipped_fraction = pcm16_metrics(recorded)
            if stop_reason == "no_activity" and waiting_samples:
                overall_rms = float(np.sqrt(waiting_energy / waiting_samples))
                clipped_fraction = waiting_clipped / waiting_samples
            measured_chunks = waited_chunks if stop_reason == "no_activity" else len(frames)
            self.last_capture = CaptureMetrics(
                stop_reason, measured_chunks * self.chunk_size / self.sample_rate,
                overall_rms, overall_rms / 32768.0, clipped_fraction,
            )
            get_runtime_logger().info(
                "audio capture stop=%s seconds=%.2f rms=%.1f clipped_fraction=%.4f",
                stop_reason, self.last_capture.seconds, overall_rms, clipped_fraction,
            )
            if stop_reason == "no_activity":
                print("[WhisperSTT] No above-threshold activity during capture")
                return ""
            print(f"[WhisperSTT] Processing audio (RMS: {overall_rms:.1f}; stop: {stop_reason})")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(audio.get_sample_size(self.audio_format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(recorded)

            stage = "transcription"
            transcription = self.transcribe_audio_file(temp_path)
            if self.last_transcription_status == "not_attempted":
                self.last_transcription_status = "ok" if transcription else "empty"

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
                    self.last_transcription_status = "filtered"
                    return ""

                if transcription_lower in phantom_phrases:
                    print(f"[WhisperSTT] Filtering phantom transcription: '{transcription}'")
                    self.last_transcription_status = "filtered"
                    return ""

                print(f"[WhisperSTT] Valid transcription: '{transcription}'")

            return transcription

        except Exception as e:
            print(f"[WhisperSTT] {stage.capitalize()} error: {e}")
            if stage == "capture":
                get_runtime_logger().warning("audio capture failed type=%s", type(e).__name__)
                self.last_capture = CaptureMetrics("capture_failed", 0.0, 0.0, 0.0, 0.0)
            else:
                get_runtime_logger().warning("audio transcription failed type=%s", type(e).__name__)
                self.last_transcription_status = "failed"
            return ""

        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            if audio is not None:
                audio.terminate()
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

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