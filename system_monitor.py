import psutil
import time
import json
import sys

def get_system_stats():
    """
    Gathers CPU usage, memory usage, and battery information.
    """
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'battery_percent': psutil.sensors_battery().percent if hasattr(psutil, "sensors_battery") and psutil.sensors_battery() else 'N/A',
    }

if __name__ == "__main__":
    while True:
        stats = get_system_stats()
        # Output stats as a single JSON line to stdout
        print(json.dumps(stats))
        sys.stdout.flush()
        time.sleep(2) # Update every 2 seconds 