"""
resumeINSIGHTS launcher

Creates a native macOS app window (WKWebView) that loads the local FastAPI
server. No Chrome required. The app appears in the Dock like any normal Mac
app and quits cleanly when the window is closed.
"""

import os
import subprocess
import sys
import threading
import time
import urllib.request

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyRegular,
    NSBackingStoreBuffered,
    NSMakeRect,
    NSObject,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSURL, NSURLRequest
from WebKit import WKWebView, WKWebViewConfiguration

# ── Config ────────────────────────────────────────────────────────────────────

RESOURCES = None
if "--resources" in sys.argv:
    idx = sys.argv.index("--resources")
    RESOURCES = sys.argv[idx + 1]

PROJECT = RESOURCES or os.path.dirname(os.path.abspath(__file__))
PORT    = 8765
URL     = f"http://127.0.0.1:{PORT}"

# ── Server ────────────────────────────────────────────────────────────────────

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

# ── Native window ─────────────────────────────────────────────────────────────

class AppDelegate(NSObject):
    """
    NSApplication delegate.
    - Owns the server process and WKWebView window.
    - Shuts down the server when the window closes.
    """

    def initWithServerProc_(self, server_proc):
        self = objc.super(AppDelegate, self).init()
        if self is None:
            return None
        self._server_proc = server_proc
        self._window      = None
        self._webview     = None
        return self

    def applicationDidFinishLaunching_(self, notification):
        self._build_window()
        self._load_url(URL)

    def _build_window(self):
        style = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskMiniaturizable
            | NSWindowStyleMaskResizable
        )
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 1300, 860),
            style,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_("resumeINSIGHTS")
        self._window.center()
        self._window.setDelegate_(self)

        cfg = WKWebViewConfiguration.alloc().init()
        self._webview = WKWebView.alloc().initWithFrame_configuration_(
            self._window.contentView().bounds(),
            cfg,
        )
        self._webview.setAutoresizingMask_(18)  # width + height flexible
        self._window.contentView().addSubview_(self._webview)
        self._window.makeKeyAndOrderFront_(None)

    def _load_url(self, url_string: str):
        ns_url     = NSURL.URLWithString_(url_string)
        ns_request = NSURLRequest.requestWithURL_(ns_url)
        self._webview.loadRequest_(ns_request)

    # Called when the red X is clicked
    def windowWillClose_(self, notification):
        self._shutdown()

    # Called when all windows are closed
    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        return True

    def applicationWillTerminate_(self, notification):
        self._shutdown()

    def _shutdown(self):
        if self._server_proc and self._server_proc.poll() is None:
            self._server_proc.terminate()
            self._server_proc.wait()

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    # Start the FastAPI server in the background before the UI launches
    server_proc = start_server()

    if not wait_for_server():
        subprocess.Popen([
            "osascript", "-e",
            'display alert "resumeINSIGHTS" message '
            '"Could not start the server. Try reinstalling the app."',
        ])
        server_proc.terminate()
        sys.exit(1)

    # Boot NSApplication
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    # Set the dock icon if the .icns is bundled
    icns_path = os.path.join(PROJECT, "..", "Resources", "AppIcon.icns")
    if os.path.exists(icns_path):
        from AppKit import NSImage
        icon = NSImage.alloc().initWithContentsOfFile_(icns_path)
        if icon:
            app.setApplicationIconImage_(icon)

    delegate = AppDelegate.alloc().initWithServerProc_(server_proc)
    app.setDelegate_(delegate)
    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == "__main__":
    main()
