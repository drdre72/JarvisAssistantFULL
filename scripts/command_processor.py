import sys
import os
import json
import argparse

# --- ROBUST PATHING SETUP ---
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Now that the path is set, we can import our local modules
from jarvis_commands import commands
from speaker import speak

def main():
    """
    Parses command-line arguments and executes a single Jarvis command.
    """
    parser = argparse.ArgumentParser(description="Process a single Jarvis command from an external source.")
    parser.add_argument("--command", required=True, help="The name of the command to execute from the commands dictionary.")
    parser.add_argument("--args", default="{}", help="A JSON string representing the arguments dictionary for the command.")
    
    args = parser.parse_args()
    
    command_name = args.command
    try:
        command_args = json.loads(args.args)
    except json.JSONDecodeError:
        error_msg = f"Error: Invalid JSON format for arguments: {args.args}"
        print(error_msg)
        # Speaking the error might not be desirable for UI-initiated commands.
        # For now, we'll just print it.
        return

    if command_name in commands:
        print(f"[CommandProcessor] Executing command '{command_name}' with args: {command_args}")
        command_function = commands[command_name]
        result = command_function(command_args)
        speak(result)
    else:
        error_msg = f"Sorry, the command '{command_name}' was not recognized."
        print(error_msg)
        speak(error_msg)

if __name__ == "__main__":
    main() 