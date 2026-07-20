"""
CPU Temperature Monitor
=======================
The i-Buddy changes color based on your CPU temperature:

  GREEN  = Cool (< 60C)
  YELLOW = Warming up (60-75C)
  MAGENTA = Hot (75-85C)
  RED    = Overheating! (> 85C) - wings flap to "cool it down"

Setup:
    pip install ibuddy

    Just run it! It will auto-elevate to admin if needed (UAC prompt).
    If you decline admin, it will show purple as a fallback.

Usage:
    python temp_monitor.py
    python temp_monitor.py --interval 5
"""

import sys
import os
import time
import subprocess
import ctypes

from ibuddy import IBuddyDevice


def is_admin():
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate():
    """Re-launch this script as admin (triggers UAC prompt)."""
    script = os.path.abspath(sys.argv[0])
    args = " ".join(f'"{a}"' for a in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}" {args}', None, 1
    )
    sys.exit(0)


def get_cpu_temp():
    """Get CPU temperature in Celsius via WMI thermal zone."""
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "$t = Get-WmiObject MSAcpi_ThermalZoneTemperature "
                "-Namespace 'root/wmi' -ErrorAction Stop; "
                "$t.CurrentTemperature"
            ],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout.strip().split("\n")[0]
            return (int(raw.strip()) - 2732) / 10.0
    except Exception:
        pass

    try:
        import wmi
        w = wmi.WMI(namespace=r"root\WMI")
        temps = w.MSAcpi_ThermalZoneTemperature()
        if temps:
            return (temps[0].CurrentTemperature - 2732) / 10.0
    except Exception:
        pass

    return None


def main():
    # Auto-elevate to admin if not already
    if not is_admin():
        print("Need admin to read CPU temperature. Requesting elevation...")
        elevate()

    interval = 3
    if "--interval" in sys.argv:
        idx = sys.argv.index("--interval")
        interval = int(sys.argv[idx + 1])

    print("CPU Temperature Monitor (admin)")
    print(f"Checking every {interval}s (Ctrl+C to stop)\n")

    with IBuddyDevice() as buddy:
        last_state = None

        try:
            while True:
                temp = get_cpu_temp()

                if temp is None:
                    print("  Could not read temperature.", flush=True)
                    buddy.head_color("magenta", 0)
                    time.sleep(interval)
                    continue

                if temp < 60:
                    state, color = "cool", "green"
                elif temp < 75:
                    state, color = "warm", "yellow"
                elif temp < 85:
                    state, color = "hot", "magenta"
                else:
                    state, color = "overheating", "red"

                if state != last_state:
                    tag = "FLAPPING TO COOL DOWN!" if state == "overheating" else state.upper()
                    print(f"  {temp:.0f}C - {tag}", flush=True)
                    last_state = state

                buddy.head_color(color, 0)

                if state == "overheating":
                    buddy.flap(2, 0.1)

                time.sleep(interval)

        except KeyboardInterrupt:
            buddy.reset()
            print("\nStopped.")


if __name__ == "__main__":
    main()
