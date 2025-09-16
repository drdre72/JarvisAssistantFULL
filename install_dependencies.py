#!/usr/bin/env python3
"""
Install missing dependencies for JarvisAssistant LLaMA functionality
"""

import subprocess
import sys
import os
import urllib.request
from pathlib import Path

def download_file(url, filename):
    """Download a file with progress"""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False

def install_visual_cpp_redistributables():
    """Install Visual C++ Redistributables"""
    print("\n🔧 Installing Visual C++ Redistributables...")

    # Visual C++ 2019-2022 Redistributable (x64)
    vc_redist_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    vc_redist_file = "vc_redist.x64.exe"

    if download_file(vc_redist_url, vc_redist_file):
        print("Installing Visual C++ Redistributable...")
        try:
            result = subprocess.run([vc_redist_file, "/quiet", "/norestart"],
                                  check=True, timeout=300)
            print("✅ Visual C++ Redistributable installed")
            os.remove(vc_redist_file)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
        except subprocess.TimeoutExpired:
            print("❌ Installation timed out")

    return False

def install_cuda_toolkit():
    """Install CUDA Toolkit"""
    print("\n🔧 Installing CUDA Toolkit...")

    # CUDA 12.x toolkit (latest compatible with RTX A4500)
    cuda_url = "https://developer.download.nvidia.com/compute/cuda/12.6.0/network_installers/cuda_12.6.0_windows_network.exe"
    cuda_file = "cuda_installer.exe"

    print("⚠️  CUDA Toolkit is large (3GB+). This will take time...")
    if download_file(cuda_url, cuda_file):
        print("Installing CUDA Toolkit (this may take 10-30 minutes)...")
        try:
            # Silent install with minimal components
            result = subprocess.run([
                cuda_file, "-s",
                "nvcc_12.6", "curand_dev_12.6", "cublas_dev_12.6",
                "cudart_12.6", "cufft_dev_12.6"
            ], check=True, timeout=1800)  # 30 minute timeout
            print("✅ CUDA Toolkit installed")
            os.remove(cuda_file)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ CUDA installation failed: {e}")
        except subprocess.TimeoutExpired:
            print("❌ CUDA installation timed out")

    return False

def check_dependencies():
    """Check current dependency status"""
    print("🔍 Checking current dependencies...")

    # Check Visual C++ runtime
    try:
        # Try to load a DLL that requires VC++ runtime
        import ctypes
        ctypes.cdll.LoadLibrary("msvcr120.dll")
        print("✅ Visual C++ Runtime appears to be available")
    except:
        print("❌ Visual C++ Runtime missing or incomplete")

    # Check CUDA
    try:
        result = subprocess.run(["nvcc", "--version"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ CUDA Toolkit is installed")
            print(f"   Version: {result.stdout.split('release ')[1].split(',')[0]}")
        else:
            print("❌ CUDA Toolkit not found")
    except:
        print("❌ CUDA Toolkit not installed")

    # Check NVIDIA driver
    try:
        result = subprocess.run(["nvidia-smi"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ NVIDIA Driver is working")
        else:
            print("❌ NVIDIA Driver issues")
    except:
        print("❌ NVIDIA Driver tools not accessible")

def main():
    print("🚀 JarvisAssistant Dependency Installer")
    print("=" * 50)

    if not sys.platform.startswith('win'):
        print("❌ This installer is for Windows only")
        return 1

    # Check current status
    check_dependencies()

    print("\n" + "=" * 50)
    response = input("Install missing dependencies? (y/N): ").strip().lower()

    if response not in ['y', 'yes']:
        print("Installation cancelled.")
        return 0

    success = True

    # Install Visual C++ Redistributables
    success &= install_visual_cpp_redistributables()

    # Ask about CUDA (large download)
    print("\n" + "=" * 50)
    cuda_response = input("Install CUDA Toolkit? (Large download ~3GB) (y/N): ").strip().lower()

    if cuda_response in ['y', 'yes']:
        success &= install_cuda_toolkit()
    else:
        print("⚠️  Skipping CUDA installation. LLaMA may not use GPU acceleration.")

    print("\n" + "=" * 50)
    if success:
        print("✅ Installation completed! Please restart your system.")
        print("Then test: python main.py")
    else:
        print("❌ Some installations failed. Check logs above.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())