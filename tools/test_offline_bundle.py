"""Tests for offline bundle diagnostics and legacy credential containment."""

import hashlib
import io
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

from check_offline_bundle import ROOT, check_bundle


class OfflineBundleTests(unittest.TestCase):
    @staticmethod
    def write_test_manifest(root, wheel):
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        (root / "wheelhouse.sha256").write_text(
            f"{digest}  {wheel.name}\n", encoding="utf-8"
        )

    @staticmethod
    def load_stt_with_mock_backend():
        backend = ModuleType("faster_whisper")
        backend.WhisperModel = Mock()
        audio = ModuleType("pyaudio")
        audio.paInt16 = 8
        with patch.dict(
            sys.modules,
            {"faster_whisper": backend, "pyaudio": audio, "numpy": ModuleType("numpy")},
        ):
            module = runpy.run_path(str(ROOT / "scripts" / "speech_recognition.py"))
        return module["WhisperSTT"], backend.WhisperModel

    def test_empty_bundle_reports_missing_assets_without_running_pip(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("check_offline_bundle.subprocess.run") as run:
                problems = check_bundle(directory)

            self.assertIn("Missing runtime asset: bin/llama-completion.exe", problems)
            self.assertIn(
                "Missing wheelhouse/*.whl for Python 3.11 on Windows x64.",
                problems,
            )
            run.assert_not_called()

    def test_model_name_does_not_count_as_offline_stt(self):
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory) / "scripts"
            scripts.mkdir()
            (scripts / "speech_recognition.py").write_text(
                "WhisperModel(self.model_size)\n", encoding="utf-8"
            )
            problems = check_bundle(directory, resolve_wheels=False)
            self.assertIn(
                "Speech recognition still loads a model name, not a local path.",
                problems,
            )

    def test_bundle_check_requires_local_only_model_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory) / "scripts"
            scripts.mkdir()
            (scripts / "speech_recognition.py").write_text(
                "WhisperModel(str(model_path))\n", encoding="utf-8"
            )
            problems = check_bundle(directory, resolve_wheels=False)
            self.assertIn("Speech recognition must disable model downloads.", problems)

    def test_missing_local_stt_model_fails_before_backend_loads(self):
        stt, load_model = self.load_stt_with_mock_backend()
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"JARVIS_BASE_PATH": directory}):
                with self.assertRaises(FileNotFoundError):
                    stt()
        load_model.assert_not_called()

    def test_stt_loads_packaged_path_with_downloads_disabled(self):
        stt, load_model = self.load_stt_with_mock_backend()
        with tempfile.TemporaryDirectory() as directory:
            model_dir = Path(directory) / "models" / "whisper-small"
            model_dir.mkdir(parents=True)
            (model_dir / "model.bin").write_bytes(b"test model")
            (model_dir / "config.json").write_text("{}", encoding="utf-8")
            with patch.dict(os.environ, {"JARVIS_BASE_PATH": directory}):
                stt()
            load_model.assert_called_once_with(
                str(model_dir), device="cpu", compute_type="int8", local_files_only=True
            )

    def test_direct_url_requirement_does_not_invoke_pip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements.txt").write_text(
                "example @ https://example.invalid/pkg.whl\n", encoding="utf-8"
            )
            wheelhouse = root / "wheelhouse"
            wheelhouse.mkdir()
            (wheelhouse / "example.whl").touch()
            with patch("check_offline_bundle.subprocess.run") as run:
                problems = check_bundle(root)
            self.assertTrue(any("direct URL" in item for item in problems))
            run.assert_not_called()

    def test_wheel_resolution_disables_package_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements.txt").write_text("example==1.0\n", encoding="utf-8")
            wheelhouse = root / "wheelhouse"
            wheelhouse.mkdir()
            wheel = wheelhouse / "example.whl"
            wheel.touch()
            self.write_test_manifest(root, wheel)
            with patch(
                "check_offline_bundle.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0),
            ) as run:
                check_bundle(root)
            command = run.call_args.args[0]
            for option in ("--isolated", "--dry-run", "--no-index", "--ignore-installed"):
                self.assertIn(option, command)
            self.assertEqual(run.call_args.kwargs["cwd"], root)

    def test_tampered_wheel_is_rejected_before_pip_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheelhouse = root / "wheelhouse"
            wheelhouse.mkdir()
            wheel = wheelhouse / "example.whl"
            wheel.write_bytes(b"original")
            self.write_test_manifest(root, wheel)
            wheel.write_bytes(b"changed")
            with patch("check_offline_bundle.subprocess.run") as run:
                problems = check_bundle(root)
            self.assertIn("Wheel hash mismatch: example.whl", problems)
            run.assert_not_called()

    def test_portable_tools_resolve_the_repository_root(self):
        portable = runpy.run_path(str(ROOT / "tools" / "test_portable.py"))
        builder = runpy.run_path(str(ROOT / "tools" / "build_package.py"))
        with redirect_stdout(io.StringIO()) as output:
            portable["test_portable_structure"]()
        self.assertNotIn("main.py - MISSING", output.getvalue())

        with patch("subprocess.run", side_effect=FileNotFoundError) as run:
            with redirect_stdout(io.StringIO()):
                self.assertFalse(builder["build_jarvis_package"]())
        self.assertEqual(run.call_args.kwargs["cwd"], ROOT)

    def test_legacy_listener_has_no_vendor_dependency_or_key(self):
        source = (ROOT / "scripts" / "wake_listener.py").read_text(encoding="utf-8")
        self.assertNotIn("pvporcupine", source)
        self.assertNotIn("JARVIS_PICOVOICE_ACCESS_KEY", source)

    def test_legacy_listener_stops_even_if_a_key_is_supplied(self):
        vendor = Mock()
        with patch.dict(sys.modules, {"pvporcupine": vendor, "pyaudio": Mock()}):
            with patch.dict(os.environ, {"JARVIS_PICOVOICE_ACCESS_KEY": "test-only"}):
                module = runpy.run_path(str(ROOT / "scripts" / "wake_listener.py"))
                with self.assertRaises(SystemExit) as error:
                    module["main"]()
        self.assertIn("disabled", str(error.exception))
        vendor.create.assert_not_called()

    def test_speech_fallback_passes_text_to_local_tts_without_shell(self):
        text = "hello'; Write-Output unsafe; #"
        tts = Mock()
        with patch.dict(sys.modules, {"pygame": Mock(), "pyttsx3": tts}):
            module = runpy.run_path(str(ROOT / "scripts" / "speaker.py"))
            with patch("subprocess.run") as run:
                module["speak"](text)
        tts.init.return_value.say.assert_called_once_with(text)
        tts.init.return_value.runAndWait.assert_called_once_with()
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
