"""Core i-Buddy device driver.

Controls the MSN i-Buddy USB HID figure with:
  - Head LED (7 colors via 3-bit RGB)
  - Heart light (on/off)
  - Wings (flap up/down)
  - Torso swivel (left/right)

Usage:
    from ibuddy import IBuddyDevice

    with IBuddyDevice() as buddy:
        buddy.head_color("red")
        buddy.flap(3)
"""

from __future__ import annotations

import sys
import time
import ctypes
from ctypes import wintypes
from typing import Dict, List, Optional, Tuple

from .exceptions import (
    IBuddyConnectionError,
    IBuddyError,
    IBuddyInvalidColorError,
    IBuddyNotFoundError,
)

# ── Hardware identifiers ──────────────────────────────────────────────────────

VENDOR_ID: int = 0x1130
PRODUCT_ID: int = 0x0001

# ── Protocol constants ────────────────────────────────────────────────────────

CMD_CLEAR: int = 0xFF  # All bits OFF (inverted: 1 = off)

# Bit positions in the 8-bit command byte (inverted logic: 0 = active)
_HEAD_R: int = 4
_HEAD_G: int = 5
_HEAD_B: int = 6
_WING_BIT: int = 2
_WING_DIR: int = 3
_SWIVEL_L: int = 0
_SWIVEL_R: int = 1
_HEART: int = 7

# Magic USB header: "USBC" + 0x00 0x40 0x02
_MESS_HEADER: bytes = bytes([0x55, 0x53, 0x42, 0x43, 0x00, 0x40, 0x02])

# ── Color definitions ─────────────────────────────────────────────────────────

COLORS: Dict[str, Tuple[int, int, int]] = {
    "red": (1, 0, 0),
    "green": (0, 1, 0),
    "blue": (0, 0, 1),
    "cyan": (0, 1, 1),
    "magenta": (1, 0, 1),
    "yellow": (1, 1, 0),
    "white": (1, 1, 1),
}

AVAILABLE_COLORS: List[str] = list(COLORS.keys())

# ── Windows API constants ─────────────────────────────────────────────────────

_GENERIC_READ: int = 0x80000000
_GENERIC_WRITE: int = 0x40000000
_OPEN_EXISTING: int = 3
_INVALID_HANDLE: int = -1


def _check_windows() -> None:
    """Raise a clear error if not running on Windows."""
    if sys.platform != "win32":
        raise IBuddyError(
            f"ibuddy only works on Windows (detected platform: {sys.platform}). "
            "The i-Buddy uses Windows HID APIs for communication."
        )


# ── Device path discovery ─────────────────────────────────────────────────────

def _find_device_path_simple() -> Optional[str]:
    """Find the i-Buddy HID device path using pywinusb."""
    try:
        import pywinusb.hid as hid
    except ImportError:
        raise IBuddyError(
            "pywinusb is required for device discovery. "
            "Install it with: pip install pywinusb"
        )

    # Prefer mi_01 interface, then fall back to any i-Buddy interface
    for device in hid.find_all_hid_devices():
        if device.vendor_id == VENDOR_ID and device.product_id == PRODUCT_ID:
            if "mi_01" in device.device_path.lower():
                return device.device_path

    for device in hid.find_all_hid_devices():
        if device.vendor_id == VENDOR_ID and device.product_id == PRODUCT_ID:
            return device.device_path

    return None


def _find_device_path_setupdi() -> Optional[str]:
    """Find the i-Buddy HID device path using the Windows SetupDi API."""
    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_byte * 8),
        ]

    class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("InterfaceClassGuid", GUID),
            ("Flags", wintypes.DWORD),
            ("Reserved", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class SP_DEVICE_INTERFACE_DETAIL_DATA_W(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("DevicePath", ctypes.c_wchar * 1024),
        ]

    hid_guid = GUID()
    ctypes.windll.hid.HidD_GetHidGuid(ctypes.byref(hid_guid))

    setupapi = ctypes.windll.setupapi
    devinfo = setupapi.SetupDiGetClassDevsW(ctypes.byref(hid_guid), None, None, 0x12)

    iface = SP_DEVICE_INTERFACE_DATA()
    iface.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)

    paths: List[str] = []
    i = 0
    while setupapi.SetupDiEnumDeviceInterfaces(
        devinfo, None, ctypes.byref(hid_guid), i, ctypes.byref(iface)
    ):
        req = wintypes.DWORD()
        setupapi.SetupDiGetDeviceInterfaceDetailW(
            devinfo, ctypes.byref(iface), None, 0, ctypes.byref(req), None
        )
        detail = SP_DEVICE_INTERFACE_DETAIL_DATA_W()
        detail.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_W)
        if setupapi.SetupDiGetDeviceInterfaceDetailW(
            devinfo, ctypes.byref(iface), ctypes.byref(detail), req, None, None
        ):
            path = detail.DevicePath
            if (
                "vid_1130" in path.lower()
                and "pid_0001" in path.lower()
                and "mi_00" in path.lower()
            ):
                paths.append(path)
        i += 1

    setupapi.SetupDiDestroyDeviceInfoList(devinfo)
    return paths[0] if paths else None


# ── Main device class ─────────────────────────────────────────────────────────

class IBuddyDevice:
    """Control an MSN i-Buddy USB figure.

    Use as a context manager for automatic cleanup::

        with IBuddyDevice() as buddy:
            buddy.head_color("red")
            buddy.flap(3)

    Or manage manually::

        buddy = IBuddyDevice()
        try:
            buddy.demo()
        finally:
            buddy.close()

    Args:
        auto_reset: If True (default), resets the device on connection.

    Raises:
        IBuddyNotFoundError: No i-Buddy device is connected.
        IBuddyConnectionError: The device could not be opened.
    """

    def __init__(self, auto_reset: bool = True) -> None:
        _check_windows()

        self._hiddll = ctypes.windll.hid
        self._kernel32 = ctypes.windll.kernel32
        self._cmd: int = CMD_CLEAR
        self._handle: Optional[int] = None

        path = _find_device_path_simple()
        if path is None:
            raise IBuddyNotFoundError(
                "i-Buddy not found. Make sure it's plugged in and try again."
            )

        self._handle = self._kernel32.CreateFileW(
            path,
            _GENERIC_READ | _GENERIC_WRITE,
            0,
            None,
            _OPEN_EXISTING,
            0,
            None,
        )
        if self._handle == _INVALID_HANDLE:
            raise IBuddyConnectionError(
                f"Failed to open i-Buddy device (error {self._kernel32.GetLastError()}). "
                "Try unplugging and re-plugging the device."
            )

        if auto_reset:
            self.reset()

    # ── Low-level I/O ─────────────────────────────────────────────────────

    def _send(self, cmd: Optional[int] = None) -> None:
        """Send a command byte to the device via HID output report."""
        if cmd is None:
            cmd = self._cmd
        data = bytes([0x00]) + _MESS_HEADER + bytes([cmd])
        buf = ctypes.create_string_buffer(data)
        self._hiddll.HidD_SetOutputReport(self._handle, buf, len(data))

    def _bit(self, num: int, value: int | bool) -> None:
        """Set or clear a bit in the command byte (inverted logic)."""
        if value:
            self._cmd &= ~(1 << num)
        else:
            self._cmd |= (1 << num)

    # ── Low-level state setters ───────────────────────────────────────────

    def reset(self) -> None:
        """Turn off all outputs (head LED, heart, wings, swivel)."""
        self._cmd = CMD_CLEAR
        self._send()
        time.sleep(0.05)

    def set_head_color(self, r: int | bool, g: int | bool, b: int | bool) -> None:
        """Set the head LED color using raw RGB bits (0 or 1 each).

        For named colors, use :meth:`head_color` instead.
        """
        self._bit(_HEAD_R, r)
        self._bit(_HEAD_G, g)
        self._bit(_HEAD_B, b)
        self._bit(_WING_BIT, 1)  # Disable wing while setting color

    def set_heart(self, on: int | bool) -> None:
        """Turn the heart LED on or off."""
        self._bit(_HEART, on)

    def set_wing(self, up: int | bool) -> None:
        """Set wing position: True = up, False = down."""
        if up:
            self._bit(_WING_DIR, 1)
            self._bit(_WING_BIT, 0)
        else:
            self._bit(_WING_DIR, 0)
            self._bit(_WING_BIT, 1)

    def set_swivel(self, direction: str) -> None:
        """Swivel the torso: ``"left"`` or ``"right"``."""
        if direction == "left":
            self._bit(_SWIVEL_R, 0)
            self._bit(_SWIVEL_L, 1)
        else:
            self._bit(_SWIVEL_L, 0)
            self._bit(_SWIVEL_R, 1)

    # ── High-level actions ────────────────────────────────────────────────

    def head_color(self, name: str, duration: float = 0.3) -> None:
        """Set the head LED to a named color and hold for ``duration`` seconds.

        Available colors: red, green, blue, cyan, magenta, yellow, white.

        Args:
            name: Color name (see :data:`COLORS`).
            duration: How long to hold the color before returning.

        Raises:
            IBuddyInvalidColorError: If ``name`` is not a valid color.
        """
        if name not in COLORS:
            raise IBuddyInvalidColorError(
                f"Unknown color: '{name}'. Available colors: {', '.join(AVAILABLE_COLORS)}"
            )
        r, g, b = COLORS[name]
        self.set_head_color(r, g, b)
        self._send()
        time.sleep(duration)

    def heart(self, on: bool, duration: float = 0.3) -> None:
        """Turn the heart LED on or off and hold for ``duration`` seconds.

        Args:
            on: True to turn on, False to turn off.
            duration: How long to hold the state.
        """
        self.set_heart(on)
        self._send()
        time.sleep(duration)

    def flap(self, times: int = 3, delay: float = 0.15) -> None:
        """Flap the wings ``times`` times.

        Args:
            times: Number of flap cycles.
            delay: Seconds between each flap position.
        """
        for _ in range(times):
            self.set_wing(True)
            self._send()
            time.sleep(delay)
            self.set_wing(False)
            self._send()
            time.sleep(delay)

    def wiggle(self, times: int = 3, delay: float = 0.5) -> None:
        """Swivel the torso left and right ``times`` times.

        Args:
            times: Number of wiggle cycles.
            delay: Seconds between each direction change.
        """
        for _ in range(times):
            self.set_swivel("left")
            self._send()
            time.sleep(delay)
            self.set_swivel("right")
            self._send()
            time.sleep(delay)

    def heartbeat(self, times: int = 3, delay: float = 0.2) -> None:
        """Blink the heart LED ``times`` times.

        Args:
            times: Number of blinks.
            delay: Seconds between on and off states.
        """
        for _ in range(times):
            self.set_heart(True)
            self._send()
            time.sleep(delay)
            self.set_heart(False)
            self._send()
            time.sleep(delay)

    def rainbow(self, times: int = 2, duration: float = 0.3) -> None:
        """Cycle through all 7 head colors ``times`` times.

        Args:
            times: Number of full color cycles.
            duration: Seconds to hold each color.
        """
        for _ in range(times):
            for color in AVAILABLE_COLORS:
                self.head_color(color, duration)

    def celebrate(self) -> None:
        """Run a celebration sequence: wiggle, flap, heartbeat, and rainbow."""
        self.wiggle(2, 0.3)
        time.sleep(0.2)
        self.flap(3, 0.12)
        time.sleep(0.2)
        self.heartbeat(3, 0.15)
        time.sleep(0.2)
        self.rainbow(1, 0.25)

    def demo(self) -> None:
        """Run a full demonstration of all capabilities."""
        for color in AVAILABLE_COLORS:
            self.head_color(color, 0.4)

        time.sleep(0.2)
        self.flap(3)
        time.sleep(0.2)
        self.wiggle(3)
        time.sleep(0.2)
        self.heartbeat(3)
        time.sleep(0.2)
        self.reset()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def close(self) -> None:
        """Reset the device and close the connection."""
        if self._handle is not None and self._handle != _INVALID_HANDLE:
            self.reset()
            self._kernel32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self) -> "IBuddyDevice":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        status = "connected" if self._handle and self._handle != _INVALID_HANDLE else "closed"
        return f"<IBuddyDevice [{status}]>"
