"""Custom exceptions for the ibuddy library."""


class IBuddyError(Exception):
    """Base exception for all ibuddy errors."""


class IBuddyNotFoundError(IBuddyError):
    """Raised when no i-Buddy device is connected."""


class IBuddyConnectionError(IBuddyError):
    """Raised when the device cannot be opened."""


class IBuddyInvalidColorError(IBuddyError):
    """Raised when an invalid color name is used."""
