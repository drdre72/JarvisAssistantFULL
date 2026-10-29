"""Read-only checks for the planned Windows offline bundle."""

import hashlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = (
    "bin/llama-completion.exe",
    "bin/llama.dll",
    "bin/ggml.dll",
    "models/qwen2.5-7b-instruct-q4_k_m.gguf",
    "models/whisper-small/model.bin",
    "models/whisper-small/config.json",
)


def verify_wheelhouse(root, wheelhouse):
    """Check that every wheel matches the recorded SHA-256 inventory."""
    manifest = root / "wheelhouse.sha256"
    if not manifest.is_file():
        return ["Missing wheelhouse.sha256 inventory."]

    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+\.whl)", line)
        if not match or match[2] in expected:
            return ["Invalid or duplicate entry in wheelhouse.sha256."]
        expected[match[2]] = match[1]

    actual = {wheel.name: wheel for wheel in wheelhouse.glob("*.whl")}
    if not expected or set(actual) != set(expected):
        return ["Wheelhouse filenames do not match wheelhouse.sha256."]

    problems = []
    for name, wheel in actual.items():
        digest = hashlib.sha256()
        with wheel.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected[name]:
            problems.append(f"Wheel hash mismatch: {name}")
    return problems


def check_bundle(root=ROOT, *, resolve_wheels=True):
    """Return blockers without downloading, installing, or running native assets."""
    root = Path(root)
    blockers = []

    if sys.version_info[:2] != (3, 11) or sys.maxsize <= 2**32:
        blockers.append("Use 64-bit Python 3.11 for this bundle baseline.")

    for relative_path in REQUIRED_FILES:
        if not (root / relative_path).is_file():
            blockers.append(f"Missing runtime asset: {relative_path}")

    stt_source = root / "scripts/speech_recognition.py"
    if stt_source.is_file():
        source = stt_source.read_text(encoding="utf-8")
        if re.search(r"WhisperModel\(\s*self\.model_size\b", source):
            blockers.append("Speech recognition still loads a model name, not a local path.")
        if "local_files_only=True" not in source:
            blockers.append("Speech recognition must disable model downloads.")

    requirements = root / "requirements.txt"
    if not requirements.is_file():
        blockers.append("Missing requirements.txt.")
    else:
        lines = requirements.read_text(encoding="utf-8").splitlines()
        if any(
            line.strip() and not line.lstrip().startswith("#")
            and ("://" in line or line.lstrip().startswith(("-e", "--", "git+")))
            for line in lines
        ):
            blockers.append("Requirements contain a direct URL or pip option; offline resolution skipped.")
            resolve_wheels = False

    wheelhouse = root / "wheelhouse"
    if not wheelhouse.is_dir() or not any(wheelhouse.glob("*.whl")):
        wheel_problems = ["Missing wheelhouse/*.whl for Python 3.11 on Windows x64."]
    else:
        wheel_problems = verify_wheelhouse(root, wheelhouse)
    blockers.extend(wheel_problems)

    if (
        wheelhouse.is_dir() and not wheel_problems
        and resolve_wheels and requirements.is_file()
    ):
        command = [
            sys.executable, "-m", "pip", "--isolated", "install", "--dry-run",
            "--ignore-installed", "--no-index", "--disable-pip-version-check",
            "--find-links", str(wheelhouse), "-r", str(requirements),
        ]
        try:
            result = subprocess.run(
                command, cwd=root, capture_output=True, text=True, timeout=120
            )
            if result.returncode:
                blockers.append("Wheelhouse cannot resolve all requirements without an index.")
        except (OSError, subprocess.TimeoutExpired):
            blockers.append("Offline wheel resolution could not complete.")

    return blockers


if __name__ == "__main__":
    problems = check_bundle()
    if problems:
        print("Offline bundle NOT READY:")
        for problem in problems:
            print(f"- {problem}")
        sys.exit(1)
    print("Offline artifacts present; wheel dependencies resolve without an index.")
    print("Native binaries and network-disabled application startup still need testing.")
