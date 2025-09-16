import sys
import os
from Cocoa import NSApplication, NSWindow, NSBackingStoreBuffered, NSRect, NSPoint, NSSize
from AVKit import AVPlayerView
from AVFoundation import AVPlayer, NSURL, AVPlayerItem
from Foundation import NSNotificationCenter, NSObject

VIDEO_PATH = "/Users/andrebaker/Desktop/JarvisAssistant/public/Standard_Mode_Jarvis_Interface__Phase1__Assemb.mp4"

def main():
    # Check if video file exists
    if not os.path.exists(VIDEO_PATH):
        print(f"Video file not found: {VIDEO_PATH}")
        return
    
    app = NSApplication.sharedApplication()
    
    # Create window
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSRect(NSPoint(100, 100), NSSize(800, 600)),
        15,  # Titled, closable, resizable
        NSBackingStoreBuffered,
        False
    )
    window.setTitle_("JARVIS Avatar")
    window.setLevel_(3)  # Always on top
    
    # Create player view
    player_view = AVPlayerView.alloc().initWithFrame_(window.contentView().frame())
    
    # Create player with URL
    url = NSURL.fileURLWithPath_(VIDEO_PATH)
    player = AVPlayer.playerWithURL_(url)
    player_view.setPlayer_(player)
    
    # Add player view to window
    window.contentView().addSubview_(player_view)
    window.makeKeyAndOrderFront_(None)
    
    # Simple loop observer class
    class VideoLooper(NSObject):
        def playerDidFinishPlaying_(self, notification):
            player.seekToTime_(0)
            player.play()
    
    # Set up looping
    looper = VideoLooper.alloc().init()
    NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
        looper, 
        "playerDidFinishPlaying:",
        "AVPlayerItemDidPlayToEndTimeNotification", 
        player.currentItem()
    )
    
    # Start playing
    player.play()
    
    print("JARVIS Avatar window opened. Close the window to exit.")
    app.run()

if __name__ == "__main__":
    main() 