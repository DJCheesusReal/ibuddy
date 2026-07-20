"""
YouTube Subscriber Alert
========================
The i-Buddy goes WILD every time you gain a subscriber.
Flaps wings, flashes head, blinks heart - as obnoxious as possible.

Setup:
    1. pip install ibuddy requests
    2. Get a YouTube Data API key:
         - Go to https://console.cloud.google.com
         - Create a project (or use existing)
         - Enable "YouTube Data API v3"
         - Create an API key under Credentials
    3. Find your channel ID:
         - Go to https://www.youtube.com/account_advanced
         - It starts with UC... (e.g. UCxxxxxxxxxxxxxxxxxxxxxxxx)
    4. Edit config.json next to this script (see below)

config.json format:
    {
        "api_key": "YOUR_YOUTUBE_API_KEY",
        "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxxxx"
    }

Usage:
    python youtube_sub_alert.py
    python youtube_sub_alert.py --check 60

Requires: pip install ibuddy requests
"""

import sys
import os
import json
import time
import requests

from ibuddy import IBuddyDevice

# ── Config ────────────────────────────────────────────────────────────────────

CHECK_INTERVAL = 30
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
YT_API = "https://www.googleapis.com/youtube/v3"

# ── Parse args ────────────────────────────────────────────────────────────────

args = sys.argv[1:]
if "--check" in args:
    idx = args.index("--check")
    CHECK_INTERVAL = int(args[idx + 1])
    args = args[:idx] + args[idx + 2:]


def load_config():
    """Load API key and channel ID from config.json."""
    if not os.path.exists(CONFIG_FILE):
        return None, None

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    return config.get("api_key"), config.get("channel_id")


def get_subscriber_count(api_key, channel_id):
    """Fetch current subscriber count from YouTube."""
    resp = requests.get(
        f"{YT_API}/channels",
        params={"part": "statistics", "id": channel_id, "key": api_key},
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        return None
    stats = items[0]["statistics"]
    return int(stats["subscriberCount"])


def celebrate(buddy, new_count):
    """Go absolutely nuts when someone subscribes."""
    print(f"\n  NEW SUBSCRIBER! Total: {new_count}\n", flush=True)

    # Head flash frenzy
    for _ in range(5):
        buddy.head_color("red", 0.1)
        buddy.head_color("white", 0.1)
        buddy.head_color("blue", 0.1)

    # Wing flap panic
    buddy.flap(5, 0.08)
    time.sleep(0.2)

    # Heartbeat blast
    buddy.heartbeat(5, 0.1)
    time.sleep(0.2)

    # Rainbow finish
    buddy.rainbow(1, 0.2)
    buddy.head_color("green", 0)
    print("  Ready for the next one!", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("YouTube Subscriber Alert")
    print(f"Checking every {CHECK_INTERVAL}s (Ctrl+C to stop)\n")

    api_key, channel_id = load_config()
    if not api_key or not channel_id or "YOUR_" in api_key or "YOUR_" in channel_id:
        print(f"Create {CONFIG_FILE} with your credentials:")
        print()
        print('  {')
        print('    "api_key": "YOUR_YOUTUBE_API_KEY",')
        print('    "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxxxx"')
        print('  }')
        print()
        print("Get an API key at: https://console.cloud.google.com")
        print("Find your channel ID at: https://www.youtube.com/account_advanced")
        return

    with IBuddyDevice() as buddy:
        print("Fetching subscriber count...", flush=True)
        count = get_subscriber_count(api_key, channel_id)
        if count is None:
            print("Could not fetch subscriber count. Check config.json.", flush=True)
            return

        print(f"Current subscribers: {count}", flush=True)
        buddy.head_color("green", 0.5)
        print(f"\nWaiting for new subscribers... (Ctrl+C to stop)\n", flush=True)

        try:
            while True:
                time.sleep(CHECK_INTERVAL)

                try:
                    new_count = get_subscriber_count(api_key, channel_id)
                    if new_count is None:
                        continue

                    if new_count > count:
                        celebrate(buddy, new_count)
                        count = new_count
                    elif new_count < count:
                        print(f"  Lost a subscriber. Total: {new_count}", flush=True)
                        count = new_count

                except requests.RequestException as e:
                    print(f"  API error: {e}", flush=True)

        except KeyboardInterrupt:
            buddy.reset()
            print("\nStopped.")


if __name__ == "__main__":
    main()
