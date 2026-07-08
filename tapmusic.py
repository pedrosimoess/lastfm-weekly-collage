"""
tapmusic.py — Last.fm weekly album collage generator via tapmusic.net
Usage: python tapmusic.py
Output: always saves to Imagens/; optional destinations configured below
"""

import urllib.request
import subprocess
import shutil
import os
import sys
import time
import logging
import platform
from logging.handlers import RotatingFileHandler
from datetime import datetime

# ─── Last.fm settings ─────────────────────────────────────────────────────────
USERNAME  = "pedrosexo"   # your Last.fm username
PERIOD    = "7day"        # 7day | 1month | 3month | 6month | 12month | overall
SIZE      = "3x3"         # 3x3 | 4x4 | 5x5 | 10x10
CAPTIONS  = False         # show album/artist name on collage
PLAYCOUNT = False         # show play count on collage

# ─── Destination settings ─────────────────────────────────────────────────────
# Images are always saved to Imagens/ (next to this script).
# Enable extra destinations below as needed.

# macOS — import into the Photos app (may time out if Mac is locked)
SAVE_TO_PHOTOS = True

# macOS — copy to iCloud Drive so the image syncs to iPhone
SAVE_TO_ICLOUD = True
ICLOUD_FOLDER  = os.path.expanduser(
    "~/Library/Mobile Documents/com~apple~CloudDocs/Tapmusic"
)

# Any OS — copy to a custom folder (OneDrive, NAS, external drive, etc.)
# Set SAVE_TO_CUSTOM = True and fill in CUSTOM_PATH to enable.
SAVE_TO_CUSTOM = False
CUSTOM_PATH    = ""
# Examples:
#   macOS/Linux : "/Users/you/Pictures/Tapmusic"
#   Windows     : r"C:\Users\you\OneDrive\Tapmusic"
# ──────────────────────────────────────────────────────────────────────────────

# ─── Retry settings ────────────────────────────────────────────────────────────
DOWNLOAD_RETRIES     = 3     # attempts for the collage download step
RETRY_BACKOFF_SECS   = 5     # base delay between retries (doubles each attempt)
# ──────────────────────────────────────────────────────────────────────────────

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "Imagens")
LOGS_DIR   = os.path.join(BASE_DIR, "Logs")
IS_MACOS   = platform.system() == "Darwin"

LOG_FILE = os.path.join(LOGS_DIR, "tapmusic.log")


def setup_logger():
    """Configure logging with timestamps, console output, and log rotation."""
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger("tapmusic")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        # Avoid duplicate handlers if run() is called more than once in-process.
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler: caps the log at ~2MB, keeps 3 backups
    # (tapmusic.log, tapmusic.log.1, tapmusic.log.2, tapmusic.log.3)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # Also mirror to stdout so launchd/manual runs still show live output.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


def run():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    log = setup_logger()

    log.info("=" * 60)
    log.info("Run started")

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"tapmusic_{date_str}.png"
    output   = os.path.join(IMAGES_DIR, filename)

    caption_val   = "1" if CAPTIONS  else "0"
    playcount_val = "1" if PLAYCOUNT else "0"

    url = (
        f"https://tapmusic.net/collage.php"
        f"?user={USERNAME}&type={PERIOD}&size={SIZE}"
        f"&caption={caption_val}&playcount={playcount_val}"
    )

    log.info(f"→ Generating collage for '{USERNAME}' ({PERIOD}, {SIZE})...")
    log.info(f"→ URL: {url}")

    # 1. Download the image (with retries for transient failures)
    downloaded = False
    last_error = None
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as response:
                content_type = response.headers.get("Content-Type", "")
                body = response.read()
                if "image" not in content_type:
                    snippet = body[:300].decode("utf-8", errors="replace")
                    last_error = f"Unexpected response: {content_type} — body: {snippet!r}"
                    log.warning(f"✗ {last_error} (attempt {attempt}/{DOWNLOAD_RETRIES})")
                else:
                    with open(output, "wb") as f:
                        f.write(body)
                    log.info(f"✓ Image saved: {output}")
                    downloaded = True
                    break
        except Exception as e:
            last_error = str(e)
            log.warning(f"✗ Download error: {e} (attempt {attempt}/{DOWNLOAD_RETRIES})")

        if attempt < DOWNLOAD_RETRIES:
            delay = RETRY_BACKOFF_SECS * attempt
            log.info(f"→ Retrying in {delay}s...")
            time.sleep(delay)

    if not downloaded:
        log.error(f"✗ Download failed after {DOWNLOAD_RETRIES} attempts: {last_error}")
        log.error("RESULT: FAIL")
        sys.exit(1)

    # 2. macOS — Photos app
    if IS_MACOS and SAVE_TO_PHOTOS:
        log.info("→ Importing to Photos app...")
        try:
            result = subprocess.run(
                [
                    "osascript", "-e",
                    f'tell application "Photos" to import POSIX file "{output}"',
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                log.info("✓ Imported to Photos app!")
            else:
                log.warning(f"⚠ Photos app failed: {result.stderr.strip()}")
        except Exception as e:
            log.warning(f"⚠ Photos app unavailable: {e}")

    # 3. macOS — iCloud Drive
    if IS_MACOS and SAVE_TO_ICLOUD:
        os.makedirs(ICLOUD_FOLDER, exist_ok=True)
        icloud_dest = os.path.join(ICLOUD_FOLDER, filename)
        log.info(f"→ Copying to iCloud Drive/Tapmusic/{filename}...")
        try:
            shutil.copy2(output, icloud_dest)
            log.info(f"✓ Copied to iCloud: {icloud_dest}")
        except Exception as e:
            log.error(f"✗ iCloud copy error: {e}")

    # 4. Custom destination (any OS)
    if SAVE_TO_CUSTOM:
        if not CUSTOM_PATH:
            log.warning("⚠ SAVE_TO_CUSTOM is True but CUSTOM_PATH is empty — skipping.")
        else:
            os.makedirs(CUSTOM_PATH, exist_ok=True)
            custom_dest = os.path.join(CUSTOM_PATH, filename)
            log.info(f"→ Copying to custom path: {CUSTOM_PATH}...")
            try:
                shutil.copy2(output, custom_dest)
                log.info(f"✓ Copied to: {custom_dest}")
            except Exception as e:
                log.error(f"✗ Custom copy error: {e}")

    log.info("Done.")
    log.info("RESULT: OK")


if __name__ == "__main__":
    run()
