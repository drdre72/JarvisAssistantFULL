#!/usr/bin/env python3
"""
Simple test script to diagnose llama.cpp hanging issue
"""

import subprocess
import os
from pathlib import Path

def test_llama_basic():
    """Test llama.cpp with minimal parameters"""

    base_path = Path(__file__).parent
    llama_exe = base_path / "bin" / "llama-cli.exe"
    model_path = base_path / "models" / "llama3-8b-q4.gguf"

    if not llama_exe.exists():
        print(f"❌ llama-cli.exe not found at {llama_exe}")
        return False

    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        return False

    print(f"✅ Found llama-cli.exe: {llama_exe}")
    print(f"✅ Found model: {model_path}")
    print(f"Model size: {model_path.stat().st_size / (1024**3):.2f} GB")

    # Test 1: Just show help
    print("\n🔧 Test 1: Show llama.cpp help...")
    try:
        result = subprocess.run([str(llama_exe), "-h"],
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Help command works")
        else:
            print(f"❌ Help failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("❌ Help command timed out")
    except Exception as e:
        print(f"❌ Help command error: {e}")

    # Test 2: Minimal inference test
    print("\n🔧 Test 2: Minimal inference test...")
    cmd = [
        str(llama_exe),
        "-m", str(model_path),
        "-p", "Hello",
        "-n", "5",
        "--temp", "0.1",
        "-c", "512"
    ]

    print(f"Command: {' '.join(cmd)}")

    try:
        # Very short timeout to catch hanging
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            print(f"✅ Basic inference works!")
            print(f"Output: {result.stdout.strip()}")
        else:
            print(f"❌ Inference failed")
            print(f"Return code: {result.returncode}")
            print(f"Stderr: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("❌ Inference timed out (15 seconds)")
        print("This confirms the hanging issue")
    except Exception as e:
        print(f"❌ Inference error: {e}")

if __name__ == "__main__":
    print("🧪 Testing llama.cpp binary...")
    test_llama_basic()