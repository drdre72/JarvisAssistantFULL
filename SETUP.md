# JarvisAssistant Setup Instructions

## Quick Start (Windows)

1. **Download the repository**
   ```bash
   git clone https://github.com/drdre72/JarvisAssistantFULL.git
   cd JarvisAssistantFULL
   ```

2. **Download the LLaMA 3 Model**
   Download `llama3-8b-q4.gguf` (4.6GB) from HuggingFace and place it in the `models/` directory:
   ```
   https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/blob/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
   ```
   Rename it to: `models/llama3-8b-q4.gguf`

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   python install_dependencies.py
   ```

4. **Download CUDA Binaries**
   ```bash
   python download_binaries.py
   ```

   **Note**: This downloads the CUDA-enabled llama.cpp binaries (~147MB) required for GPU acceleration.

5. **Launch JarvisAssistant**
   ```bash
   python main.py
   ```

## GPU Acceleration Setup

### CUDA (NVIDIA)
- Download and install [CUDA Toolkit 13.0+](https://developer.nvidia.com/cuda-toolkit)
- The application will automatically detect and use GPU acceleration
- Compatible with RTX 20/30/40 series cards

### Performance Expectations
- **CPU-only**: 1-2 tokens/second
- **GPU-accelerated**: 5-20+ tokens/second (depending on GPU)

## System Requirements

### Minimum
- Windows 10/11
- 8GB RAM
- 10GB free disk space
- Microphone and speakers

### Recommended (GPU Acceleration)
- Windows 11
- 16GB+ RAM
- NVIDIA GPU with 8GB+ VRAM
- CUDA Toolkit 13.0+

## Features
- 🎤 Voice recognition (offline)
- 🧠 LLaMA 3 8B reasoning engine
- 🔊 Text-to-speech synthesis
- 🖥️ System monitoring dashboard
- 💾 Conversation memory
- 🚀 GPU acceleration support
- 📱 Modern Flet UI

## Troubleshooting

### Voice Recognition Issues
- Check microphone permissions
- Adjust audio threshold in config

### GPU Not Detected
- Install latest NVIDIA drivers
- Run `nvidia-smi` to verify CUDA installation
- Check `install_dependencies.py` output

### Model Loading Errors
- Verify model file is exactly `models/llama3-8b-q4.gguf`
- Check file size is ~4.6GB
- Ensure sufficient RAM available

For more details, see `progress.txt` and the project documentation.