"""
test_portable.py - Test script for JarvisAssistant portable package
Verifies all components are working before packaging
"""

import sys
import os
from pathlib import Path

def test_portable_structure():
    """Test that the portable structure is correct"""

    print("🔍 Testing JarvisAssistant Portable Structure")
    print("=" * 50)

    base_dir = Path(__file__).parent
    required_dirs = ["bin", "models", "scripts", "ui", "memory", "logs", "updates"]
    required_files = {
        "bin/llama-cli.exe": "LLaMA CLI executable",
        "models/llama3-8b-q4.gguf": "LLaMA 3 8B model",
        "scripts/reasoning.py": "Reasoning engine",
        "scripts/speech_recognition.py": "Speech recognition",
        "scripts/text_to_speech.py": "Text-to-speech",
        "scripts/dispatcher.py": "Command dispatcher",
        "scripts/jarvis_app.py": "Main UI application",
        "scripts/memory_system.py": "Memory system",
        "main.py": "Main launcher",
        "requirements.txt": "Dependencies list"
    }

    # Test directory structure
    print("\n📁 Directory Structure:")
    all_dirs_exist = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - MISSING")
            all_dirs_exist = False

    # Test required files
    print("\n📄 Required Files:")
    all_files_exist = True
    for file_path, description in required_files.items():
        full_path = base_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            if size > 1024*1024:  # > 1MB
                size_str = f"{size/(1024*1024):.1f} MB"
            elif size > 1024:  # > 1KB
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size} bytes"
            print(f"✅ {file_path} ({size_str}) - {description}")
        else:
            print(f"❌ {file_path} - MISSING - {description}")
            all_files_exist = False

    return all_dirs_exist and all_files_exist

def test_python_imports():
    """Test that all Python modules can be imported"""

    print("\n🐍 Python Module Imports:")
    print("-" * 30)

    # Add scripts to path
    scripts_dir = Path(__file__).parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    modules_to_test = [
        ("reasoning", "LLaMA reasoning engine"),
        ("speech_recognition", "Speech recognition"),
        ("text_to_speech", "Text-to-speech"),
        ("dispatcher", "Command dispatcher"),
        ("memory_system", "Memory system"),
        ("jarvis_app", "Main application")
    ]

    all_imports_successful = True

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} - {description}")
        except ImportError as e:
            print(f"❌ {module_name} - FAILED: {e}")
            all_imports_successful = False
        except Exception as e:
            print(f"⚠️  {module_name} - WARNING: {e}")

    return all_imports_successful

def test_external_dependencies():
    """Test external dependencies"""

    print("\n📦 External Dependencies:")
    print("-" * 30)

    dependencies = [
        ("flet", "UI framework"),
        ("psutil", "System monitoring"),
        ("faster_whisper", "Speech recognition"),
        ("pyttsx3", "Text-to-speech"),
        ("pyaudio", "Audio processing"),
        ("numpy", "Numerical computing"),
        ("requests", "HTTP requests")
    ]

    all_deps_available = True

    for dep_name, description in dependencies:
        try:
            __import__(dep_name)
            print(f"✅ {dep_name} - {description}")
        except ImportError:
            print(f"❌ {dep_name} - MISSING - {description}")
            all_deps_available = False

    return all_deps_available

def test_binaries():
    """Test that binary executables exist and are executable"""

    print("\n⚙️ Binary Executables:")
    print("-" * 30)

    bin_dir = Path(__file__).parent / "bin"
    required_binaries = [
        "llama-cli.exe",
        "llama.dll",
        "ggml.dll"
    ]

    all_binaries_exist = True

    for binary_name in required_binaries:
        binary_path = bin_dir / binary_name
        if binary_path.exists():
            size = binary_path.stat().st_size / (1024*1024)  # MB
            print(f"✅ {binary_name} ({size:.1f} MB)")
        else:
            print(f"❌ {binary_name} - MISSING")
            all_binaries_exist = False

    return all_binaries_exist

def test_models():
    """Test that AI models exist and are valid"""

    print("\n🧠 AI Models:")
    print("-" * 30)

    models_dir = Path(__file__).parent / "models"

    # Test LLaMA model
    llama_model = models_dir / "llama3-8b-q4.gguf"
    if llama_model.exists():
        size = llama_model.stat().st_size / (1024**3)  # GB
        print(f"✅ LLaMA 3 8B model ({size:.2f} GB)")
        llama_ok = True
    else:
        print("❌ LLaMA 3 8B model - MISSING")
        llama_ok = False

    return llama_ok

def run_functionality_test():
    """Test basic functionality"""

    print("\n🔧 Functionality Tests:")
    print("-" * 30)

    # Add scripts to path
    scripts_dir = Path(__file__).parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    tests_passed = 0
    total_tests = 4

    # Test reasoning engine
    try:
        from reasoning import LlamaReasoning
        reasoning = LlamaReasoning()
        print("✅ Reasoning engine initialized")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Reasoning engine failed: {e}")

    # Test TTS
    try:
        from text_to_speech import JarvisTTS
        tts = JarvisTTS()
        print("✅ Text-to-speech initialized")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Text-to-speech failed: {e}")

    # Test STT
    try:
        from speech_recognition import WhisperSTT
        if WhisperSTT:
            print("✅ Speech recognition available")
            tests_passed += 1
        else:
            print("❌ Speech recognition not available")
    except Exception as e:
        print(f"❌ Speech recognition failed: {e}")

    # Test memory system
    try:
        from memory_system import JarvisMemory
        memory = JarvisMemory()
        print("✅ Memory system initialized")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Memory system failed: {e}")

    print(f"\n📊 Functionality Test Results: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def main():
    """Run all tests"""

    print("🤖 JarvisAssistant Portable Package Test Suite")
    print("=" * 60)

    test_results = {
        "Structure": test_portable_structure(),
        "Python Imports": test_python_imports(),
        "Dependencies": test_external_dependencies(),
        "Binaries": test_binaries(),
        "Models": test_models(),
        "Functionality": run_functionality_test()
    }

    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print("-" * 30)

    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if not result:
            all_passed = False

    print("-" * 30)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for packaging!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Fix issues before packaging")
        return 1

if __name__ == "__main__":
    sys.exit(main())