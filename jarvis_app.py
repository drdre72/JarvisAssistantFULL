import flet as ft
import subprocess
import psutil
import asyncio
import threading
import json
import os
import sys
import time
from datetime import datetime

# Add the scripts directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(script_dir, "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

# Import JARVIS modules
try:
    from jarvis_commands import commands, listen_for_input_vad
    from speaker import speak
    from dispatcher import process as process_command
    from command_processor import main as execute_command
except ImportError as e:
    print(f"Warning: Could not import JARVIS modules: {e}")
    # Create dummy functions for testing
    def speak(text): print(f"JARVIS: {text}")
    def listen_for_input_vad(has_spoken_before=False): return ""
    def process_command(text): return "CONTINUE_LOOP"
    commands = {}

# Import flet-video for proper video support
try:
    from flet_video import Video, VideoMedia, PlaylistMode
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    print("flet-video not available, using placeholder")

# Define color constants
ORANGE = "#ff6b35"
WHITE = "#ffffff"
WHITE70 = "#b3b3b3"
BLACK = "#0a0a0a"

class JarvisApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.is_listening = False
        self.avatar_playing = False
        self.voice_thread = None
        self.system_monitor_thread = None
        self.should_monitor = True
        self.voice_button = None
        
        # Initialize audio and system monitoring
        self.setup_page()
        self.create_ui()
        self.start_system_monitoring()
        
        # Play startup sequence
        self.startup_sequence()

    def startup_sequence(self):
        """Display welcome message and auto-start voice mode"""
        # Add welcome message to chat
        self.add_chat_message("Jarvis", "Good day, sir. J.A.R.V.I.S. systems are online and ready for your commands.", True)
        speak("Good day, sir. J.A.R.V.I.S. systems are online and ready for your commands.")
        
        # Auto-start voice recognition after greeting
        def delayed_voice_start():
            import time
            time.sleep(3)  # Wait for greeting to finish
            if hasattr(self, 'page'):
                self.start_voice_recognition()
                speak("Awaiting orders, sir.")
        
        threading.Thread(target=delayed_voice_start, daemon=True).start()

    def start_system_monitoring(self):
        """Start real-time system monitoring"""
        def monitor_system():
            while self.should_monitor:
                try:
                    # Update system stats
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    try:
                        battery = psutil.sensors_battery()
                        battery_percent = int(battery.percent) if battery else 100
                    except:
                        battery_percent = 100
                    
                    # Update UI
                    if hasattr(self, 'cpu_text'):
                        self.cpu_text.value = f"CPU: {cpu_percent:.1f}%"
                        self.memory_text.value = f"Memory: {memory.percent:.1f}%"
                        self.battery_text.value = f"Battery: {battery_percent}%"
                        
                        # Update status indicator color based on system health
                        if cpu_percent > 80 or memory.percent > 90:
                            self.status_indicator.color = "#ff4444"  # Red for high usage
                        elif cpu_percent > 60 or memory.percent > 70:
                            self.status_indicator.color = "#ffaa00"  # Orange for medium usage
                        else:
                            self.status_indicator.color = ORANGE  # Green for normal
                        
                        self.page.update()
                except Exception as e:
                    print(f"System monitoring error: {e}")
                
                time.sleep(2)
        
        self.system_monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        self.system_monitor_thread.start()

    def setup_page(self):
        """Configure the main application window"""
        self.page.title = "J.A.R.V.I.S. - Just A Rather Very Intelligent System"
        self.page.bgcolor = BLACK
        self.page.padding = 0
        self.page.spacing = 0
        
        # Set window to fullscreen for optimal JARVIS experience
        self.page.window.maximized = True
        self.page.window.always_on_top = True  # Keep JARVIS on top
        self.page.window.full_screen = True
        
        # Fallback window size if fullscreen doesn't work
        self.page.window.width = 1920
        self.page.window.height = 1080
        
        # Configure color scheme
        self.page.theme = ft.Theme(
            color_scheme_seed=ORANGE,
            color_scheme=ft.ColorScheme(
                primary=ORANGE,
                on_primary=BLACK,
                surface=BLACK,
                on_surface=WHITE,
                background=BLACK,
                on_background=WHITE,
            ),
        )

    def create_animated_jarvis_avatar(self):
        """Create an animated JARVIS avatar placeholder"""
        return ft.Container(
            content=ft.Stack([
                # Outer ring animation placeholder
                ft.Container(
                    width=140,
                    height=140,
                    border_radius=70,
                    border=ft.border.all(2, ORANGE),
                    bgcolor="transparent",
                ),
                # Inner content
                ft.Container(
                    content=ft.Column([
                        ft.Icon(
                            "smart_toy",
                            size=50,
                            color=ORANGE,
                        ),
                        ft.Text(
                            "J.A.R.V.I.S.",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ORANGE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "ONLINE",
                            size=8,
                            color="#4a9eff",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                    width=130,
                    height=130,
                    border_radius=65,
                    bgcolor="#1a1a1a",
                    padding=10,
                    margin=5,
                ),
            ]),
            width=150,
            height=150,
        )
    
    def create_ui(self):
        """Create the main user interface"""
        # Header with title and status
        header = self.create_header()
        
        # Main content area
        main_content = self.create_main_content()
        
        # Sidebar with controls
        sidebar = self.create_sidebar()
        
        # Layout
        layout = ft.Row(
            [
                ft.Container(
                    content=sidebar,
                    width=250,
                    bgcolor="#111111",
                    padding=10,
                    border_radius=10,
                ),
                ft.Container(
                    content=ft.Column([header, main_content]),
                    expand=True,
                    padding=10,
                )
            ],
            expand=True,
        )
        
        self.page.add(layout)
        self.page.update()
    
    def create_header(self):
        """Create the header section"""
        self.status_indicator = ft.Icon(
            "circle",
            color=ORANGE,
            size=12,
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Text(
                    "J.A.R.V.I.S.",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ORANGE,
                ),
                ft.Row([
                    self.status_indicator,
                    ft.Text("System Status", size=14, color=WHITE70),
                ]),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=20),
        )
    
    def create_sidebar(self):
        """Create the left sidebar with system monitor and quick actions"""
        # Real system monitor section
        self.cpu_text = ft.Text("CPU: 0.0%", size=14, color=WHITE70)
        self.memory_text = ft.Text("Memory: 0.0%", size=14, color=WHITE70)
        self.battery_text = ft.Text("Battery: 100%", size=14, color=WHITE70)
        
        system_monitor = ft.Container(
            content=ft.Column([
                ft.Text("System Monitor", size=16, weight=ft.FontWeight.BOLD, color="#4a9eff"),
                ft.Divider(height=1, color="#333333"),
                self.cpu_text,
                self.memory_text,
                self.battery_text,
            ], spacing=10),
            bgcolor="#1a1a1a",
            border_radius=10,
            border=ft.border.all(1, "#333333"),
            padding=20,
        )
        
        # Functional Quick Actions
        # Create the voice button first, assign to self
        self.voice_button = ft.ElevatedButton(
            "Voice Mode",
            icon="mic" if not self.is_listening else "mic_off",
            bgcolor="#2a2a2a" if not self.is_listening else ORANGE,
            color=ORANGE if not self.is_listening else WHITE,
            on_click=self.toggle_voice_mode,
        )

        quick_actions = ft.Container(
            content=ft.Column([
                ft.Text("Quick Actions", size=16, weight=ft.FontWeight.BOLD, color="#4a9eff"),
                ft.Divider(height=1, color="#333333"),
                ft.ElevatedButton(
                    "Open Terminal",
                    icon="terminal",
                    bgcolor="#2a2a2a",
                    color=ORANGE,
                    on_click=self.open_terminal,
                ),
                ft.ElevatedButton(
                    "Take Screenshot",
                    icon="camera_alt",
                    bgcolor="#2a2a2a",
                    color=ORANGE,
                    on_click=self.take_screenshot_action,
                ),
                ft.ElevatedButton(
                    "System Info",
                    icon="info",
                    bgcolor="#2a2a2a",
                    color=ORANGE,
                    on_click=self.show_system_info,
                ),
                self.voice_button,  # Just reference here
                ft.ElevatedButton(
                    "JARVIS Avatar",
                    icon="play_circle" if not self.avatar_playing else "stop_circle",
                    bgcolor=ORANGE if self.avatar_playing else "#2a2a2a",
                    color=WHITE if self.avatar_playing else ORANGE,
                    on_click=self.toggle_avatar_video,
                ),
            ], spacing=10),
            bgcolor="#1a1a1a",
            border_radius=10,
            border=ft.border.all(1, "#333333"),
            padding=20,
        )
        
        return ft.Column([
            system_monitor,
            quick_actions,
        ], spacing=20)

    def create_main_content(self):
        """Create the main content area with time, JARVIS avatar, chat, and visualizations"""
        # Time display
        self.time_display = ft.Text(
            self.get_current_time(),
            size=48,
            weight=ft.FontWeight.BOLD,
            color=WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.date_display = ft.Text(
            self.get_current_date(),
            size=18,
            color=WHITE70,
            text_align=ft.TextAlign.CENTER,
        )
        
        # JARVIS Avatar positioned in center, slightly underneath time
        video_failed = False
        if VIDEO_AVAILABLE:
            # Use actual video with looping - simplified approach
            try:
                video_path = os.path.join(script_dir, "public", "Standard_Mode_Jarvis_Interface__Phase1__Assemb.mp4")
                self.jarvis_avatar = ft.Container(
                    content=Video(
                        playlist=[VideoMedia(resource=video_path)],
                        playlist_mode=PlaylistMode.LOOP,
                        autoplay=True,
                        muted=True,
                        show_controls=False,
                    ),
                    width=260,  # 200 * 1.3 = 260
                    height=260,  # 200 * 1.3 = 260
                    border_radius=130,  # Make it circular (260/2)
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    border=ft.border.all(3, ORANGE),
                    bgcolor="#1a1a1a",
                )
                print("✅ Video component created successfully")
            except Exception as e:
                print(f"❌ Video error: {e}")
                # Set flag to use placeholder if video fails
                video_failed = True
        
        if not VIDEO_AVAILABLE or video_failed:
            # Enhanced animated JARVIS avatar
            self.jarvis_avatar = self.create_animated_jarvis_avatar()
        
        # Chat area
        self.chat_container = ft.ListView(
            height=300,
            spacing=10,
            padding=10,
        )
        
        chat_area = ft.Container(
            content=self.chat_container,
            bgcolor="#1a1a1a",
            border_radius=10,
            border=ft.border.all(1, "#333333"),
            padding=10,
        )
        
        # Chat input
        self.chat_input = ft.TextField(
            hint_text="What can I help you with, sir?",
            border_color=ORANGE,
            focused_border_color=ORANGE,
            cursor_color=ORANGE,
            expand=True,
            on_submit=self.on_chat_submit,
        )
        
        chat_input_row = ft.Row([
            self.chat_input,
            ft.IconButton(
                icon="send",
                icon_color=ORANGE,
                on_click=self.on_chat_submit,
            )
        ])
        
        # Create main content area with JARVIS positioned to the right
        main_content = ft.Column([
            ft.Container(
                content=ft.Column([
                    self.time_display,
                    self.date_display,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.only(bottom=10),
            ),
            ft.Text("Command Center", size=20, weight=ft.FontWeight.BOLD),
            chat_area,
            chat_input_row,
        ])
        
        # Position JARVIS avatar to the right of main content
        return ft.Row([
            ft.Container(
                content=main_content,
                expand=True,
            ),
            ft.Container(
                content=self.jarvis_avatar,
                alignment=ft.alignment.center,
                padding=ft.padding.only(left=20, right=20),
                width=300,  # Fixed width for JARVIS area
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    def get_current_time(self):
        """Get formatted current time"""
        return datetime.now().strftime("%I:%M %p")
    
    def get_current_date(self):
        """Get formatted current date"""
        return datetime.now().strftime("%A, %B %d, %Y")
    
    def add_chat_message(self, role, message, is_jarvis=False):
        """Add a message to the chat"""
        color = ORANGE if role == "user" else "#4a9eff"
        label = "User" if role == "user" else "Jarvis"
        
        message_container = ft.Container(
            content=ft.Column([
                ft.Text(f"{label}:", size=12, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(message, size=14, color=WHITE),
            ]),
            bgcolor="#2a2a2a" if role == "assistant" else "#333333",
            border_radius=10,
            padding=10,
            margin=ft.margin.only(bottom=5),
        )
        
        self.chat_container.controls.append(message_container)
        self.page.update()
        
        # Auto-scroll to bottom
        self.chat_container.scroll_to(offset=-1)
    
    def on_chat_submit(self, e):
        """Handle chat input submission"""
        user_input = self.chat_input.value.strip()
        if not user_input:
            return
            
        # Clear input and add user message
        self.chat_input.value = ""
        self.page.update()
        
        self.add_chat_message("You", user_input)
        
        # Process command through JARVIS system
        self.process_user_command(user_input)
    
    def process_user_command(self, user_input):
        """Process user command through JARVIS system"""
        try:
            # Check for direct commands first
            if user_input.lower() in ["exit", "quit", "goodbye"]:
                self.add_chat_message("Jarvis", "Goodbye, sir. JARVIS systems standing by.", True)
                speak("Goodbye, sir. JARVIS systems standing by.")
                return
            
            # Check for conversation mode trigger
            if "speak freely" in user_input.lower() or "conversation" in user_input.lower():
                self.add_chat_message("Jarvis", "Of course, sir. I am here to assist.", True)
                speak("Of course, sir. I am here to assist.")
                return
            
            # Use JARVIS dispatcher to process command
            result = process_command(user_input)
            
            # If no specific command found, use conversation mode
            if result == 'CONTINUE_LOOP':
                # Send to conversation AI
                try:
                    import ollama
                    client = ollama.Client()
                    
                    response = client.chat(
                        model='llama3:8b',
                        messages=[
                            {'role': 'system', 'content': self.create_jarvis_persona_prompt()},
                            {'role': 'user', 'content': user_input}
                        ]
                    )
                    
                    assistant_response = response['message']['content']
                    self.add_chat_message("Jarvis", assistant_response, True)
                    speak(assistant_response)
                    
                except Exception as e:
                    print(f"Conversation AI error: {e}")
                    self.add_chat_message("Jarvis", "I'm sorry, I'm having trouble with my reasoning module.", True)
                    speak("I'm sorry, I'm having trouble with my reasoning module.")
            
        except Exception as e:
            print(f"Command processing error: {e}")
            self.add_chat_message("Jarvis", "I encountered an error processing that command, sir.", True)
            speak("I encountered an error processing that command.")

    def create_jarvis_persona_prompt(self):
        """Create the JARVIS persona prompt for conversation mode"""
        return """You are JARVIS (Just A Rather Very Intelligent System), Tony Stark's AI assistant. 
        You are sophisticated, polite, and efficient. You address the user as "sir" and maintain a professional yet friendly demeanor.
        You are helpful, intelligent, and have a slight sense of humor when appropriate.
        Keep responses concise but informative. You are currently running on the user's desktop system."""

    # Quick Action Functions
    def open_terminal(self, e):
        """Open Terminal application"""
        try:
            subprocess.Popen(["open", "-a", "Terminal"])
            self.add_chat_message("Jarvis", "Opening Terminal for you, sir.", True)
            speak("Opening Terminal for you, sir.")
        except Exception as error:
            self.add_chat_message("Jarvis", "I'm sorry, I couldn't open Terminal.", True)

    def take_screenshot_action(self, e):
        """Execute screenshot command"""
        try:
            from jarvis_commands import take_screenshot
            result = take_screenshot({})
            self.add_chat_message("Jarvis", result, True)
        except Exception as error:
            self.add_chat_message("Jarvis", "I'm sorry, I couldn't take a screenshot.", True)

    def show_system_info(self, e):
        """Display detailed system information"""
        try:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info = f"System Information:\n"
            info += f"• CPU Cores: {cpu_count}\n"
            info += f"• Total Memory: {memory.total // (1024**3)} GB\n"
            info += f"• Available Memory: {memory.available // (1024**3)} GB\n"
            info += f"• Disk Usage: {disk.percent:.1f}%"
            
            self.add_chat_message("Jarvis", info, True)
            speak("System information displayed, sir.")
        except Exception as error:
            self.add_chat_message("Jarvis", "I'm sorry, I couldn't retrieve system information.", True)

    def toggle_voice_mode(self, e):
        """Toggle voice recognition mode"""
        if not self.is_listening:
            self.start_voice_recognition()
        else:
            self.stop_voice_recognition()
        
        # Update button appearance
        voice_button = e.control
        voice_button.icon = "mic" if self.is_listening else "mic_off"
        voice_button.bgcolor = ORANGE if self.is_listening else "#2a2a2a"
        voice_button.color = WHITE if self.is_listening else ORANGE
        self.page.update()

    def start_voice_recognition(self):
        """Start listening for voice commands"""
        self.is_listening = True
        self.add_chat_message("Jarvis", "Voice recognition activated. I'm listening, sir.", True)
        speak("Voice recognition activated. I'm listening.")
        
        def voice_loop():
            has_spoken_before = False  # Track if user has spoken in this session
            
            while self.is_listening:
                try:
                    user_input = listen_for_input_vad(has_spoken_before)
                    if user_input == "TIMEOUT":
                        # After one timeout, go back to sleep
                        print("[Voice] Timeout detected, going back to sleep")
                        self.is_listening = False
                        self.add_chat_message("Jarvis", "Going back to sleep, sir. Say 'Jarvis' to wake me.", True)
                        speak("Going back to sleep, sir. Say 'Jarvis' to wake me.")
                        break
                    elif user_input and user_input.strip() and self.is_listening:
                        # User has spoken - set flag for tighter timeout
                        has_spoken_before = True
                        
                        # Add user input to chat first
                        self.add_chat_message("User", user_input)
                        self.page.update()  # Force UI update
                        # Then process the command
                        self.process_user_command(user_input)
                except Exception as e:
                    print(f"Voice recognition error: {e}")
                    break
        
        self.voice_thread = threading.Thread(target=voice_loop, daemon=True)
        self.voice_thread.start()

    def stop_voice_recognition(self):
        """Stop voice recognition"""
        self.is_listening = False
        self.add_chat_message("Jarvis", "Voice recognition deactivated, sir.", True)
        speak("Voice recognition deactivated.")

    def toggle_avatar_video(self, e):
        """Toggle JARVIS avatar video playback"""
        if not self.avatar_playing:
            self.start_avatar_video()
        else:
            self.stop_avatar_video()
        
        # Update button appearance
        avatar_button = e.control
        avatar_button.icon = "stop_circle" if self.avatar_playing else "play_circle"
        avatar_button.bgcolor = ORANGE if self.avatar_playing else "#2a2a2a"
        avatar_button.color = WHITE if self.avatar_playing else ORANGE
        self.page.update()

    def start_avatar_video(self):
        """Start JARVIS avatar video using AppleScript"""
        try:
            from jarvis_avatar_applescript import play_jarvis_avatar
            success = play_jarvis_avatar()
            if success:
                self.avatar_playing = True
                self.add_chat_message("Jarvis", "Avatar video activated, sir.", True)
                speak("Avatar video activated.")
            else:
                self.add_chat_message("Jarvis", "I'm sorry, I couldn't start the avatar video.", True)
        except Exception as e:
            print(f"Error starting avatar video: {e}")
            self.add_chat_message("Jarvis", "Avatar video system encountered an error.", True)

    def stop_avatar_video(self):
        """Stop JARVIS avatar video"""
        try:
            from jarvis_avatar_applescript import stop_jarvis_avatar
            success = stop_jarvis_avatar()
            if success:
                self.avatar_playing = False
                self.add_chat_message("Jarvis", "Avatar video deactivated, sir.", True)
                speak("Avatar video deactivated.")
        except Exception as e:
            print(f"Error stopping avatar video: {e}")

    def update_system_stats(self):
        """Update system statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Battery info (if available)
            battery = psutil.sensors_battery()
            battery_percent = f"{battery.percent}%" if battery else "N/A"
            
            self.system_stats = {
                "cpu": cpu_percent,
                "memory": memory_percent,
                "battery": battery_percent
            }
            
            # Update UI
            if self.cpu_display:
                self.cpu_display.value = f"CPU: {cpu_percent:.1f}%"
                self.memory_display.value = f"Memory: {memory_percent:.1f}%"
                self.battery_display.value = f"Battery: {battery_percent}"
                self.page.update()
                
        except Exception as e:
            print(f"Error updating system stats: {e}")
    
    def update_time_display(self):
        """Update time and date displays"""
        if hasattr(self, 'time_display'):
            self.time_display.value = self.get_current_time()
            self.date_display.value = self.get_current_date()
            self.page.update()
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        self.running = True
        
        def stats_worker():
            while self.running:
                self.update_system_stats()
                time.sleep(2)
        
        def time_worker():
            while self.running:
                self.update_time_display()
                time.sleep(1)
        
        threading.Thread(target=stats_worker, daemon=True).start()
        threading.Thread(target=time_worker, daemon=True).start()
        
        # Initial welcome message
        self.add_chat_message("assistant", "Good day, sir. J.A.R.V.I.S. systems are online and ready for your commands.")

    def cleanup(self):
        """Clean up resources when app closes"""
        self.should_monitor = False
        self.is_listening = False

def main(page: ft.Page):
    """Main application entry point"""
    app = JarvisApp(page)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="public")