#!/bin/zsh

# --- TEMPORARY DEBUGGING VERSION ---
# This script will ONLY launch the UI to isolate the launch issue.

echo "[DEBUG] Launching Jarvis UI in isolation..."
cd /Users/andrebaker/Desktop/JarvisAssistant/JarvisUI
npm install
npm run dev
