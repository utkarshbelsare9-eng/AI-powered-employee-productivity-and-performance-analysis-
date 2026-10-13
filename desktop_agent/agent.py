"""
Cross-platform desktop activity collector.

IMPORTANT:
- Counts keyboard activity but never records actual key values.
- Counts mouse movement/click/scroll activity.
- Records active application/process name only where available.
- Sends one aggregate interval every 60 seconds.
"""
import os
import sys
import time
import threading
import platform
import urllib.request
import json

try:
    from pynput import keyboard, mouse
except ImportError:
    print("Missing dependency: pynput. Run: pip install -r requirements.txt")
    raise

SERVER = os.environ.get("PRODUCTIVITY_AI_SERVER", "http://127.0.0.1:5000").rstrip("/")
TOKEN = os.environ.get("PRODUCTIVITY_AI_AGENT_TOKEN", "").strip()
INTERVAL = 60

lock = threading.Lock()
stats = {
    "keyboard_events": 0,
    "mouse_moves": 0,
    "mouse_clicks": 0,
    "scroll_events": 0,
}
last_input = time.monotonic()


def bump(name):
    global last_input
    with lock:
        stats[name] += 1
        last_input = time.monotonic()


def on_key(_key):
    # Do not inspect/store _key: only count the event.
    bump("keyboard_events")


def on_move(_x, _y):
    bump("mouse_moves")


def on_click(_x, _y, _button, pressed):
    if pressed:
        bump("mouse_clicks")


def on_scroll(_x, _y, _dx, _dy):
    bump("scroll_events")


def active_application():
    system = platform.system()
    try:
        if system == "Windows":
            import ctypes
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if not pid.value:
                return None
            import psutil
            return psutil.Process(pid.value).name()[:120]

        if system == "Darwin":
            import subprocess
            out = subprocess.check_output(
                ["osascript", "-e",
                 'tell application "System Events" to get name of first application process whose frontmost is true'],
                text=True, timeout=2
            )
            return out.strip()[:120] or None

        if system == "Linux":
            import subprocess
            out = subprocess.check_output(
                ["bash", "-lc", "xdotool getactivewindow getwindowpid 2>/dev/null"],
                text=True, timeout=2
            ).strip()
            if out:
                import psutil
                return psutil.Process(int(out)).name()[:120]
    except Exception:
        pass
    return None


def snapshot_and_reset():
    with lock:
        payload = dict(stats)
        for k in stats:
            stats[k] = 0
        idle = int(min(INTERVAL, max(0, time.monotonic() - last_input)))
    return payload, idle


def send(payload):
    if not TOKEN:
        print("Set PRODUCTIVITY_AI_AGENT_TOKEN before starting the agent.")
        return

    body = json.dumps({
        "mouse_events": payload["mouse_moves"] + payload["mouse_clicks"] + payload["scroll_events"],
        "keyboard_events": payload["keyboard_events"],
        "mouse_clicks": payload["mouse_clicks"],
        "mouse_moves": payload["mouse_moves"],
        "scroll_events": payload["scroll_events"],
        "idle_seconds": payload["idle_seconds"],
        "active_application": active_application(),
        "interval_seconds": INTERVAL,
    }).encode("utf-8")

    req = urllib.request.Request(
        SERVER + "/api/activity/agent/ping",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + TOKEN,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"[OK] {result.get('date')} active={result.get('total_active_hours', 0):.2f}h")
    except Exception as exc:
        print("[WARN] Could not send activity:", exc)


def main():
    if not TOKEN:
        print("No PRODUCTIVITY_AI_AGENT_TOKEN configured.")
        print("Generate one from Settings → Desktop Activity Tracker.")
        sys.exit(1)

    print("ProductivityAI desktop activity agent started.")
    print("Privacy mode: counts only; no key values, typed text, clipboard, screenshots, or window titles.")

    kb = keyboard.Listener(on_press=on_key)
    ms = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    kb.start()
    ms.start()

    try:
        while True:
            time.sleep(INTERVAL)
            data, idle = snapshot_and_reset()
            data["idle_seconds"] = idle
            send(data)
    except KeyboardInterrupt:
        pass
    finally:
        kb.stop()
        ms.stop()


if __name__ == "__main__":
    main()
