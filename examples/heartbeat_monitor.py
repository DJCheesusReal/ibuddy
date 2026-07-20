"""Heartbeat monitor - pulsing heart with color feedback.

    python heartbeat_monitor.py
    python heartbeat_monitor.py fast
"""

import sys
import time
from ibuddy import IBuddyDevice

fast = "fast" in sys.argv
delay = 0.15 if fast else 0.4

with IBuddyDevice() as buddy:
    print("Heartbeat monitor running (Ctrl+C to stop)...")
    buddy.head_color("red", 0)

    try:
        while True:
            buddy.heart(True, delay)
            buddy.heart(False, delay)
    except KeyboardInterrupt:
        buddy.reset()
        print("\nStopped.")
