#!/usr/bin/env python3
import subprocess
import os

VIDEO_PATH = "/Users/andrebaker/Desktop/JarvisAssistant/public/Standard_Mode_Jarvis_Interface__Phase1__Assemb.mp4"

def play_jarvis_avatar():
    """Play JARVIS avatar video using QuickTime Player via AppleScript"""
    
    # Check if video file exists
    if not os.path.exists(VIDEO_PATH):
        print(f"Video file not found: {VIDEO_PATH}")
        return False
    
    applescript = f'''
    tell application "QuickTime Player"
        activate
        open POSIX file "{VIDEO_PATH}"
        tell front document
            set looping to true
            set muted to true
            play
        end tell
        
        -- Position window (optional)
        tell front window
            set bounds to {{100, 100, 900, 700}}
        end tell
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, check=True)
        print("✅ JARVIS Avatar video started in QuickTime Player")
        print("📺 Video will loop continuously")
        print("🚪 Close QuickTime Player to stop the video")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running AppleScript: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ osascript command not found. Are you on macOS?")
        return False

def stop_jarvis_avatar():
    """Stop JARVIS avatar video by quitting QuickTime Player"""
    applescript = '''
    tell application "QuickTime Player"
        quit
    end tell
    '''
    
    try:
        subprocess.run(['osascript', '-e', applescript], 
                      capture_output=True, text=True, check=True)
        print("🛑 JARVIS Avatar video stopped")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error stopping video: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Starting JARVIS Avatar...")
    success = play_jarvis_avatar()
    
    if success:
        print("\n💡 To stop the video, run:")
        print("   python jarvis_avatar_applescript.py stop")
        print("   or just close QuickTime Player")
    else:
        print("❌ Failed to start JARVIS Avatar video") 