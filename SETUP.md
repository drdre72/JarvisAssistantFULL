# JarvisAssistant Setup Instructions

## Quick Start (Windows)

1. **Download the repository**
   ```bash
   git clone https://github.com/drdre72/JarvisAssistantFULL.git
   cd JarvisAssistantFULL
   ```

2. **Stage local offline assets**
   Follow `OFFLINE_BUNDLE.md` for the ungated Qwen2.5 GGUF, faster-whisper
   small model, CPU llama.cpp binaries and wheelhouse. They are not on GitHub.

3. **Install Dependencies**
   ```bash
   py -3.11 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements.txt
   ```

4. **Verify the offline bundle**
   Run `.\.venv\Scripts\python.exe tools\check_offline_bundle.py` to check
   local files and wheels without downloading or installing anything.

5. **Launch JarvisAssistant**
   ```bash
   launch_jarvis.bat
   ```
   This uses the project `.venv` when present. If you run `python main.py`
   directly, make sure the `.venv` is activated first (`.\.venv\Scripts\Activate.ps1`)
   or the system Python will report missing dependencies.

## GPU Acceleration (Not Yet Available)

The staged llama.cpp binaries are CPU-only. No CUDA toolkit or NVIDIA GPU is
needed, and the app does not automatically detect GPU acceleration.

### Performance Expectations
- **Bundled CPU**: roughly 7.5 tokens/second in a real smoke test on the
  development machine; conversational replies took 18-19 seconds.
- **GPU**: no supported binary staged or runtime validation completed.

## System Requirements

### Minimum
- Windows 10/11
- 16GB+ RAM recommended for the local model and speech pipeline
- 10GB free disk space
- Microphone and speakers

### Recommended
- Windows 11
- 16GB+ RAM
- CPU inference (no GPU dependency)

## Features
- Offline faster-whisper speech recognition
- Qwen2.5-7B-Instruct on local llama.cpp CPU binaries
- Windows SAPI text-to-speech and system monitoring
- Local Obsidian Markdown vault with review-gated knowledge
- Deterministic Lute-inspired memory-action authorization
- Flet desktop UI (not yet packaged as a portable release)

## Troubleshooting

### Voice Recognition Issues
- Check microphone permissions
- Adjust audio threshold in config

### Memory Vault
- The default vault is `memory/obsidian-vault/` (gitignored).
- For an existing vault, set `JARVIS_OBSIDIAN_VAULT` to an absolute existing
  folder before launching. See `OBSIDIAN_BRAIN.md` for review policies.

### Model Loading Errors
- Verify model file is exactly `models/qwen2.5-7b-instruct-q4_k_m.gguf`
- Check file size against `OFFLINE_BUNDLE.md`.
- Ensure sufficient RAM available

For verified status see `JARVIS_STATE.md`, `CURRENT_ISSUES.md`, and
`OBSIDIAN_BRAIN.md`. Offline bundle checks do not prove a packaged release.