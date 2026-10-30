# JarvisAssistant - Offline Windows Development Build

Local voice assistant with an inspectable, review-gated Obsidian memory vault.

JarvisAssistant uses local faster-whisper speech recognition, Qwen2.5-7B
inference on a staged llama.cpp CPU build, and offline Windows TTS. This is
not yet a verified portable release. See `JARVIS_STATE.md` for current truth
and `CURRENT_ISSUES.md` for limitations.

## Key Features

- **Offline Voice Recognition** - Fast, accurate speech-to-text with Whisper
- **Local AI** - Qwen2.5-7B-Instruct on the staged CPU llama.cpp runtime
- **Natural Speech Synthesis** - Windows SAPI integration
- **Inspectable Memory** - Local Markdown vault with manually approved knowledge
- **Offline Decisions** - Local capability registry and a small rule-based
  controller select relevant memory, CPU/memory readings, or a model reply
- **System Monitoring** - Real-time performance dashboard
- **Desktop UI** - Flet interface with live metrics
- **Offline Development** - Local-only runtime; portable build still unverified

## Performance

| Configuration | Speed | Requirements |
|--------------|-------|-------------|
| **Staged CPU runtime** | About 7.5 tokens/sec in a smoke test; 18-19s replies observed | 16GB+ RAM recommended |
| **GPU runtime** | Not staged or tested | Separate future build |

## Quick Start

### 1. Download & Setup
```bash
git clone https://github.com/drdre72/JarvisAssistantFULL.git
cd JarvisAssistantFULL
```

### 2. Download AI Model
Stage the ungated Qwen2.5-7B-Instruct Q4_K_M GGUF, CPU llama.cpp
binaries and faster-whisper files as documented in `OFFLINE_BUNDLE.md`.
These assets are gitignored, not included on GitHub.

Save as: `models/qwen2.5-7b-instruct-q4_k_m.gguf`

### 3. Install Dependencies
```bash
.\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements.txt
```

### 4. Launch
```bash
launch_jarvis.bat
```
This uses the project `.venv` when present; `python main.py` also works if your
system Python already has the dependencies installed.

## GPU Acceleration (Future)

The staged binaries are CPU-only. GPU offload defaults to zero; no CUDA
toolkit or automatic GPU detection is needed for the current build.

## Voice Interaction

1. **Start listening**: Use the microphone button; wake-word listening is disabled.
2. **Natural Conversation**: Ask questions or use explicit local memory commands.
3. **Local Responses**: Time, metrics and gratitude avoid inference; uncanned
   questions use the local model and may take longer on a CPU.
4. **Inspectable memory**: `OBSIDIAN_BRAIN.md` explains the local vault,
   reviewed purpose profile, bounded approved-note wikilink graph, review
   queue and deterministic memory-action gate.

**Example Interactions:**
- *"Jarvis, write this down: Call Mom tomorrow."*
- *"Remember that I prefer short answers."* (saved for review)
- *"What do you remember about my preferences?"* (approved notes only)
- *"Tell me about your capabilities"*
- *"What's my system status?"*
- *"Can you hear me, Jarvis?"*

## Technical Architecture

```
JarvisAssistant/
main.py                      # Launcher and offline asset checks
bin/                         # Ignored CPU llama.cpp binaries
models/                      # Ignored local GGUF and Whisper models
scripts/reasoning.py          # Qwen completion subprocess
scripts/speech_recognition.py # Local faster-whisper
scripts/speaker.py            # Offline Windows TTS
scripts/dispatcher.py         # Deterministic command routing
scripts/intent_gate.py        # Typed memory intent authorization
scripts/obsidian_memory.py    # Markdown vault reader/writer
scripts/capability_registry.py # Declared local abilities and evidence
scripts/decision_controller.py # Bounded offline response selection
memory/obsidian-vault/        # Ignored user-owned Obsidian vault
```

## System Requirements

### Minimum
- Windows 10/11 x64
- 16GB+ RAM recommended for the local model and speech pipeline
- 10GB free disk space
- Microphone & speakers

### Recommended
- Windows 11
- 16GB+ RAM
- CPU inference (no GPU binaries staged)

## Latest Updates

**Current development milestone:** offline voice conversation and local CPU
inference were verified on this machine. The Obsidian vault, deterministic
memory gate and first local-only decision controller are unit-tested; the
new controller needs a live voice/UI test. No online tools, general-purpose
simulation or portable release are available yet.

## Documentation

- **Setup Guide**: See `SETUP.md` for detailed installation
- **Current state and issues**: `JARVIS_STATE.md`, `CURRENT_ISSUES.md`
- **Memory setup and review**: `OBSIDIAN_BRAIN.md`
- **Development log**: `PROGRESS_LOG.md`
- **Architecture**: See `PRD.txt` for project requirements

## Contributing

Contributions welcome. Packaging and a clean-machine network-disabled launch
have not yet been verified. Run `tools/verify.ps1` for the current checks.

## License

No `LICENSE` file is present yet. Do not assume redistribution rights for
this repository or its staged third-party assets.

---

**Development status:** local voice conversation works on the development
machine; Obsidian memory and the logic gate still need live UI validation.