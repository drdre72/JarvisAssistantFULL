# dispatcher.py
import sys
import os
import re

# --- ROBUST PATHING SETUP ---
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# --- LOCAL MODULE IMPORTS ---
from jarvis_commands import commands
from speaker import speak
from intent_gate import authorized, parse_intent
from obsidian_memory import get_brain
from runtime_log import get_runtime_logger
from capability_registry import CapabilityRegistry

def simple_command_check(text: str):
    """Check for simple commands without using LLM"""
    text_lower = text.lower()
    normalized = " ".join(re.sub(r"[^\w\s]", "", text_lower).split())

    # Simple greeting responses
    if normalized in {
        "hello", "hi", "hey", "jarvis",
        "hello jarvis", "hi jarvis", "hey jarvis",
    }:
        speak("Hello, sir. How may I assist you?")
        return True

    if normalized in {"thank you", "thank you jarvis", "thanks", "thanks jarvis"}:
        speak("You're welcome, sir.")
        return True

    ability_question = re.search(
        r"\b(?:can|could|do|does|are) you (?:able to )?"
        r"(?:see|view|access|inspect|recognize|use|manage|edit|update|"
        r"write|search|read|organize|look at)\b",
        normalized,
    )
    if ability_question and re.search(r"\b(?:obsidian|vault|notes?)\b", normalized):
        speak(CapabilityRegistry().describe_vault_access())
        return True

    # Ground capability and clock answers in implemented features and local time.
    if (
        re.search(r"\bcan you see\b", normalized)
        or (
            ability_question and re.search(
                r"\b(?:tools?|ui|user interface|screen)\b", normalized
            )
        )
    ):
        speak(CapabilityRegistry().describe())
        return True

    clock_question = re.sub(r"^(?:jarvis|please|can you tell me|tell me)\s+", "", normalized)
    clock_question = re.sub(r"\s+(?:please|jarvis)$", "", clock_question)
    if clock_question in {
        "time and date", "date and time", "the time and date",
        "what time is it", "what is the time", "whats the time",
        "what date is it", "what is the date", "whats the date",
        "what day is it", "todays date", "current time", "current date",
        "the current time", "the current date", "what time", "what date",
    }:
        from datetime import datetime
        now = datetime.now()
        speak(
            f"The local time is {now.strftime('%I:%M %p')} and today's date "
            f"is {now.strftime('%A, %B %d, %Y')}, sir."
        )
        return True

    # Capability questions (check first for priority)
    if any(phrase in text_lower for phrase in ['capabilities', 'what can you do', 'your abilities', 'system capabilities']):
        speak(CapabilityRegistry().describe())
        return True

    # Identity/name questions
    identity_question = normalized.removeprefix("jarvis ").removesuffix(" jarvis")
    if identity_question in {'what is your name', 'your name'}:
        speak("I am JARVIS, your personal AI assistant, sir.")
        return True

    return False

def process(text: str):
    """
    Executes an explicit local note request or routes other text to conversation.
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
        "bye", "goodbye",
        "orders sir", "orders, sir", "orders", "sir"
    ]

    if text.lower() in phantom_phrases:
        print(f"[Dispatcher] Filtering phantom input: '{text}'")
        return 'CONTINUE_LOOP'

    print(f"[Dispatcher] Processing text: '{text}'")

    intent = parse_intent(text)
    if intent.verb == "delete_denied":
        get_runtime_logger().info("dispatch memory_delete denied")
        speak("I cannot delete memories automatically. Please review them in your Obsidian vault.")
        return 'EXIT_LOOP'

    if intent.verb in {"note", "candidate", "recall"}:
        if not intent.payload:
            speak("What would you like me to remember or look up, sir?")
            return 'EXIT_LOOP'
        if not authorized(intent, source="user_voice_or_text"):
            get_runtime_logger().info("dispatch intent=%s denied", intent.verb)
            speak("I cannot perform that memory action, sir.")
            return 'EXIT_LOOP'
        try:
            if intent.verb == "note":
                result = commands["write this down"]({"content": intent.payload})
            elif intent.verb == "candidate":
                get_brain().propose_memory(intent.payload)
                result = "Saved for your review in Obsidian, sir. This is not a confirmed fact."
            else:
                result = get_brain().recall(intent.payload)
            get_runtime_logger().info("dispatch intent=%s completed", intent.verb)
            speak(result)
            return 'EXIT_LOOP'
        except Exception as e:
            print(f"[Dispatcher] Memory action failed: {e}")
            get_runtime_logger().warning("dispatch intent=%s failed type=%s", intent.verb, type(e).__name__)
            speak("I could not complete that memory action, sir. Nothing was confirmed.")
            return 'EXIT_LOOP'

    # Try simple command recognition first (fast)
    if simple_command_check(text):
        print(f"[Dispatcher] Handled with simple response")
        return 'EXIT_LOOP'  # Don't continue to conversation mode

    print("[Dispatcher] No explicit command; using conversation mode.")
    return 'CONTINUE_LOOP'