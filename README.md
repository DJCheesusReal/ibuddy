# ibuddy

Control your MSN i-Buddy USB figure from Python and Discord.

The i-Buddy is a small USB HID figure with a head LED (7 colors), heart light, flapping wings, and a swiveling torso. This library gives you full control over all of it.

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

That's it. Plug in your i-Buddy, run the code, and watch it go.

## Discord Integration

A [Vencord](https://vencord.dev/) plugin is included that makes your i-Buddy react to Discord activity:

- **Voice call status** - Head LED changes color based on mute/deafen state (green = unmuted, red = muted, blue = deafened)
- **DM notifications** - i-Buddy flaps, swivels, and blinks its heart when you receive a DM
- **Priority contacts** - Heartbeat when specific users come online (like old MSN Messenger)

### Setup

#### 1. Install the Python package

```
pip install ibuddy websockets
```

#### 2. Clone this repo

```
git clone https://github.com/djcheesusreal/ibuddy.git
cd ibuddy
```

#### 3. Start the WebSocket server

```
python ibuddy_ws.py
```

This runs a local WebSocket server on `ws://127.0.0.1:8765` that the Vencord plugin connects to.

#### 4. Install the Vencord plugin

Copy the `vencord-plugin/` folder into your Vencord userplugins directory:

```
%AppData%\Roaming\Vencord\userplugins\iBuddy\
```

#### 5. Rebuild Vencord

```
cd C:\path\to\Vencord
pnpm build
```

#### 6. Restart Discord

Kill Discord completely from Task Manager (not just close the window), then relaunch it.

#### 7. Enable the plugin

Go to **Vencord Settings > Plugins** and enable **iBuddy**.

### Plugin Settings

| Setting | Description |
|---------|-------------|
| **WebSocket server URL** | `ws://127.0.0.1:8765` (default) |
| **Path to python.exe** | `python` (default) |
| **Path to ibuddy_ws.py** | Set this to where you cloned `ibuddy_ws.py` |
| **Auto-start server** | Launch the Python server automatically when Discord loads |
| **Message notifications** | Flap + swivel + heartbeat on new DMs |
| **Priority contacts** | Comma-separated Discord user IDs — heartbeat when they come online |

To find user IDs: enable Developer Mode in Discord (Settings > Advanced > Developer Mode), then right-click a user and click **Copy User ID**.

### How it works

```
Discord (Vencord plugin)
    |  WebSocket JSON commands
    v
ibuddy_ws.py
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

### Exceptions

| Exception | When |
|-----------|------|
| `IBuddyError` | Base exception |
| `IBuddyNotFoundError` | i-Buddy not plugged in |
| `IBuddyConnectionError` | Device found but can't be opened |
| `IBuddyInvalidColorError` | Unknown color name |

## Requirements

- Windows
- Python 3.9+
- [Vencord](https://vencord.dev/) (for Discord integration)

## License

MIT
