"""
Twitch Stream Live Alert
========================
The i-Buddy flaps and flashes when your favourite streamers go live.
No API keys needed - just a list of streamer names.

Setup:
    1. pip install ibuddy requests
    2. Create a file called streamers.txt next to this script
    3. Put one Twitch username per line, e.g.:
         shroud
         xqc
         kai cenat

Usage:
    python twitch_alert.py
    python twitch_alert.py --check 15
    python twitch_alert.py --streamers my_list.txt

Requires: pip install ibuddy requests
"""

import sys
import os
import time
import json
import requests

from ibuddy import IBuddyDevice

# ── Config ────────────────────────────────────────────────────────────────────

CHECK_INTERVAL = 30
STREAMERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamers.txt")

# Twitch GQL endpoint (public, no auth needed)
GQL_URL = "https://gql.twitch.tv/gql"
CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"  # Twitch website's public client ID

# ── Parse args ────────────────────────────────────────────────────────────────

args = sys.argv[1:]
if "--check" in args:
    idx = args.index("--check")
    CHECK_INTERVAL = int(args[idx + 1])
    args = args[:idx] + args[idx + 2:]
if "--streamers" in args:
    idx = args.index("--streamers")
    STREAMERS_FILE = args[idx + 1]
    args = args[:idx] + args[idx + 2:]


# ── Twitch GQL ────────────────────────────────────────────────────────────────

def load_streamers():
    """Load streamer names from txt file (one per line)."""
    if not os.path.exists(STREAMERS_FILE):
        return None

    with open(STREAMERS_FILE, "r") as f:
        names = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]

    return names if names else None


GQL_QUERY = """
query ($login: String!) {
    user(login: $login) {
        login
        stream {
            title
            viewersCount
        }
    }
}
"""


def check_streams_gql(usernames):
    """Check which streamers are live using Twitch's GQL API."""
    headers = {
        "Client-ID": CLIENT_ID,
        "Content-Type": "application/json",
    }

    results = {}
    for name in usernames:
        try:
            resp = requests.post(
                GQL_URL,
                headers=headers,
                json={"query": GQL_QUERY, "variables": {"login": name}},
                timeout=10,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            user = data.get("data", {}).get("user")
            if user and user.get("stream"):
                login = user["login"].lower()
                stream = user["stream"]
                results[login] = {
                    "title": stream.get("title", "Untitled"),
                    "viewers": stream.get("viewersCount", 0),
                }
        except requests.RequestException:
            continue

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Twitch Stream Alert")
    print(f"Checking every {CHECK_INTERVAL}s (Ctrl+C to stop)\n")

    streamers = load_streamers()
    if streamers is None:
        print(f"Create {STREAMERS_FILE} with one username per line:")
        print("  shroud")
        print("  xqc")
        print("  kai cenat")
        return

    print(f"Watching {len(streamers)} streamers: {', '.join(streamers)}\n")

    with IBuddyDevice() as buddy:
        previously_live = set()

        try:
            while True:
                try:
                    live = check_streams_gql(streamers)

                    # Detect newly live
                    for name, info in live.items():
                        if name not in previously_live:
                            print(f"  LIVE: {name} - {info['title'][:50]} ({info['viewers']} viewers)", flush=True)
                            for _ in range(3):
                                buddy.head_color("magenta", 0.15)
                                buddy.flap(2, 0.08)
                                buddy.head_color("white", 0.15)
                            buddy.head_color("green", 0)

                    # Detect went offline
                    for name in list(previously_live):
                        if name not in live:
                            print(f"  OFFLINE: {name}", flush=True)

                    previously_live = set(live.keys())

                except Exception as e:
                    print(f"  Error: {e}", flush=True)

                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            buddy.reset()
            print("\nStopped.")


if __name__ == "__main__":
    main()
