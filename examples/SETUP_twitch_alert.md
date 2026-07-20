# Twitch Stream Alert - Setup Guide

## What It Does

The i-Buddy alerts you when your favourite streamers go live. Flaps wings and flashes colors so you never miss a stream.

**No API keys or credentials needed.**

## Requirements

```bash
pip install ibuddy requests
```

## Setup

### 1. Create a streamers.txt file

Create a file called `streamers.txt` next to the script with one Twitch username per line:

```
shroud
xqc
kai cenat
pokimane
```

Lines starting with `#` are ignored.

### 2. Run it

```bash
python twitch_alert.py
```

### Options

```bash
python twitch_alert.py --check 15        # Check every 15 seconds (default: 30)
python twitch_alert.py --streamers my.txt  # Use a different file
```

## How It Works

Uses Twitch's public GQL API (the same one the Twitch website uses) to check if any of your listed streamers are currently live. When someone goes live, the i-Buddy flaps and flashes to grab your attention.
