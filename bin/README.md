# Binary Directory

This directory contains the CUDA-enabled llama.cpp binaries required for GPU acceleration.

## Download Binaries

Run the download script to automatically fetch the latest CUDA binaries:

```bash
python download_binaries.py
```

## Manual Download

If the automatic download fails, manually download from:
https://github.com/ggml-org/llama.cpp/releases/download/b6490/llama-b6490-bin-win-cuda-12.4-x64.zip

Extract all files to this `bin/` directory.

## Required Files

After download, this directory should contain:
- `llama-cli.exe` - Main inference binary
- `ggml-cuda.dll` - CUDA acceleration library (333MB)
- `llama.dll` - Core llama library
- Additional supporting DLLs and executables

## GPU Acceleration

With CUDA Toolkit 13.0+ installed, these binaries will automatically utilize NVIDIA GPU acceleration for significantly improved performance.