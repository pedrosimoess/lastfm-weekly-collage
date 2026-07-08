# tapmusic-collage

Automatically generates a weekly Last.fm album collage using [tapmusic.net](https://tapmusic.net) and saves it locally. No browser automation — just a direct HTTP request.

**macOS bonus:** imports to the Photos app and syncs to iCloud Drive so the image appears on your iPhone.

---

## Features

- Downloads a 3×3 (or any size) album collage for any Last.fm user
- Saves images to `Imagens/` with date-stamped filenames (`tapmusic_YYYY-MM-DD.png`)
- Works on **macOS, Windows, and Linux**
- On **macOS**: also imports to the Photos app and copies to iCloud Drive (`~/iCloud Drive/Tapmusic/`)
- Checks free disk space before downloading, so a full disk fails fast instead of mid-run
- Retries transient download failures with exponential backoff, and validates that what was downloaded is actually a well-formed PNG
- Zero external dependencies — Python standard library only

---

## Requirements

- Python 3.8+
- A [Last.fm](https://www.last.fm) account with listening history

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/tapmusic-collage.git
cd tapmusic-collage

# 2. Edit tapmusic.py — change USERNAME to your Last.fm username
#    (and optionally PERIOD, SIZE, CAPTIONS, PLAYCOUNT)

# 3. Run
python tapmusic.py
```

The image is saved to `Imagens/tapmusic_YYYY-MM-DD.png`.

---

## Configuration

Open `tapmusic.py` and edit the block at the top:

| Variable                      | Default       | Options                                                          |
|--------------------------------|---------------|-------------------------------------------------------------------|
| `USERNAME`                    | `"pedrosexo"` | your Last.fm username                                            |
| `PERIOD`                      | `"7day"`      | `7day` · `1month` · `3month` · `6month` · `12month` · `overall` |
| `SIZE`                        | `"3x3"`       | `3x3` · `4x4` · `5x5` · `10x10`                                 |
| `CAPTIONS`                    | `False`       | `True` to show album/artist names                                |
| `PLAYCOUNT`                   | `False`       | `True` to show play counts                                       |
| `SAVE_TO_PHOTOS` (macOS)       | `True`        | import each collage into Photos                                  |
| `PHOTOS_IMPORT_TIMEOUT_SECS`  | `60`          | seconds to wait for Photos before giving up (Photos can be slow to cold-start) |
| `PHOTOS_IMPORT_RETRIES`       | `2`           | total attempts to import into Photos                              |
| `SAVE_TO_ICLOUD` (macOS)       | `True`        | copy each collage to iCloud Drive                                 |
| `SAVE_TO_CUSTOM` / `CUSTOM_PATH` | `False` / `""` | copy to any extra folder (any OS)                              |
| `MIN_FREE_SPACE_MB`            | `100`         | abort before downloading if free disk space drops below this      |
| `DOWNLOAD_RETRIES`             | `3`           | download attempts before giving up                                |
| `RETRY_BACKOFF_SECS`           | `5`           | base retry delay in seconds; doubles each attempt (5s, 10s, 20s…) |

---

## Reliability notes

- Before downloading, the script checks free disk space (`MIN_FREE_SPACE_MB`). If there isn't enough room, it fails immediately instead of wasting download retries.
- The download step validates both the HTTP `Content-Type` and the actual PNG file signature/size, so a truncated or non-image response (e.g. an HTML error page from tapmusic.net) is treated as a retry-worthy failure rather than silently saved.
- DNS/connectivity errors are called out explicitly in the log so it's clear when the problem is "no internet" rather than a bad response from the server.
- The final log line reflects what actually happened: `RESULT: OK` only if every enabled step succeeded, `RESULT: PARTIAL` if the collage itself was downloaded but an optional step (Photos import, iCloud copy, custom copy) failed, `RESULT: FAIL` if the download itself failed.

---

## Scheduling

### macOS — launchd (runs every Friday at 9:00 AM)

```bash
# 1. Edit the .plist to match your paths (Python path + script path)
nano agendamento/macos/com.pedro.tapmusic.plist

# 2. Install
cp agendamento/macos/com.pedro.tapmusic.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pedro.tapmusic.plist

# 3. Verify
launchctl list | grep tapmusic

# Run manually for testing
launchctl start com.pedro.tapmusic
```

To uninstall:
```bash
launchctl unload ~/Library/LaunchAgents/com.pedro.tapmusic.plist
rm ~/Library/LaunchAgents/com.pedro.tapmusic.plist
```

> **Tip:** if you use a virtual environment, set `ProgramArguments[0]` in the plist
> to the venv Python, e.g. `/Users/you/tapmusic-env/bin/python`.

---

### Windows — Task Scheduler

**Option A — import via GUI:**
1. Edit `agendamento/windows/tapmusic_task.xml`: replace `C:\path\to\LastfmAutomacao` with your actual path.
2. Open Task Scheduler → Action → **Import Task…** → select the XML file.

**Option B — import via PowerShell (run as Administrator):**
```powershell
Register-ScheduledTask `
  -Xml (Get-Content agendamento\windows\tapmusic_task.xml | Out-String) `
  -TaskName "tapmusic" -Force
```

The `.bat` wrapper at `agendamento/windows/tapmusic.bat` can be used as the task's action if you prefer to point Task Scheduler at a batch file instead.

---

### Linux — cron

```bash
crontab -e
```

Add this line (runs every Friday at 9:00 AM):
```
0 9 * * 5 /usr/bin/python3 /path/to/LastfmAutomacao/tapmusic.py >> /path/to/LastfmAutomacao/Logs/tapmusic.log 2>&1
```

---

## Folder Structure

```
tapmusic-collage/
├── tapmusic.py                   # main script
├── requirements.txt
├── .gitignore
├── Imagens/                      # generated collages (git-ignored)
│   └── tapmusic_YYYY-MM-DD.png
├── Logs/                         # execution logs (git-ignored)
│   └── tapmusic.log
└── agendamento/
    ├── macos/
    │   └── com.pedro.tapmusic.plist   # launchd agent
    └── windows/
        ├── tapmusic.bat               # batch wrapper
        └── tapmusic_task.xml          # Task Scheduler definition
```

---

## macOS — iCloud Drive path

The script copies the image to:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Tapmusic/
```
which appears as `iCloud Drive/Tapmusic/` in Finder and syncs to your iPhone automatically.

---

## License

MIT
