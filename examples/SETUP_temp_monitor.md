# CPU Temperature Monitor - Setup Guide

## What It Does

The i-Buddy acts as a real-time CPU temperature indicator:

| Color | Meaning |
|-------|---------|
| Green | Cool (< 60C) |
| Yellow | Warming up (60-75C) |
| Magenta | Hot (75-85C) |
| Red + wing flaps | Overheating (> 85C) - flapping to "cool it down" |

## Requirements

```bash
pip install ibuddy
```

Windows only. Needs admin privileges to read CPU temperature.

## Usage

**Right-click your terminal and "Run as administrator"**, then:**

```bash
python temp_monitor.py
```

It will auto-prompt for admin elevation via UAC if needed.

### Options

```bash
python temp_monitor.py --interval 5    # Check every 5 seconds (default: 3)
```

## How It Works

Reads temperature from Windows' `MSAcpi_ThermalZoneTemperature` WMI class, which requires admin access. Without admin, it shows purple as a fallback.

If temperature reading fails, try:
- Running the terminal as administrator
- Installing and running [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)
