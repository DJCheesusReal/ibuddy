# YouTube Subscriber Alert - Setup Guide

## What It Does

The i-Buddy goes WILD every time you gain a subscriber. Flaps wings, flashes the head LED, blinks the heart - as obnoxious as possible.

## Requirements

```bash
pip install ibuddy requests
```

## Setup

### 1. Get a YouTube Data API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Go to **APIs & Services > Library**
4. Search for **YouTube Data API v3** and enable it
5. Go to **APIs & Services > Credentials**
6. Click **Create Credentials > API Key**
7. Copy the key

### 2. Find Your Channel ID

1. Go to [YouTube Account Advanced](https://www.youtube.com/account_advanced)
2. Your channel ID is at the top (starts with `UC`, e.g. `UCxxxxxxxxxxxxxxxxxxxxxxxx`)

### 3. Create config.json

Create a file called `config.json` next to the script:

```json
{
    "api_key": "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

### 4. Run it

```bash
python youtube_sub_alert.py
```

### Options

```bash
python youtube_sub_alert.py --check 60    # Check every 60 seconds (default: 30)
```

## How It Works

Polls the YouTube Data API every 30 seconds to check your subscriber count. When it increases, the i-Buddy celebrates. When it decreases (unsub), it notes it quietly.

## Notes

- YouTube API has a free quota of 10,000 units/day
- Each check costs ~1 unit, so 30-second intervals = ~2,880 checks/day (well within limits)
- The API key is yours - don't share it publicly
