# dispatcher.py
import sys
import os
import json

# --- ROBUST PATHING SETUP ---
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# --- LOCAL MODULE IMPORTS ---
from jarvis_commands import commands
from speaker import speak
from reasoning import get_reasoning_engine

# --- INITIALIZE THE REASONING ENGINE ---
try:
    reasoning_engine = get_reasoning_engine()
    print("[Dispatcher] LLaMA reasoning engine initialized successfully.")
except Exception as e:
    print(f"[Dispatcher] FATAL: Could not initialize reasoning engine. Error: {e}")
    sys.exit(1)

def create_system_prompt():
    """Creates a detailed system prompt to instruct the LLM on its task."""
    available_commands = list(commands.keys())
    
    json_format = """
    {
      "intent": "command_name",
      "entities": {
        "argument_name": "value"
      }
    }
    """

    prompt = f"""
    You are the central dispatcher for a voice assistant named Jarvis. Your primary function is to analyze transcribed user text and convert it into a structured JSON command.

    1.  **Identify Intent:** Determine the user's command from the list of available commands: {available_commands}.
    2.  **Extract Entities:** Identify any arguments or entities required for the command.
    3.  **Handle Ambiguity:** If the user's request is vague, choose the 'unrecognized' intent.
    4.  **Strict JSON Output:** You MUST respond ONLY with a single, valid JSON object in the following format. Do not add any explanatory text before or after the JSON.
        {json_format}
    5.  **Unrecognized Commands:** If the text does not match any command, return the intent as "unrecognized".
    
    ### Special Instructions for Commands:
    - For the **"write this down"** command, capture all the text that comes after the phrase "write this down" and place it into a single entity called **"content"**.
    - For example, if the user says "write this down a b", the output must be: {{"intent": "write this down", "entities": {{"content": "a b"}}}}

    Analyze the user's text and provide the corresponding JSON command.
    """
    return prompt.strip()

def simple_command_check(text: str):
    """Check for simple commands without using LLM"""
    text_lower = text.lower()

    # Simple greeting responses
    if any(word in text_lower for word in ['hello', 'hi', 'hey', 'jarvis']):
        speak("Hello, sir. How may I assist you?")
        return True

    # Capability questions (check first for priority)
    if any(phrase in text_lower for phrase in ['capabilities', 'what can you do', 'your abilities', 'system capabilities']):
        speak("I can assist with voice commands, system monitoring, basic queries, and simple conversations, sir. My advanced reasoning is currently optimized for speed.")
        return True

    # Identity/name questions
    if any(phrase in text_lower for phrase in ['what is your name', 'who are you', 'your name', 'what are you']):
        speak("I am JARVIS, your personal AI assistant, sir.")
        return True

    # Status check responses
    if any(phrase in text_lower for phrase in ['how are you', 'status', 'online', 'working', 'functioning']):
        speak("All systems operational, sir. I'm functioning normally.")
        return True

    # Reasoning/model questions
    if any(phrase in text_lower for phrase in ['reasoning', 'model', 'thinking', 'brain']):
        speak("My reasoning systems are online but running at reduced capacity to ensure responsiveness, sir.")
        return True

    # Can you hear me
    if any(phrase in text_lower for phrase in ['can you hear', 'hear me', 'listening']):
        speak("Yes sir, I can hear you clearly. Audio systems are functioning normally.")
        return True

    # File/system questions
    if any(phrase in text_lower for phrase in ['manipulate files', 'local files', 'file access', 'can you access']):
        speak("I have limited file system access, sir. I can take screenshots and execute basic system commands.")
        return True

    # Help requests
    if any(word in text_lower for word in ['help', 'assist', 'support']):
        speak("I can help with basic commands like taking screenshots, system status, or simple conversations, sir.")
        return True

    # Time/date questions
    if any(phrase in text_lower for phrase in ['what time', 'current time', 'what date', 'today']):
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d, %Y")
        speak(f"The current time is {time_str}, and today is {date_str}, sir.")
        return True

    # AI/technology questions
    if any(phrase in text_lower for phrase in ['artificial intelligence', 'about ai', 'technology', 'machine learning']):
        speak("Artificial intelligence is a fascinating field focused on creating systems that can perform tasks requiring human-like intelligence, sir.")
        return True

    # System info
    if any(phrase in text_lower for phrase in ['system info', 'computer specs', 'hardware']):
        speak("You're running on a powerful workstation with an AMD EPYC processor and RTX A4500 graphics card, sir.")
        return True

    return False

def process(text: str):
    """
    Processes the transcribed text using an LLM to find and execute a command.
    Returns a status to the main loop ('EXIT_LOOP' or 'CONTINUE_LOOP').
    """
    if not text or not text.strip():
        return 'CONTINUE_LOOP'

    # Additional validation to prevent phantom input processing
    text = text.strip()
    if len(text) < 2:
        print(f"[Dispatcher] Input too short, ignoring: '{text}'")
        return 'CONTINUE_LOOP'

    # Filter out common phantom phrases that shouldn't trigger processing
    phantom_phrases = [
        "thank you", "thank you for your time", "thanks", "bye", "goodbye",
        "orders sir", "orders, sir", "orders", "sir"
    ]

    if text.lower() in phantom_phrases:
        print(f"[Dispatcher] Filtering phantom input: '{text}'")
        return 'CONTINUE_LOOP'

    print(f"[Dispatcher] Processing text: '{text}'")

    # Try simple command recognition first (fast)
    if simple_command_check(text):
        print(f"[Dispatcher] Handled with simple response")
        return 'EXIT_LOOP'  # Don't continue to conversation mode
    
    system_prompt = create_system_prompt()
    
    try:
        response_text = reasoning_engine.generate_response(
            prompt=text,
            system_prompt=system_prompt,
            temperature=0.0,
            max_tokens=256
        )
        print(f"[Dispatcher] LLM Raw Response: {response_text}")

        # --- RESILIENT JSON PARSING ---
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start == -1 or end == 0:
                raise json.JSONDecodeError("No JSON object found in response", response_text, 0)
            
            json_part = response_text[start:end]
            command_data = json.loads(json_part)
            
            intent = command_data.get("intent")
            entities = command_data.get("entities", {})
        except json.JSONDecodeError as e:
            print(f"[Dispatcher] ERROR: LLM returned malformed JSON. Cannot parse response. Error: {e}")
            print(f"[Dispatcher] Failing Response Text: {response_text}")
            speak("I'm sorry, I encountered a processing error. Please try again.")
            return 'CONTINUE_LOOP'

        # --- COMMAND EXECUTION (FULFILLMENT) ---
        if intent and intent in commands:
            print(f"[Dispatcher] Matched Intent: '{intent}', Entities: {entities}")
            command_function = commands[intent]
            result = command_function(entities)
            speak(result)
            return 'EXIT_LOOP' # A standard command was successful, so exit
        else:
            # For unrecognized or unknown commands, seamlessly fall back to conversation
            print(f"[Dispatcher] Command not recognized, falling back to conversation mode.")
            return 'CONTINUE_LOOP'  # This triggers conversation mode in the app

    except Exception as e:
        print(f"[Dispatcher] An unexpected error occurred: {e}")
        speak("I'm sorry, sir. I've encountered a critical error in my dispatcher module.")
        return 'CONTINUE_LOOP'