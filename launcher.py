"""
resumeINSIGHTS launcher

Starts the FastAPI server, opens a Chrome app-mode window, and shows a
menu bar icon (top-right macOS bar) with Open / Quit controls.

Quitting from the menu bar — or closing the Chrome window — automatically
shuts down the server. No manual pkill needed.
"""

import os
import subprocess
import sys
import threading
import time
import urllib.request

import rumps

# ── Config ────────────────────────────────────────────────────────────────────

RESOURCES = None
if "--resources" in sys.argv:
    idx = sys.argv.index("--resources")
    RESOURCES = sys.argv[idx + 1]

PROJECT = RESOURCES or os.path.dirname(os.path.abspath(__file__))
PORT    = 8765
URL     = f"http://127.0.0.1:{PORT}"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAVE  = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

APP_PROFILE = os.path.join(
    os.path.expanduser("~"),
    "Library", "Application Support", "resumeINSIGHTS", "chrome-profile",
)

# ── Server helpers ────────────────────────────────────────────────────────────

def start_server() -> subprocess.Popen:
    python = os.path.join(PROJECT, "venv", "bin", "python")
    return subprocess.Popen(
        [python, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "error"],
        cwd=PROJECT,
    )


def wait_for_server(timeout: int = 20) -> bool:
    for _ in range(timeout * 5):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def open_browser_window() -> subprocess.Popen | None:
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
    subprocess.Popen(["open", URL])
    return None

# ── Menu bar app ──────────────────────────────────────────────────────────────

class ResumeInsightsApp(rumps.App):
    """
    Menu bar icon for resumeINSIGHTS.
    Appears as 'rI' in the top-right macOS menu bar.
    Provides Open and Quit controls.
    """

    def __init__(self):
        super().__init__("rI", quit_button=None)
        self.menu = [
            rumps.MenuItem("Open resumeINSIGHTS", callback=self.open_window),
            None,                                               # separator
            rumps.MenuItem("Quit resumeINSIGHTS", callback=self.quit_app),
        ]
        self._server_proc:  subprocess.Popen | None = None
        self._browser_proc: subprocess.Popen | None = None

    # ── Startup ───────────────────────────────────────────────────────────────

    def launch(self) -> None:
        """Called in a background thread immediately after the menu bar starts."""
        self._server_proc = start_server()

        if not wait_for_server():
            rumps.alert(
                title="resumeINSIGHTS",
                message="Could not start the server. Try reinstalling the app.",
            )
            self._shutdown()
            return

        self._browser_proc = open_browser_window()

        # Watch for the Chrome window closing
        if self._browser_proc:
            self._browser_proc.wait()
            # Window was closed by the user — shut everything down
            self._shutdown()

    # ── Menu actions ──────────────────────────────────────────────────────────

    def open_window(self, _) -> None:
        """Re-open the app window if it was closed."""
        self._browser_proc = open_browser_window()
        if self._browser_proc:
            threading.Thread(target=self._watch_browser, daemon=True).start()

    def quit_app(self, _) -> None:
        """Terminate browser + server then exit the menu bar app."""
        if self._browser_proc and self._browser_proc.poll() is None:
            self._browser_proc.terminate()
        self._shutdown()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _watch_browser(self) -> None:
        """Background thread: shut down when the browser window closes."""
        if self._browser_proc:
            self._browser_proc.wait()
            self._shutdown()

    def _shutdown(self) -> None:
        if self._server_proc and self._server_proc.poll() is None:
            self._server_proc.terminate()
            self._server_proc.wait()
        rumps.quit_application()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    menu_app = ResumeInsightsApp()

    # Start server + browser in background so the menu bar appears immediately
    t = threading.Thread(target=menu_app.launch, daemon=True)
    t.start()

    menu_app.run()
