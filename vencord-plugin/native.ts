import { IpcMainInvokeEvent } from "electron";
import { ChildProcess, spawn } from "child_process";
import { existsSync, mkdirSync, writeFileSync } from "fs";
import { join } from "path";

let serverProcess: ChildProcess | null = null;

const IBUDDY_WS_PY = `"""
ibuddy_ws.py - WebSocket server for i-Buddy.

Accepts JSON commands over WebSocket and controls the i-Buddy hardware.
Runs on 127.0.0.1:8765.

Commands:
  {"cmd": "color", "color": "red|green|blue|cyan|magenta|yellow|white"}
  {"cmd": "heart", "on": true|false}
  {"cmd": "flap", "times": 3}
  {"cmd": "wiggle", "times": 3}
  {"cmd": "heartbeat", "times": 3}
  {"cmd": "rainbow", "times": 2}
  {"cmd": "celebrate"}
  {"cmd": "reset"}
  {"cmd": "demo"}
  {"cmd": "notify", "on": true|false}
  {"cmd": "status"}

Requires: pip install ibuddy websockets
"""

import asyncio
import json
import threading
import time

from ibuddy import IBuddyDevice, IBuddyError, COLORS

import websockets.server
import websockets.asyncio.server


buddy = None
notify_active = False


def run_blocking(fn):
    def wrapper():
        try:
            fn()
        except Exception as e:
            print(f"[ibuddy] Thread error: {e}")
    t = threading.Thread(target=wrapper, daemon=True)
    t.start()


def try_reconnect():
    global buddy
    if buddy is None:
        try:
            buddy = IBuddyDevice()
            print("[ibuddy] i-Buddy reconnected!")
        except IBuddyError:
            pass


def handle_command(cmd_data):
    global notify_active
    if buddy is None:
        return {"ok": False, "error": "i-Buddy not connected"}

    c = cmd_data.get("cmd", "")
    print(f"[ibuddy] <- {json.dumps(cmd_data)}")

    if c == "color":
        color = cmd_data.get("color", "white")
        if color not in COLORS:
            return {"ok": False, "error": f"Unknown color: {color}"}
        buddy.head_color(color, cmd_data.get("duration", 0.3))
        return {"ok": True}

    elif c == "heart":
        on = cmd_data.get("on", True)
        buddy.heart(on, cmd_data.get("duration", 0.3))
        return {"ok": True}

    elif c == "flap":
        times = cmd_data.get("times", 3)
        buddy.flap(times)
        return {"ok": True}

    elif c == "wiggle":
        times = cmd_data.get("times", 3)
        buddy.wiggle(times)
        return {"ok": True}

    elif c == "heartbeat":
        times = cmd_data.get("times", 3)
        buddy.heartbeat(times)
        return {"ok": True}

    elif c == "reset":
        buddy.reset()
        return {"ok": True}

    elif c == "rainbow":
        times = cmd_data.get("times", 2)
        def do_rainbow():
            colors = ["red", "green", "blue", "cyan", "magenta", "yellow", "white"]
            for _ in range(times):
                for color in colors:
                    buddy.head_color(color, 0.15)
            buddy.reset()
        run_blocking(do_rainbow)
        return {"ok": True}

    elif c == "celebrate":
        def do_celebrate():
            colors = ["red", "green", "blue", "cyan", "magenta", "yellow", "white"]
            for _ in range(2):
                buddy.wiggle(1, delay=0.3)
                buddy.flap(1, delay=0.15)
                buddy.heartbeat(1, delay=0.2)
                for color in colors:
                    buddy.head_color(color, 0.1)
            buddy.reset()
        run_blocking(do_celebrate)
        return {"ok": True}

    elif c == "demo":
        run_blocking(buddy.demo)
        return {"ok": True}

    elif c == "notify":
        on = cmd_data.get("on", True)
        notify_active = on
        print(f"[ibuddy] NOTIFY {'ON' if on else 'OFF'}")
        if on:
            def do_notify():
                buddy.wiggle(2, delay=0.2)
                buddy.flap(3, delay=0.12)
                buddy.heart(True, duration=0.4)
                buddy.heart(False, duration=0.1)
            run_blocking(do_notify)
        else:
            run_blocking(lambda: buddy.heart(False, duration=0.1))
        return {"ok": True}

    elif c == "status":
        return {"ok": True, "notify_active": notify_active}

    else:
        return {"ok": False, "error": f"Unknown command: {c}"}


async def handler(websocket):
    global buddy
    print(f"[ibuddy] Client connected: {websocket.remote_address}")
    async for message in websocket:
        if buddy is None:
            try_reconnect()
        try:
            cmd_data = json.loads(message)
            response = handle_command(cmd_data)
            await websocket.send(json.dumps(response))
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"ok": False, "error": "Invalid JSON"}))
        except Exception as e:
            print(f"[ibuddy] Error handling command: {e}")
            await websocket.send(json.dumps({"ok": False, "error": str(e)}))
    print(f"[ibuddy] Client disconnected")


async def main():
    global buddy

    print("[ibuddy] Connecting to i-Buddy hardware...")
    try:
        buddy = IBuddyDevice()
        print("[ibuddy] i-Buddy connected!")
    except IBuddyError as e:
        print(f"[ibuddy] WARNING: {e}")
        print("[ibuddy] Starting server anyway - will retry on first command")
        buddy = None

    async with websockets.asyncio.server.serve(handler, "127.0.0.1", 8765):
        print("[ibuddy] WebSocket server running on ws://127.0.0.1:8765")
        print("[ibuddy] Waiting for Vencord plugin to connect...")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
`;

function getVencordDir(): string {
    const appData = process.env.APPDATA || "";
    return join(appData, "Vencord");
}

function installScript(): string {
    const vencordDir = getVencordDir();
    const scriptPath = join(vencordDir, "ibuddy_ws.py");

    if (!existsSync(vencordDir)) {
        mkdirSync(vencordDir, { recursive: true });
    }

    if (!existsSync(scriptPath)) {
        writeFileSync(scriptPath, IBUDDY_WS_PY, "utf-8");
        console.log("[iBuddy] Installed ibuddy_ws.py to", scriptPath);
    }

    return scriptPath;
}

export function getScriptPath(): string {
    return join(getVencordDir(), "ibuddy_ws.py");
}

export function startServer(
    _: IpcMainInvokeEvent,
    pythonPath: string,
    scriptPath: string
): { ok: boolean; error?: string } {
    if (serverProcess) {
        return { ok: true };
    }

    // Auto-install if no path provided
    if (!scriptPath) {
        scriptPath = installScript();
    }

    try {
        serverProcess = spawn(pythonPath, [scriptPath], {
            stdio: ["ignore", "pipe", "pipe"],
            detached: false,
        });

        serverProcess.stdout?.on("data", (data: Buffer) => {
            process.stdout.write(data);
        });
        serverProcess.stderr?.on("data", (data: Buffer) => {
            process.stderr.write(data);
        });
        serverProcess.on("close", () => {
            serverProcess = null;
        });
        serverProcess.on("error", () => {
            serverProcess = null;
        });

        return { ok: true };
    } catch (e: any) {
        return { ok: false, error: e.message };
    }
}

export function stopServer(_: IpcMainInvokeEvent): void {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
    }
}

export function isServerRunning(_: IpcMainInvokeEvent): boolean {
    return serverProcess !== null && !serverProcess.killed;
}
