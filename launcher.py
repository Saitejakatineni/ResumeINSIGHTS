"""
resumeINSIGHTS launcher — starts server and opens a standalone app window.
Works both from project folder (dev) and from inside .app bundle (installed).
"""
import subprocess
import sys
import os
import time
import urllib.request

# Support --resources flag passed by the .app shell script
RESOURCES = None
if "--resources" in sys.argv:
    idx = sys.argv.index("--resources")
    RESOURCES = sys.argv[idx + 1]

PROJECT  = RESOURCES or os.path.dirname(os.path.abspath(__file__))
PORT     = 8765
URL      = f"http://127.0.0.1:{PORT}"
CHROME   = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAVE    = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
APP_PROFILE = os.path.join(os.path.expanduser("~"), "Library",
                           "Application Support", "resumeINSIGHTS", "chrome-profile")


def start_server():
    python = os.path.join(PROJECT, "venv", "bin", "python")
    subprocess.Popen(
        [python, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "error"],
        cwd=PROJECT,
    )


def wait_for_server(timeout=20):
    for _ in range(timeout * 5):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def open_app_window():
    os.makedirs(APP_PROFILE, exist_ok=True)
    browser = CHROME if os.path.exists(CHROME) else \
              BRAVE  if os.path.exists(BRAVE)  else None
    if browser:
        subprocess.Popen([
            browser,
            f"--app={URL}",
            f"--user-data-dir={APP_PROFILE}",
            "--window-size=1300,860",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
        ])
    else:
        subprocess.Popen(["open", URL])


if __name__ == "__main__":
    start_server()
    if wait_for_server():
        open_app_window()
    else:
        subprocess.Popen(["osascript", "-e",
            'display alert "resumeINSIGHTS failed to start" message '
            '"Could not start the server. Try reinstalling the app."'])
        sys.exit(1)
