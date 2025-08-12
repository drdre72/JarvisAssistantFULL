# dispatcher.py
import sys
import os
import json
import ollama 

# --- ROBUST PATHING SETUP ---
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# --- LOCAL MODULE IMPORTS ---
from jarvis_commands import commands
from speaker import speak

# --- INITIALIZE THE LLM CLIENT ---
try:
    client = ollama.Client()
    print("[Dispatcher] Ollama client initialized successfully.")
except Exception as e:
    print(f"[Dispatcher] FATAL: Could not connect to Ollama. Is the application running? Error: {e}")
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

def process(text: str):
    """
    Processes the transcribed text using an LLM to find and execute a command.
    Returns a status to the main loop ('EXIT_LOOP' or 'CONTINUE_LOOP').
    """
    if not text:
        return 'CONTINUE_LOOP'

    print(f"[Dispatcher] Processing text: '{text}'")
    
    system_prompt = create_system_prompt()
    
    try:
        response = client.chat(
            model='llama3:8b',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text}
            ],
            options={"temperature": 0.0}
        )
        
        response_text = response['message']['content']
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