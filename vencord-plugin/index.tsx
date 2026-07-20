import { definePluginSettings } from "@api/Settings";
import { ChannelStore, MediaEngineStore, UserStore, VoiceStateStore } from "@webpack/common";
import definePlugin, { PluginNative, OptionType } from "@utils/types";

const Native = VencordNative.pluginHelpers.iBuddy as PluginNative<typeof import("./native")>;

const settings = definePluginSettings({
    wsUrl: {
        type: OptionType.STRING,
        description: "WebSocket server URL",
        default: "ws://127.0.0.1:8765",
    },
    pythonPath: {
        type: OptionType.STRING,
        description: "Path to python.exe",
        default: "python",
    },
    scriptPath: {
        type: OptionType.STRING,
        description: "Path to ibuddy_ws.py",
        default: "",
    },
    autoStartServer: {
        type: OptionType.BOOLEAN,
        description: "Auto-start the Python WebSocket server when Discord loads",
        default: true,
    },
    messageNotifications: {
        type: OptionType.BOOLEAN,
        description: "Notify on new DMs (flap + swivel + heartbeat)",
        default: true,
    },
    priorityContacts: {
        type: OptionType.STRING,
        description: "Comma-separated user IDs — heartbeat when they come online",
        default: "",
    },
});

const TAG = "[iBuddy]";
let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let lastMute: boolean | null = null;
let lastDeaf: boolean | null = null;
let connectedOnce = false;

// Message notification debouncing
let messageNotifyTimer: ReturnType<typeof setTimeout> | null = null;

// Priority contact tracking
const onlineUsers = new Set<string>();
const alertedContacts = new Set<string>();

function sendCmd(cmd: object) {
    try {
        if (ws?.readyState === WebSocket.OPEN) {
            const json = JSON.stringify(cmd);
            console.log(TAG, ">>>", json);
            ws.send(json);
        }
    } catch (e) {
        console.error(TAG, "send error:", e);
    }
}

function isInVoice(): boolean {
    try {
        const me = UserStore.getCurrentUser();
        if (!me) return false;
        const vs = VoiceStateStore.getVoiceStateForUser(me.id);
        return vs != null;
    } catch {
        return false;
    }
}

function checkState() {
    try {
        if (!isInVoice()) {
            if (lastMute !== null || lastDeaf !== null) {
                sendCmd({ cmd: "reset" });
            }
            lastMute = null;
            lastDeaf = null;
            return;
        }
        const muted = MediaEngineStore.isSelfMute();
        const deafened = MediaEngineStore.isSelfDeaf();
        if (muted === lastMute && deafened === lastDeaf) return;
        lastMute = muted;
        lastDeaf = deafened;
        console.log(TAG, "muted=" + muted, "deafened=" + deafened);
        if (deafened) sendCmd({ cmd: "color", color: "blue" });
        else if (muted) sendCmd({ cmd: "color", color: "red" });
        else sendCmd({ cmd: "color", color: "green" });
    } catch (e) {
        console.error(TAG, "checkState error:", e);
    }
}

function handleMessageCreate({ message, optimistic }: { message: any; optimistic: boolean }) {
    if (!settings.store.messageNotifications) return;
    if (optimistic) return;

    // Ignore our own messages
    const me = UserStore.getCurrentUser();
    if (!me || message.author?.id === me.id) return;

    // Only DMs (channel type 1)
    const channel = ChannelStore.getChannel(message.channel_id);
    if (!channel || channel.type !== 1) return;

    console.log(TAG, `DM from ${message.author?.username || "unknown"}`);

    // Debounce: batch rapid messages into one notification
    if (messageNotifyTimer) clearTimeout(messageNotifyTimer);
    messageNotifyTimer = setTimeout(() => {
        sendCmd({ cmd: "notify", on: true });
        messageNotifyTimer = null;
    }, 3000);
}

function getPriorityContactIds(): Set<string> {
    const raw = settings.store.priorityContacts || "";
    return new Set(
        raw.split(",").map(s => s.trim()).filter(s => /^\d+$/.test(s))
    );
}

function handlePresenceUpdate({ updates }: { updates: Array<{ user: { id: string }; status: string }> }) {
    const contactIds = getPriorityContactIds();
    if (contactIds.size === 0) return;

    for (const update of updates) {
        const userId = update.user.id;
        const status = update.status;
        if (!contactIds.has(userId)) continue;

        const wasOnline = onlineUsers.has(userId);
        const isOnline = status === "online";

        if (isOnline) onlineUsers.add(userId);
        else onlineUsers.delete(userId);

        // Transition offline -> online and not yet alerted
        if (isOnline && !wasOnline && !alertedContacts.has(userId)) {
            alertedContacts.add(userId);
            console.log(TAG, `Priority contact ${userId} came online — heartbeat`);
            sendCmd({ cmd: "heartbeat", times: 3 });
        }

        // Reset alert when contact goes offline
        if (!isOnline) {
            alertedContacts.delete(userId);
        }
    }
}

function connectWs() {
    if (ws) return;
    try {
        ws = new WebSocket(settings.store.wsUrl);
        ws.onopen = () => {
            console.log(TAG, "Connected to server");
            if (!connectedOnce) {
                connectedOnce = true;
                sendCmd({ cmd: "flap", times: 2 });
            }
        };
        ws.onclose = () => { ws = null; reconnectTimer = setTimeout(connectWs, 5000); };
        ws.onerror = () => ws?.close();
    } catch (e) {
        console.error(TAG, "connect error:", e);
        reconnectTimer = setTimeout(connectWs, 5000);
    }
}

export default definePlugin({
    name: "iBuddy",
    description: "Controls i-Buddy: mute/deafen colors, DM notifications, priority contact alerts",
    tags: ["i-buddy"],
    authors: [{ name: "DJche", id: 0n }],
    settings,

    settingsAboutComponent: () => {
        return (
            <button
                onClick={() => {
                    sendCmd({ cmd: "wiggle", times: 2 });
                    setTimeout(() => sendCmd({ cmd: "flap", times: 3 }), 1200);
                    setTimeout(() => sendCmd({ cmd: "heartbeat", times: 3 }), 2000);
                }}
                style={{
                    padding: "8px 16px",
                    borderRadius: "4px",
                    border: "none",
                    background: "#5865f2",
                    color: "white",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: "bold",
                }}
            >
                Test i-Buddy
            </button>
        );
    },

    flux: {
        MEDIA_ENGINE_DEVICES: checkState,
        VOICE_STATE_UPDATES: checkState,
        MESSAGE_CREATE: handleMessageCreate,
        PRESENCE_UPDATES: handlePresenceUpdate,
    },

    async start() {
        lastMute = null;
        lastDeaf = null;
        connectedOnce = false;
        onlineUsers.clear();
        alertedContacts.clear();

        if (settings.store.autoStartServer) {
            const result = await Native.startServer(
                settings.store.pythonPath,
                settings.store.scriptPath
            );
            if (result.ok) console.log(TAG, "Server started");
            else console.error(TAG, "Failed to start server:", result.error);
        }

        connectWs();
        setTimeout(checkState, 2000);
    },

    stop() {
        if (reconnectTimer) clearTimeout(reconnectTimer);
        if (messageNotifyTimer) clearTimeout(messageNotifyTimer);
        ws?.close();
        ws = null;
        lastMute = null;
        lastDeaf = null;
        connectedOnce = false;
        messageNotifyTimer = null;
        onlineUsers.clear();
        alertedContacts.clear();
    },
});
