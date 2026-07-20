"""Quick test - just runs the demo.

    python quickstart.py
"""

from ibuddy import IBuddyDevice

print("ibuddy quickstart!")
print()

with IBuddyDevice() as buddy:
    print("Connected:", buddy)
    print()
    print("Running demo...")
    buddy.demo()
    print("Done!")
