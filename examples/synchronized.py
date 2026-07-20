"""Color cycle with wing flaps - mesmerizing synchronized pattern.

    python synchronized.py
"""

import time
from ibuddy import IBuddyDevice, AVAILABLE_COLORS

with IBuddyDevice() as buddy:
    print("Synchronized mode (Ctrl+C to stop)...")

    try:
        while True:
            for color in AVAILABLE_COLORS:
                buddy.head_color(color, 0.2)
                buddy.flap(1, 0.1)
                time.sleep(0.1)
    except KeyboardInterrupt:
        buddy.reset()
        print("\nStopped.")
