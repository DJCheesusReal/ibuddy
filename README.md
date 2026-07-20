# ibuddy

Control your MSN i-Buddy USB figure from Python and Discord.

The i-Buddy is a small USB HID figure with a head LED (7 colors), heart light, flapping wings, and a swiveling torso.

```
pip install ibuddy
```

> **Windows only** - The i-Buddy uses Windows HID APIs for communication.

## Quick Start

```python
from ibuddy import IBuddyDevice

with IBuddyDevice() as buddy:
    buddy.demo()
```

Plug in your i-Buddy, run the code, and watch it go.

## Discord Integration

A [Vencord](https://vencord.dev/) plugin that makes your i-Buddy react to Discord:

- **Voice calls** — Head LED changes based on mute/deafen state (green = unmuted, red = muted, blue = deafened)
- **DM notifications** — Flaps, swivels, and blinks its heart when you receive a DM
- **Priority contacts** — Heartbeat when specific users come online (like old MSN Messenger)

### Setup

#### 1. Install Python dependencies

```
pip install ibuddy websockets
```

#### 2. Clone this repo

```
git clone https://github.com/djcheesusreal/ibuddy.git
cd ibuddy
```

#### 3. Copy the Vencord plugin

Copy the `vencord-plugin/` folder into your Vencord userplugins directory:

```
%AppData%\Roaming\Vencord\userplugins\iBuddy\
```

#### 4. Rebuild Vencord and restart Discord

```
cd C:\path\to\Vencord
pnpm build
```

Kill Discord completely from Task Manager (not just close the window), then relaunch.

#### 5. Enable the plugin

Go to **Vencord Settings > Plugins** and enable **iBuddy**.

The plugin automatically installs `ibuddy_ws.py` into `%AppData%\Roaming\Vencord\` and starts the WebSocket server when Discord loads. No manual server startup needed.

### Plugin Settings

| Setting | Description |
|---------|-------------|
| **WebSocket server URL** | `ws://127.0.0.1:8765` (default) |
| **Path to python.exe** | `python` (default) |
| **Path to ibuddy_ws.py** | Leave blank for auto-install |
| **Auto-start server** | Launch the Python server automatically when Discord loads |
| **Message notifications** | Flap + swivel + heartbeat on new DMs |
| **Priority contacts** | Comma-separated Discord user IDs — heartbeat when they come online |

To find user IDs: enable Developer Mode in Discord (Settings > Advanced > Developer Mode), then right-click a user and click **Copy User ID**.

### How it works

```
Discord (Vencord plugin)
    |  WebSocket JSON commands
    v
ibuddy_ws.py (auto-installed)
    |  USB HID
    v
i-Buddy hardware
```

The plugin monitors Discord's internal flux events (mute state, incoming DMs, presence updates) and sends commands to the Python server, which controls the physical device. No Discord bot token required.

## Library Usage

### Head LED

```python
buddy.head_color("red")         # Hold for 0.3s (default)
buddy.head_color("blue", 1.0)   # Hold for 1 second
buddy.head_color("green", 0)    # Set and return immediately

# Available colors: red, green, blue, cyan, magenta, yellow, white
```

### Heart LED

```python
buddy.heart(True)         # Turn on for 0.3s
buddy.heart(False)        # Turn off for 0.3s
buddy.heartbeat(times=5)  # Blink 5 times
```

### Wings

```python
buddy.flap(times=3, delay=0.15)  # Flap 3 times
```

### Torso Swivel

```python
buddy.wiggle(times=3, delay=0.5)  # Swivel left/right 3 times
```

### Combos

```python
buddy.rainbow(times=2)     # Cycle all 7 colors twice
buddy.celebrate()           # Wiggle + flap + heartbeat + rainbow
buddy.demo()                # Full demo of every feature
```

### Low-Level Control

```python
buddy.set_head_color(1, 0, 0)  # Set raw RGB bits
buddy.set_wing(True)            # Wings up
buddy.set_swivel("left")       # Swivel left
buddy.set_heart(True)           # Heart on
buddy.reset()                   # Everything off
```

## Examples

### Disco Party

Rainbow colors synced with wing flaps:

```python
import time
from ibuddy import IBuddyDevice, AVAILABLE_COLORS

with IBuddyDevice() as buddy:
    for _ in range(3):
        for color in AVAILABLE_COLORS:
            buddy.head_color(color, 0.15)
            buddy.flap(1, 0.08)
        time.sleep(0.3)
    buddy.reset()
```

### Heartbeat Monitor

Pulsing heart with color feedback:

```python
from ibuddy import IBuddyDevice

with IBuddyDevice() as buddy:
    buddy.head_color("red", 0)
    while True:
        buddy.heart(True, 0.4)
        buddy.heart(False, 0.4)
```

### Alert Notifier

Flaps wings and flashes red on demand:

```python
from ibuddy import IBuddyDevice

with IBuddyDevice() as buddy:
    buddy.head_color("green", 0)
    while True:
        input()  # Press Enter for alert
        for _ in range(3):
            buddy.head_color("red", 0.15)
            buddy.flap(2, 0.08)
            buddy.head_color("white", 0.15)
        buddy.head_color("green", 0)
```

### CPU Temperature Monitor

Changes color based on CPU temperature:

| Color | Meaning |
|-------|---------|
| Green | Cool (< 60C) |
| Yellow | Warming up (60-75C) |
| Magenta | Hot (75-85C) |
| Red + flaps | Overheating (> 85C) |

Requires admin privileges. Run terminal as administrator:

```bash
pip install ibuddy
python examples/temp_monitor.py
```

### Twitch Stream Alert

Flaps and flashes when your favourite streamers go live. No API keys needed.

```bash
pip install ibuddy requests
```

Create `streamers.txt` with one Twitch username per line:

```
shroud
xqc
kai cenat
```

Then run:

```bash
python examples/twitch_alert.py
python examples/twitch_alert.py --check 15    # Check every 15 seconds
```

Uses Twitch's public GQL API (the same one the Twitch website uses).

### YouTube Subscriber Alert

Goes wild every time you gain a subscriber.

```bash
pip install ibuddy requests
```

1. Get a YouTube Data API key from [Google Cloud Console](https://console.cloud.google.com)
2. Find your channel ID at [YouTube Account Advanced](https://www.youtube.com/account_advanced)
3. Create `config.json`:

```json
{
    "api_key": "YOUR_YOUTUBE_API_KEY",
    "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

4. Run:

```bash
python examples/youtube_sub_alert.py
python examples/youtube_sub_alert.py --check 60    # Check every 60 seconds
```

YouTube API free quota: 10,000 units/day. Each check costs ~1 unit.

## API Reference

### `IBuddyDevice(auto_reset=True)`

Main device class. Connects to the i-Buddy on creation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auto_reset` | `bool` | `True` | Reset all outputs on connection |

### High-Level Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `head_color(name, duration=0.3)` | color name, seconds | Set head LED color |
| `heart(on, duration=0.3)` | bool, seconds | Turn heart on/off |
| `flap(times=3, delay=0.15)` | count, seconds | Flap wings |
| `wiggle(times=3, delay=0.5)` | count, seconds | Swivel torso |
| `heartbeat(times=3, delay=0.2)` | count, seconds | Blink heart |
| `rainbow(times=2, duration=0.3)` | cycles, seconds | Cycle all colors |
| `celebrate()` | - | Party mode |
| `demo()` | - | Full feature demo |
| `reset()` | - | Turn everything off |

### Low-Level Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `set_head_color(r, g, b)` | 0 or 1 each | Set raw RGB bits |
| `set_heart(on)` | bool | Set heart state |
| `set_wing(up)` | bool | Set wing position |
| `set_swivel(direction)` | "left"/"right" | Set swivel direction |
| `close()` | - | Reset and disconnect |

### Exceptions

| Exception | When |
|-----------|------|
| `IBuddyError` | Base exception |
| `IBuddyNotFoundError` | i-Buddy not plugged in |
| `IBuddyConnectionError` | Device found but can't be opened |
| `IBuddyInvalidColorError` | Unknown color name |

### Available Colors

| Name | RGB |
|------|-----|
| `red` | (1, 0, 0) |
| `green` | (0, 1, 0) |
| `blue` | (0, 0, 1) |
| `cyan` | (0, 1, 1) |
| `magenta` | (1, 0, 1) |
| `yellow` | (1, 1, 0) |
| `white` | (1, 1, 1) |

## Requirements

- Windows
- Python 3.9+
- [Vencord](https://vencord.dev/) (for Discord integration)

## License

MIT
