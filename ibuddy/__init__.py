"""ibuddy - Control your MSN i-Buddy USB figure from Python.

Quick start::

    from ibuddy import IBuddyDevice

    with IBuddyDevice() as buddy:
        buddy.demo()

Available colors: red, green, blue, cyan, magenta, yellow, white.
"""

from .device import (
    AVAILABLE_COLORS,
    COLORS,
    IBuddyDevice,
)
from .exceptions import (
    IBuddyConnectionError,
    IBuddyError,
    IBuddyInvalidColorError,
    IBuddyNotFoundError,
)

__version__ = "1.0.1"

__all__ = [
    "AVAILABLE_COLORS",
    "COLORS",
    "IBuddyConnectionError",
    "IBuddyDevice",
    "IBuddyError",
    "IBuddyInvalidColorError",
    "IBuddyNotFoundError",
]
