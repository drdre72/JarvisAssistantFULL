#!/usr/bin/env python3
"""
Download CUDA-enabled llama.cpp binaries for JarvisAssistant
"""

import urllib.request
import zipfile
import os
from pathlib import Path

def download_cuda_binaries():
    """Download and extract CUDA binaries"""

    print("🚀 JarvisAssistant Binary Downloader")
    print("Downloading CUDA-enabled llama.cpp binaries...")

    # URL for latest CUDA binaries
    url = 'https://github.com/ggml-org/llama.cpp/releases/download/b6490/llama-b6490-bin-win-cuda-12.4-x64.zip'
    zip_path = 'llama-cuda.zip'

    try:
        print(f"Downloading from: {url}")
        urllib.request.urlretrieve(url, zip_path)
        print(f"✅ Downloaded {zip_path} (147 MB)")

        # Create bin directory if it doesn't exist
        os.makedirs('bin', exist_ok=True)

        # Extract CUDA binaries
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('bin')

        print("✅ Extracted CUDA binaries to bin/")

        # List key binaries
        key_files = ['llama-cli.exe', 'ggml-cuda.dll', 'llama.dll']
        print("\n📁 Key binaries installed:")
        for file in key_files:
            file_path = Path('bin') / file
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024**2)
                print(f"  ✅ {file} ({size_mb:.1f} MB)")
            else:
                print(f"  ❌ {file} (missing)")

        # Clean up
        os.remove(zip_path)
        print("\n🎯 CUDA binaries ready for GPU acceleration!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please download binaries manually from:")
        print("https://github.com/ggml-org/llama.cpp/releases")

if __name__ == "__main__":
    download_cuda_binaries()