"""
main.py - JarvisAssistant Portable Windows Edition
Main launcher for the complete portable package
"""

import sys
import os
import time
from pathlib import Path

def setup_portable_environment():
    """Setup the portable application environment"""

    # Determine if running as PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller executable
        application_path = Path(sys._MEIPASS)
        base_path = Path(sys.executable).parent
    else:
        # Running as script
        application_path = Path(__file__).parent
        base_path = application_path

    # Add scripts directory to Python path
    scripts_dir = application_path / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    # Set environment variables for portable mode
    os.environ['JARVIS_BASE_PATH'] = str(base_path)
    os.environ['JARVIS_APP_PATH'] = str(application_path)

    return base_path, application_path

def check_dependencies():
    """Check if all required dependencies are available"""

    print("[Main] Checking dependencies...")

    required_modules = [
        'flet', 'psutil', 'faster_whisper', 'pyttsx3', 'pyaudio'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"[Main] ERROR: Missing required modules: {missing_modules}")
        print("[Main] Please install missing dependencies:")
        print(f"[Main] pip install {' '.join(missing_modules)}")
        return False

    print("[Main] All dependencies available")
    return True

def check_assets():
    """Check if required assets are available"""

    print("[Main] Checking assets...")

    base_path = Path(os.environ.get('JARVIS_BASE_PATH', '.'))

    required_assets = [
        "bin/llama-cli.exe",
        "models/llama3-8b-q4.gguf"
    ]

    missing_assets = []
    for asset in required_assets:
        asset_path = base_path / asset
        if not asset_path.exists():
            missing_assets.append(asset)

    if missing_assets:
        print(f"[Main] ERROR: Missing required assets: {missing_assets}")
        return False

    print("[Main] All assets available")
    return True

def main():
    """Main entry point for JarvisAssistant"""

    print("=" * 60)
    print("  JarvisAssistant - Windows Portable Edition")
    print("     Version 1.0 - Offline AI Assistant")
    print("=" * 60)
    print()

    try:
        # Setup portable environment
        base_path, app_path = setup_portable_environment()
        print(f"[Main] Base path: {base_path}")
        print(f"[Main] App path: {app_path}")

        # Check dependencies
        if not check_dependencies():
            input("Press Enter to exit...")
            return 1

        # Check assets
        if not check_assets():
            input("Press Enter to exit...")
            return 1

        print("[Main] Initializing JarvisAssistant...")
        print("[Main] Loading AI models (this may take a moment)...")

        # Import the main application
        try:
            import flet as ft
            from jarvis_app import JarvisApp

            def app_main(page: ft.Page):
                app = JarvisApp(page)

            print("[Main] Starting user interface...")
            ft.app(target=app_main, port=0)

        except ImportError as e:
            print(f"[Main] ERROR: Failed to import application modules: {e}")
            print("[Main] This may indicate a packaging issue.")
            input("Press Enter to exit...")
            return 1

    except KeyboardInterrupt:
        print("\n[Main] Shutdown requested by user")
        return 0

    except Exception as e:
        print(f"\n[Main] FATAL ERROR: {e}")
        print("[Main] Please check the logs for more details.")
        input("Press Enter to exit...")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())