# JarvisAssistant - Windows Portable Edition

**🚀 Professional AI Assistant with GPU Acceleration**

JarvisAssistant is a fully offline, portable AI assistant for Windows featuring advanced voice interaction, GPU-accelerated LLaMA 3 reasoning, and professional-grade performance.

## 🎯 Key Features

- **🎤 Offline Voice Recognition** - Fast, accurate speech-to-text with Whisper
- **🧠 GPU-Accelerated AI** - LLaMA 3 8B model with CUDA acceleration
- **🔊 Natural Speech Synthesis** - Windows SAPI integration
- **💾 Conversation Memory** - Persistent chat history and context
- **🖥️ System Monitoring** - Real-time performance dashboard
- **📱 Modern UI** - Beautiful Flet interface with live metrics
- **🚀 Portable Design** - Runs from USB stick, no external dependencies

## ⚡ Performance

| Configuration | Speed | Requirements |
|--------------|-------|-------------|
| **CPU-only** | 1-2 tokens/sec | 8GB RAM |
| **GPU-accelerated** | 5-20+ tokens/sec | NVIDIA GPU + CUDA |

## 🚀 Quick Start

### 1. Download & Setup
```bash
git clone https://github.com/drdre72/JarvisAssistantFULL.git
cd JarvisAssistantFULL
```

### 2. Download AI Model
Download LLaMA 3 8B model (4.6GB): [Meta-Llama-3-8B-Instruct.Q4_K_M.gguf](https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/blob/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf)

Save as: `models/llama3-8b-q4.gguf`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
python install_dependencies.py
```

### 4. Launch
```bash
python main.py
```

## 🎮 GPU Acceleration

**For NVIDIA Users:**
- Install [CUDA Toolkit 13.0+](https://developer.nvidia.com/cuda-toolkit)
- Application auto-detects GPU and enables acceleration
- Compatible with RTX 20/30/40 series cards

**Performance Boost:**
- RTX A4500: 5.21 tokens/second (all 33 layers on GPU)
- RTX 3080: ~8-12 tokens/second estimated
- RTX 4090: ~15-20+ tokens/second estimated

## 🎤 Voice Interaction

1. **Wake Word**: Say "Jarvis" to activate
2. **Natural Conversation**: Ask questions, give commands
3. **Smart Responses**: Instant replies for common queries
4. **Technical Awareness**: Jarvis knows about its own GPU acceleration!

**Example Interactions:**
- *"Jarvis, are you using CUDA or CPU?"*
- *"Tell me about your capabilities"*
- *"What's my system status?"*
- *"Can you hear me, Jarvis?"*

## 🔧 Technical Architecture

```
JarvisAssistant/
├── main.py              # 🚀 Primary launcher
├── bin/                 # 🔧 CUDA-enabled llama.cpp binaries
├── models/              # 🧠 AI models (download separately)
├── scripts/             # 📝 Core modules
│   ├── reasoning.py     # 🤖 LLaMA 3 integration
│   ├── speech_recognition.py # 🎤 Whisper STT
│   ├── speaker.py       # 🔊 Windows TTS
│   └── dispatcher.py    # 🎯 Command routing
├── memory/              # 💾 Conversation persistence
└── ui/                  # 📱 Flet interface
```

## 📋 System Requirements

### Minimum
- Windows 10/11 x64
- 8GB RAM
- 10GB free disk space
- Microphone & speakers

### Recommended
- Windows 11
- 16GB+ RAM
- NVIDIA GPU (8GB+ VRAM)
- CUDA Toolkit 13.0+

## 🚀 Latest Updates

**v1.0 - GPU Acceleration Release**
- ✅ CUDA Toolkit 13.0 integration
- ✅ llama.cpp CUDA binaries (build 6490)
- ✅ All 33 model layers GPU-accelerated
- ✅ 5x+ performance improvement
- ✅ Professional voice interaction pipeline
- ✅ Real-world validation complete

## 📚 Documentation

- **Setup Guide**: See `SETUP.md` for detailed installation
- **Development Log**: See `progress.txt` for technical details
- **Architecture**: See `PRD.txt` for project requirements

## 🤝 Contributing

Contributions welcome! This is a complete Windows Portable AI Assistant ready for enhancement and customization.

## 📄 License

MIT License - See LICENSE file for details

---

**🎯 Ready for Production Use** - Professional AI assistant with GPU acceleration, offline capabilities, and modern Windows integration.