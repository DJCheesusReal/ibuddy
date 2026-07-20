"""Disco party - rainbow colors synced with flapping.

    python disco_party.py
    python disco_party.py 5
"""

import sys
import time
from ibuddy import IBuddyDevice, AVAILABLE_COLORS

times = int(sys.argv[1]) if len(sys.argv) > 1 else 3

with IBuddyDevice() as buddy:
    for i in range(times):
        print(f"Round {i + 1}/{times}")
        for color in AVAILABLE_COLORS:
            buddy.head_color(color, 0.15)
            buddy.flap(1, 0.08)
        time.sleep(0.3)

    buddy.reset()
    print("Party over!")
