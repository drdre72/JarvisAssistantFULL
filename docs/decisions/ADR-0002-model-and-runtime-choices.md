# ADR-0002: Model and inference runtime choices

**Status:** accepted · **Date:** 2026-10-28

## Decision

- LLM: **Qwen2.5-7B-Instruct Q4_K_M** (Apache-2.0, ungated) over the originally
  documented Meta Llama 3 8B (license-gated on HuggingFace).
- Runtime: **llama.cpp CPU build** (b11985 win-cpu-x64), invoked via
  `llama-completion.exe` for raw prompt completion.
- STT: **faster-whisper small** (Systran/faster-whisper-small), loaded from a
  packaged local directory only.
- TTS: **pyttsx3** (Windows SAPI), replacing the previous shell-interpolated
  PowerShell speech path (command-injection risk + a Python 3.11 parse bug).

## Consequences

- `llama-cli.exe` is chat-mode only in modern llama.cpp — reasoning code,
  launch checks, and the bundle checker all point at `llama-completion.exe`.
- GPU offload is off by default (`JARVIS_GPU_LAYERS=0`); a GPU llama.cpp build
  can be staged later without code changes.
- ~7.5 tok/s on the current CPU; acceptable for a single-user companion,
  revisit if responsiveness becomes a problem.
- Model swap = drop a different `.gguf` into `models/` and update the one
  filename constant; the provider interface is deliberately thin.
