"""
resumeINSIGHTS launcher — starts the FastAPI server and opens a standalone
app window using Chrome's --app mode (no address bar, no tabs).

The server is automatically shut down when the app window is closed.
Works from the project folder (dev) and from inside the .app bundle (installed).
"""

import os
import subprocess
import sys
import time
import urllib.request

# ── Config ────────────────────────────────────────────────────────────────────

# --resources flag is passed by the .app shell script so paths resolve
# correctly regardless of where the app is installed.
RESOURCES = None
if "--resources" in sys.argv:
    idx = sys.argv.index("--resources")
    RESOURCES = sys.argv[idx + 1]

PROJECT = RESOURCES or os.path.dirname(os.path.abspath(__file__))
PORT    = 8765
URL     = f"http://127.0.0.1:{PORT}"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAVE  = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

# Isolated Chrome profile so the app window is separate from the user's
# normal browser session.
APP_PROFILE = os.path.join(
    os.path.expanduser("~"),
    "Library", "Application Support", "resumeINSIGHTS", "chrome-profile",
)

# ── Server ────────────────────────────────────────────────────────────────────

def start_server() -> subprocess.Popen:
    python = os.path.join(PROJECT, "venv", "bin", "python")
    return subprocess.Popen(
        [python, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "error"],
        cwd=PROJECT,
    )


def wait_for_server(timeout: int = 20) -> bool:
    """Poll the server until it responds or the timeout is reached."""
    for _ in range(timeout * 5):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False

# ── Browser window ────────────────────────────────────────────────────────────

def open_app_window() -> subprocess.Popen | None:
    """
    Open the app in Chrome/Brave app mode (no address bar, no tabs).
    Returns the browser process, or None if only 'open' was available.
    """
    os.makedirs(APP_PROFILE, exist_ok=True)

    browser = (
        CHROME if os.path.exists(CHROME) else
        BRAVE  if os.path.exists(BRAVE)  else
        None
    )

    if browser:
        return subprocess.Popen([
            browser,
            f"--app={URL}",
            f"--user-data-dir={APP_PROFILE}",
            "--window-size=1300,860",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
        ])

    # Fallback: open in default browser (no auto-shutdown support)
    subprocess.Popen(["open", URL])
    return None

# ── Main ──────────────────────────────────────────────────────────────────────

def show_error_dialog(message: str) -> None:
    subprocess.Popen([
        "osascript", "-e",
        f'display alert "resumeINSIGHTS failed to start" message "{message}"',
    ])


if __name__ == "__main__":
    server_proc = start_server()

    if not wait_for_server():
        show_error_dialog("Could not start the server. Try reinstalling the app.")
        server_proc.terminate()
        sys.exit(1)

    browser_proc = open_app_window()

    if browser_proc is not None:
        # Block until the user closes the app window, then shut down the server.
        browser_proc.wait()
        server_proc.terminate()
        server_proc.wait()
    else:
        # Fallback mode (no browser process to track) — keep server alive
        # until the user manually kills it or closes the terminal.
        try:
            server_proc.wait()
        except KeyboardInterrupt:
            server_proc.terminate()
