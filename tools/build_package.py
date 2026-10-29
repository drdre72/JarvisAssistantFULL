"""
build_package.py - PyInstaller packaging script for JarvisAssistant
Creates a portable Windows executable with all dependencies bundled
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build_jarvis_package():
    """Build the complete JarvisAssistant portable package"""

    print("=" * 60)
    print("JarvisAssistant Portable Package Builder")
    print("Building Windows executable with PyInstaller...")
    print("=" * 60)

    # Get current directory
    base_dir = PROJECT_ROOT

    # Create build configuration
    main_script = base_dir / "main.py"
    if not main_script.exists():
        print("❌ Error: main.py not found")
        return False

    # PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=JarvisAssistant",
        "--onefile",
        "--windowed",
        "--icon=ui/assets/jarvis_icon.ico" if (base_dir / "ui/assets/jarvis_icon.ico").exists() else None,

        # Add data files
        "--add-data=bin;bin",
        "--add-data=models;models",
        "--add-data=scripts;scripts",
        "--add-data=ui;ui",

        # Hidden imports for dynamic modules
        "--hidden-import=faster_whisper",
        "--hidden-import=pyttsx3",
        "--hidden-import=flet",
        "--hidden-import=psutil",
        "--hidden-import=pyaudio",

        # Windows specific
        "--console",  # Keep console for debugging

        str(main_script)
    ]

    # Remove None values
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg is not None]

    print("Running PyInstaller...")
    print(f"Command: {' '.join(pyinstaller_cmd)}")

    try:
        result = subprocess.run(pyinstaller_cmd, check=True, cwd=base_dir)
        print("✅ PyInstaller completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found. Install with: pip install pyinstaller")
        return False

    # Check if build was successful
    dist_dir = base_dir / "dist"
    jarvis_exe = dist_dir / "JarvisAssistant.exe"

    if jarvis_exe.exists():
        print(f"✅ Successfully built: {jarvis_exe}")
        print(f"📦 Package size: {jarvis_exe.stat().st_size / (1024*1024*1024):.2f} GB")

        # Create final distribution folder
        final_dist = base_dir / "JarvisAssistant_Portable"
        if final_dist.exists():
            shutil.rmtree(final_dist)
        final_dist.mkdir()

        # Copy executable
        shutil.copy2(jarvis_exe, final_dist / "JarvisAssistant.exe")

        # Copy additional files
        additional_files = [
            "README.md",
            "requirements.txt",
            "progress.txt"
        ]

        for file_name in additional_files:
            src = base_dir / file_name
            if src.exists():
                shutil.copy2(src, final_dist / file_name)

        # Create batch launcher
        batch_launcher = final_dist / "Launch_Jarvis.bat"
        with open(batch_launcher, 'w') as f:
            f.write("""@echo off
echo Starting JarvisAssistant...
echo Please wait while the AI models load...
echo.
JarvisAssistant.exe
pause
""")

        print(f"✅ Final package created in: {final_dist}")
        print("📋 Package contents:")
        for item in final_dist.iterdir():
            size = item.stat().st_size / (1024*1024) if item.is_file() else 0
            print(f"   - {item.name} ({size:.1f} MB)")

        return True
    else:
        print("❌ Build failed - executable not found")
        return False

def create_spec_file():
    """Create a PyInstaller spec file for advanced configuration"""

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Analysis of the main script
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('bin', 'bin'),
        ('models', 'models'),
        ('scripts', 'scripts'),
        ('ui', 'ui'),
    ],
    hiddenimports=[
        'faster_whisper',
        'pyttsx3',
        'flet',
        'psutil',
        'pyaudio',
        'numpy',
        'pathlib',
        'threading',
        'subprocess',
        'json',
        'wave',
        'tempfile'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JarvisAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Change to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ui/assets/jarvis_icon.ico'  # Add icon if available
)
'''

    with open(PROJECT_ROOT / "JarvisAssistant.spec", 'w') as f:
        f.write(spec_content)

    print("✅ PyInstaller spec file created: JarvisAssistant.spec")
    print("   You can now run: pyinstaller JarvisAssistant.spec")

def install_build_dependencies():
    """Install required dependencies for building"""

    dependencies = [
        "pyinstaller>=5.0",
        "auto-py-to-exe",  # Optional GUI for PyInstaller
    ]

    print("Installing build dependencies...")
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")

def check_package_size():
    """Check the size of various components"""

    base_dir = PROJECT_ROOT

    print("\n📊 Package Size Analysis:")
    print("-" * 40)

    components = {
        "Local LLM": base_dir / "models" / "qwen2.5-7b-instruct-q4_k_m.gguf",
        "Binaries": base_dir / "bin",
        "Scripts": base_dir / "scripts",
        "UI Assets": base_dir / "ui"
    }

    total_size = 0

    for name, path in components.items():
        if path.exists():
            if path.is_file():
                size = path.stat().st_size
            else:
                size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

            size_gb = size / (1024**3)
            total_size += size
            print(f"{name:15} {size_gb:8.2f} GB")

    print("-" * 40)
    print(f"{'Total Estimated':15} {total_size/(1024**3):8.2f} GB")

    if total_size > 10 * (1024**3):  # 10GB
        print("⚠️  Warning: Package will be very large (>10GB)")
        print("   Consider using smaller models for distribution")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JarvisAssistant Package Builder")
    parser.add_argument("--install-deps", action="store_true", help="Install build dependencies")
    parser.add_argument("--create-spec", action="store_true", help="Create PyInstaller spec file")
    parser.add_argument("--check-size", action="store_true", help="Check package component sizes")
    parser.add_argument("--build", action="store_true", help="Build the package")

    args = parser.parse_args()

    if args.install_deps:
        install_build_dependencies()
    elif args.create_spec:
        create_spec_file()
    elif args.check_size:
        check_package_size()
    elif args.build:
        build_jarvis_package()
    else:
        # Default: run size check and build
        check_package_size()
        print("\n" + "="*60)
        if input("Proceed with build? (y/N): ").lower() == 'y':
            build_jarvis_package()
        else:
            print("Build cancelled.")