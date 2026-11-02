"""Synthetic microphone tests; never open a real device or download a model."""

import sys
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import speech_recognition as speech


class FakeStream:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.read_count = 0
        self.stop_stream = Mock()
        self.close = Mock()

    def read(self, size):
        self.read_count += 1
        return next(self.chunks)


class SpeechCaptureTests(unittest.TestCase):
    def setUp(self):
        self.engine = object.__new__(speech.WhisperSTT)
        self.engine.sample_rate = 16000
        self.engine.chunk_size = 1024
        self.engine.channels = 1
        self.engine.audio_format = speech.pyaudio.paInt16
        self.engine.transcribe_audio_file = Mock(return_value="What is your purpose?")
        self.quiet = np.zeros(1024, dtype=np.int16).tobytes()
        self.loud = np.full(1024, 30000, dtype=np.int16).tobytes()

    def capture(self, chunks, **kwargs):
        stream = FakeStream(chunks)
        self.last_stream = stream
        audio = Mock()
        audio.open.return_value = stream
        audio.get_sample_size.return_value = 2
        with patch.object(speech.pyaudio, "PyAudio", return_value=audio):
            with patch.object(speech.time, "sleep"):
                with patch.object(speech, "get_runtime_logger") as logger:
                    text = self.engine.listen_and_transcribe(**kwargs)
        stream.stop_stream.assert_called_once()
        stream.close.assert_called_once()
        audio.terminate.assert_called_once()
        return text, stream, logger

    def test_pcm16_rms_widens_before_squaring(self):
        rms, clipped = speech.pcm16_metrics(self.loud)
        self.assertAlmostEqual(rms, 30000)
        self.assertEqual(clipped, 0)
        rms, clipped = speech.pcm16_metrics(
            np.array([-32768, 32767, 0, 0], dtype=np.int16).tobytes()
        )
        self.assertAlmostEqual(clipped, 0.5)
        self.assertGreater(rms, 23000)
        self.assertEqual(speech.pcm16_metrics(b""), (0, 0))

    def test_waiting_silence_does_not_cut_off_late_speech(self):
        # A 2.5-second pre-speech pause previously ended capture after ~2 seconds.
        text, stream, logger = self.capture(
            [self.quiet] * 40 + [self.loud] * 20 + [self.quiet] * 32,
            duration=5, max_speech_seconds=12,
        )
        self.assertEqual(text, "What is your purpose?")
        self.assertEqual(stream.read_count, 92)
        self.assertEqual(self.engine.last_capture.stop_reason, "trailing_silence")
        self.assertGreater(self.engine.last_capture.rms, 1000)
        self.assertGreater(self.engine.last_capture.normalized_rms, 0)
        self.assertLess(self.engine.last_capture.seconds, 4)
        self.assertIn("stop=%s", logger.return_value.info.call_args.args[0])
        path = self.engine.transcribe_audio_file.call_args.args[0]
        self.assertFalse(Path(path).exists())

    def test_active_speech_can_exceed_five_seconds_but_is_bounded(self):
        text, stream, _ = self.capture(
            [self.loud] * 300, duration=5, max_speech_seconds=12,
        )
        self.assertTrue(text)
        self.assertEqual(stream.read_count, 188)
        self.assertEqual(self.engine.last_capture.stop_reason, "max_speech_duration")
        self.assertGreater(self.engine.last_capture.seconds, 5)
        self.assertLessEqual(self.engine.last_capture.seconds, 12.1)
        self.assertAlmostEqual(self.engine.last_capture.rms, 30000)
        self.assertEqual(self.engine.last_transcription_status, "ok")

    def test_short_pause_and_pre_roll_do_not_lose_continuation(self):
        soft = np.full(1024, 10, dtype=np.int16).tobytes()

        def inspect_wav(path):
            with wave.open(path, "rb") as wav:
                samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
            self.assertEqual(samples[0], 10)
            self.assertEqual(samples[-33 * 1024], 30000)
            return "A complete thought"

        self.engine.transcribe_audio_file.side_effect = inspect_wav
        text, stream, _ = self.capture(
            [soft] * 8 + [self.loud] * 3 + [self.quiet] * 24
            + [self.loud] * 3 + [self.quiet] * 32,
        )
        self.assertEqual(text, "A complete thought")
        self.assertEqual(stream.read_count, 70)
        self.assertEqual(self.engine.last_capture.stop_reason, "trailing_silence")

    def test_no_activity_waits_for_full_window_without_transcribing(self):
        text, stream, _ = self.capture([self.quiet] * 100, duration=5)
        self.assertEqual(text, "")
        self.assertEqual(stream.read_count, 79)
        self.assertEqual(self.engine.last_capture.stop_reason, "no_activity")
        self.assertGreaterEqual(self.engine.last_capture.seconds, 5)
        self.assertEqual(self.engine.last_transcription_status, "not_attempted")
        self.engine.transcribe_audio_file.assert_not_called()

    def test_capture_failure_closes_microphone_without_transcribing(self):
        text, stream, _ = self.capture([self.loud])
        self.assertEqual(text, "")
        self.assertEqual(stream.read_count, 2)
        self.assertEqual(self.engine.last_capture.stop_reason, "capture_failed")
        self.engine.transcribe_audio_file.assert_not_called()

    def test_transcription_error_does_not_become_capture_error(self):
        self.engine.transcribe_audio_file.side_effect = RuntimeError("model failed")
        text, _, _ = self.capture(
            [self.loud] * 3 + [self.quiet] * 32, duration=5,
        )
        self.assertEqual(text, "")
        self.assertEqual(self.engine.last_capture.stop_reason, "trailing_silence")
        self.assertEqual(self.engine.last_transcription_status, "failed")
        path = self.engine.transcribe_audio_file.call_args.args[0]
        self.assertFalse(Path(path).exists())

    def test_transcription_receives_valid_bounded_wav_and_cleans_it(self):
        def check_file(path):
            self.last_stream.stop_stream.assert_called_once()
            self.last_stream.close.assert_called_once()
            with wave.open(path, "rb") as wav:
                self.assertEqual(wav.getframerate(), 16000)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertEqual(wav.getnchannels(), 1)
                self.assertGreater(wav.getnframes(), 1024)
            return "Hello Jarvis"

        self.engine.transcribe_audio_file.side_effect = check_file
        text, _, _ = self.capture(
            [self.loud] * 3 + [self.quiet] * 32, duration=5,
        )
        self.assertEqual(text, "Hello Jarvis")


if __name__ == "__main__":
    unittest.main()
