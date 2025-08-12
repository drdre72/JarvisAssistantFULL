import pvporcupine
import pyaudio
import struct
import subprocess
import time
import sys
import os
import signal

ACCESS_KEY = "jEN9RUBpiJ46RTyk+9TrhR7QSjeMtANAVKx+6IBw0CB9p6SMYrDUAg=="

def main():
    print("Initializing Porcupine...")
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=["jarvis"]
    )

    pa = pyaudio.PyAudio()

    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("✅ Ready. Say 'Jarvis' to activate.")
    jarvis_process = None

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            if porcupine.process(pcm) >= 0:
                print("🎤 Wake word detected!")
                
                if jarvis_process and jarvis_process.poll() is None:
                    print("🔄 Stopping existing Jarvis session...")
                    jarvis_process.terminate()
                    try:
                        jarvis_process.wait(timeout=1)  # Wait for clean exit
                    except subprocess.TimeoutExpired:
                        jarvis_process.kill()  # Force kill if needed
                    time.sleep(0.5)
                
                print("🚀 Starting Jarvis...")
                
                script_dir = os.path.dirname(os.path.abspath(__file__))
                jarvis_script = os.path.join(script_dir, "llama_trigger.py")
                
                jarvis_process = subprocess.Popen([
                    sys.executable,
                    jarvis_script,
                    "--activated"
                ])

    except KeyboardInterrupt:
        print("🔌 Shutting down...")

    finally:
        if jarvis_process and jarvis_process.poll() is None:
            jarvis_process.terminate()
            try:
                jarvis_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                jarvis_process.kill()
        if audio_stream is not None:
            audio_stream.stop_stream()
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        porcupine.delete()

if __name__ == "__main__":
    main()