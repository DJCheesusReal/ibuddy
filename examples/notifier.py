"""Alert notifier - flaps wings and flashes red for notifications.

    python notifier.py
    Then press Enter to trigger an alert, Ctrl+C to exit.
"""

from ibuddy import IBuddyDevice

with IBuddyDevice() as buddy:
    buddy.head_color("green", 0)
    print("Notifier running. Press Enter for alert, Ctrl+C to exit.")

    try:
        while True:
            input()
            print("ALERT!")
            for _ in range(3):
                buddy.head_color("red", 0.15)
                buddy.flap(2, 0.08)
                buddy.head_color("white", 0.15)
            buddy.head_color("green", 0)
            print("Ready.")
    except (KeyboardInterrupt, EOFError):
        buddy.reset()
        print("\nStopped.")
