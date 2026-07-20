import { IpcMainInvokeEvent } from "electron";
import { ChildProcess, spawn } from "child_process";

let serverProcess: ChildProcess | null = null;

export function startServer(
    _: IpcMainInvokeEvent,
    pythonPath: string,
    scriptPath: string
): { ok: boolean; error?: string } {
    if (serverProcess) {
        return { ok: true };
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
