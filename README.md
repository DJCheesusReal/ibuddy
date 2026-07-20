# ibuddy

Control your MSN i-Buddy USB figure from Python.

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

## Usage

### Connecting

The library uses a context manager so the device is always properly reset when you're done:

```python
from ibuddy import IBuddyDevice

with IBuddyDevice() as buddy:
    buddy.head_color("red")
    buddy.flap(3)
# Automatically resets and closes
```

### Head LED

Set the head to one of 7 named colors:

```python
buddy.head_color("red")         # Hold for 0.3s (default)
buddy.head_color("blue", 1.0)   # Hold for 1 second
buddy.head_color("green", 0)    # Set and return immediately

# Available colors: red, green, blue, cyan, magenta, yellow, white
```

Or set raw RGB bits directly:

```python
buddy.set_head_color(1, 0, 0)  # Red (r=1, g=0, b=0)
buddy._send()                   # Send the command
```

### Heart LED

```python
buddy.heart(True)         # Turn on for 0.3s
buddy.heart(False)        # Turn off for 0.3s
buddy.heart(True, 1.0)    # Stay on for 1 second
buddy.heart(False, 0)     # Turn off immediately

buddy.heartbeat(times=5, delay=0.2)  # Blink 5 times
```

### Wings

```python
buddy.flap(times=3, delay=0.15)  # Flap 3 times (default)
buddy.flap(10, 0.1)              # Flap 10 times, faster
```

### Torso Swivel

```python
buddy.wiggle(times=3, delay=0.5)  # Wiggle left/right 3 times
buddy.wiggle(5, 0.3)              # Faster wiggle
```

### Combos

```python
buddy.rainbow(times=2)     # Cycle all 7 colors twice
buddy.celebrate()           # Wiggle + flap + heartbeat + rainbow
buddy.demo()                # Full demo of every feature
```

### Low-Level Control

```python
buddy.set_wing(True)        # Wings up
buddy.set_wing(False)       # Wings down
buddy.set_swivel("left")    # Swivel left
buddy.set_swivel("right")   # Swivel right
buddy.set_heart(True)       # Heart on
buddy.reset()               # Everything off
```

After setting state manually, call `buddy._send()` to push it to the device.

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
| `IBuddyError` | Base exception for all ibuddy errors |
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
- `pywinusb` (installed automatically)

## License

MIT
