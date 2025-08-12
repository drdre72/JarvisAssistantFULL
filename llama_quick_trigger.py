# In wake_listener.py (or llama_trigger.py) after detecting “Jarvis”
text = listen_short(duration=2)  # short 2‑sec capture
if match_command(text):
    dispatcher.process(text)
    return     # skip longer timeout
# else fallback:
text = listen_full(timeout=8)
dispatcher.process(text)
