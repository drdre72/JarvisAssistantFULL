#!/bin/zsh

# Full JARVIS Launch Script with Avatar Integration
# This script launches all JARVIS components including the new Flet UI and avatar video

echo "🤖 Initializing J.A.R.V.I.S. systems..."

# Set the project directory
PROJECT_DIR="/Users/andrebaker/Desktop/JarvisAssistant"
cd "$PROJECT_DIR"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Function to launch components in separate terminals
launch_in_terminal() {
    local title="$1"
    local command="$2"
    osascript -e "
    tell application \"Terminal\"
        do script \"cd '$PROJECT_DIR' && source venv/bin/activate && echo '🚀 Starting $title...' && $command\"
        set the name of front window to \"JARVIS - $title\"
    end tell"
}

# Note: JARVIS Avatar is now embedded in the Flet UI
echo "👁️ JARVIS Avatar will be embedded in the main interface..."

# Launch Voice Recognition Backend
echo "🎤 Starting Voice Recognition System..."
launch_in_terminal "Voice Backend" "python scripts/wake_listener.py"

# Small delay between launches
sleep 1

# Launch Flet UI
echo "💻 Starting JARVIS Interface..."
launch_in_terminal "Flet UI" "python jarvis_app.py"

echo ""
echo "✅ All JARVIS systems are initializing..."
echo "👁️ Avatar video: Embedded in main interface"
echo "🎤 Voice backend: Terminal window"
echo "💻 Main interface: Flet application"
echo ""
echo "🎯 Ready for activation with wake word or UI interaction"
echo "🔊 Say 'Jarvis' to begin voice interaction"
echo ""
echo "To stop all systems:"
echo "  - Close terminal windows"
echo "  - Close Flet app"

# Optional: Wait for user input before exiting this script
echo "Press any key to continue..."
read -n 1 -s 