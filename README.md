# resumeINSIGHTS

An AI-powered Mac desktop app that analyzes your resume against any job description — giving you an ATS score, keyword gaps, grade, and ready-to-paste rewrites to help you reach 97%+ match.

Built with **Claude Sonnet** (Anthropic AI) · **FastAPI** · **SQLite** · runs as a native-feeling window via Chrome app mode.

---

## Features

- **Match %** — skills + experience overlap with the job description
- **ATS Score** — keyword density, formatting parseability, section structure
- **Overall Grade** — A+ to F combined rating
- **Clickable score cards** — each opens a detail panel with score breakdown, what's hurting it, and a step-by-step guide to improve
- **Git-style diff** — red/green rewrites showing exactly what line to change and why
- **Lines to Add** — ready-to-paste bullet points with the target section
- **Keywords tab** — matching vs missing keywords with a coverage bar
- **Format & ATS tab** — formatting tips + why ATS systems reject resumes
- **Report tab** — consolidated printable summary of all results
- **Analysis history** — every run saved locally; revisit without re-uploading
- **Tech log** — animated analysis log shown during processing
- **Test mode** — verify the UI works without spending any API credits
- **Cost tracking** — token count and estimated cost shown after each real analysis

---

## Screenshots

> Upload your resume (PDF or DOCX), paste the job description, click Analyze.

The app opens as a standalone window (no browser tabs or address bar).

---

## Setup

### Prerequisites

- macOS 11+
- Python 3.10+
- Google Chrome or Brave Browser
- An [Anthropic API key](https://console.anthropic.com)

### Install & run (developer mode)

```bash
# 1. Clone the repo
git clone https://github.com/Saitejakatineni/ResumeINSIGHTS.git
cd ResumeINSIGHTS

# 2. Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env
# Edit .env and paste your key: ANTHROPIC_API_KEY=sk-ant-...

# 4. Launch
python launcher.py
```

This starts the FastAPI server on port 8765 and opens a Chrome app-mode window (no address bar — feels like a native app).

To stop: `pkill -f "uvicorn main:app"`

### Run in browser (without launcher)

```bash
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8765
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

---

## Build the Mac Desktop App (.dmg)

```bash
# 1. Make sure venv is set up (see above)
# 2. Create the .app bundle structure
mkdir -p resumeINSIGHTS.app/Contents/{MacOS,Resources}

# Copy source files into bundle
cp main.py launcher.py requirements.txt resumeINSIGHTS.app/Contents/Resources/
cp -R static resumeINSIGHTS.app/Contents/Resources/
cp -R venv   resumeINSIGHTS.app/Contents/Resources/

# Write the shell-script launcher
cat > resumeINSIGHTS.app/Contents/MacOS/resumeINSIGHTS << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESOURCES="$SCRIPT_DIR/../Resources"
source "$RESOURCES/venv/bin/activate"
DATA_DIR="$HOME/Library/Application Support/resumeINSIGHTS"
mkdir -p "$DATA_DIR"
export RESUMEINSIGHTS_DB="$DATA_DIR/history.db"
export RESUMEINSIGHTS_STATIC="$RESOURCES/static"
export RESUMEINSIGHTS_ENV="$DATA_DIR/.env"
# Copy .env from project if not yet set up in Application Support
[ ! -f "$RESUMEINSIGHTS_ENV" ] && cp "$RESOURCES/../../../.env" "$RESUMEINSIGHTS_ENV" 2>/dev/null || true
exec python "$RESOURCES/launcher.py" --resources "$RESOURCES"
EOF
chmod +x resumeINSIGHTS.app/Contents/MacOS/resumeINSIGHTS

# Write Info.plist
cat > resumeINSIGHTS.app/Contents/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundleExecutable</key><string>resumeINSIGHTS</string>
  <key>CFBundleIdentifier</key><string>com.user.resumeinsights</string>
  <key>CFBundleName</key><string>resumeINSIGHTS</string>
  <key>CFBundleDisplayName</key><string>resumeINSIGHTS</string>
  <key>CFBundleVersion</key><string>2.0.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
  <key>NSPrincipalClass</key><string>NSApplication</string>
</dict>
</plist>
EOF

# 3. Package into DMG
rm -rf /tmp/dmg-staging && mkdir /tmp/dmg-staging
cp -R resumeINSIGHTS.app /tmp/dmg-staging/
ln -s /Applications /tmp/dmg-staging/Applications
hdiutil create -volname "resumeINSIGHTS" -srcfolder /tmp/dmg-staging -ov -format UDZO resumeINSIGHTS.dmg
```

**Install the DMG:**
1. Double-click `resumeINSIGHTS.dmg`
2. Drag `resumeINSIGHTS` → `Applications`
3. Eject the DMG
4. Open from Launchpad or Applications
5. **First launch:** right-click → Open (to bypass Gatekeeper) — only needed once

**API key in the installed app:**
Place your `.env` file at:
```
~/Library/Application Support/resumeINSIGHTS/.env
```
Contents:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## API Key

Get yours at [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key.

Copy `.env.example` to `.env` and paste your key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Never commit `.env` — it is in `.gitignore`.**

---

## Cost

Uses `claude-sonnet-4-6` — optimal balance of quality and cost for structured JSON output.

| | Cost |
|---|---|
| Per analysis | ~$0.02–0.04 |
| $5 credit | ~150–200 analyses |
| $10 credit | ~300–400 analyses |

Cost is displayed after every real analysis. Test mode costs $0.

---

## Project Structure

```
ResumeINSIGHTS/
├── main.py            # FastAPI backend · Claude API · SQLite history
├── launcher.py        # Starts uvicorn + opens Chrome app-mode window
├── requirements.txt   # Python dependencies
├── .env.example       # API key template (copy to .env)
└── static/
    └── index.html     # Full frontend — HTML + CSS + JS (single file)
```

---

## How It Works

```
Resume (PDF/DOCX)  +  Job Description (text)
              │
              ▼
       FastAPI (main.py)
              │
              ▼
    Claude Sonnet API
    (structured JSON analysis)
              │
              ▼
   SQLite (history.db) — stored locally
              │
              ▼
   Chrome --app window (launcher.py)
   renders static/index.html
```

- **PDF** resumes → sent to Claude as base64 (native PDF understanding, no text extraction needed)
- **DOCX** resumes → text extracted via `python-docx`, then sent as plain text
- All history stored locally in `history.db` — never sent anywhere except Anthropic's API for analysis

---

## Troubleshooting

**"Cannot reach the server"** — The server isn't running. Launch via `python launcher.py` or start uvicorn manually.

**"Failed to parse analysis JSON"** — Rare; the model response was malformed. Try again.

**"Your credit balance is too low"** — Add credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing).

**App opens a browser tab instead of its own window** — Chrome must be installed. If Chrome is already open, it may reuse the session; the isolated `--user-data-dir` in `launcher.py` prevents this in most cases.

**Gatekeeper blocks the app** — Right-click → Open → Open. Only needed on first launch.

---

## Dependencies

```
fastapi            — web framework
uvicorn[standard]  — ASGI server
anthropic          — Claude API client
python-docx        — DOCX text extraction
python-dotenv      — .env file loading
python-multipart   — multipart file upload support
Pillow             — icon generation (build only)
```
