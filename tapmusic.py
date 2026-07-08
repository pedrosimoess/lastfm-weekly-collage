"""
tapmusic.py — Last.fm weekly album collage generator via tapmusic.net
Usage: python tapmusic.py
Output: always saves to Imagens/; optional destinations configured below
Works on macOS, Windows and Linux — macOS-only steps (Photos/iCloud) are
skipped automatically on other platforms.
"""

import urllib.request
import urllib.error
import socket
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
PHOTOS_IMPORT_TIMEOUT_SECS = 60   # Photos can be slow to cold-start; bumped from 30s
PHOTOS_IMPORT_RETRIES      = 2    # total attempts (helps when Photos was still launching)

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
RETRY_BACKOFF_SECS   = 5     # base delay in seconds; DOUBLES each retry (5s, 10s, 20s, ...)
# ──────────────────────────────────────────────────────────────────────────────

# ─── Image validation settings ─────────────────────────────────────────────────
PNG_SIGNATURE   = b"\x89PNG\r\n\x1a\n"
MIN_IMAGE_BYTES = 2048   # anything smaller is almost certainly a truncated/broken file
# ──────────────────────────────────────────────────────────────────────────────

# ─── Disk space settings ───────────────────────────────────────────────────────
# Checked before the download even starts, so a full disk fails fast instead
# of burning through download retries for nothing.
MIN_FREE_SPACE_MB = 100
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

    # Also mirror to stdout so launchd/cron/Task Scheduler runs still show live output.
    # encoding="utf-8" with errors="replace" keeps this from crashing on Windows
    # consoles whose default code page can't render the ✓/✗/→ characters.
    console_stream = sys.stdout
    if hasattr(console_stream, "reconfigure"):
        try:
            console_stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    console_handler = logging.StreamHandler(console_stream)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


def has_enough_disk_space(path, min_mb, log):
    """Check free space on the volume containing `path` (works on Win/macOS/Linux)."""
    try:
        free_mb = shutil.disk_usage(path).free / (1024 * 1024)
    except Exception as e:
        log.warning(f"⚠ Could not check disk space for {path}: {e}")
        return True  # don't block the run if the check itself is unavailable

    if free_mb < min_mb:
        log.error(
            f"✗ Low disk space: {free_mb:.0f}MB free (need at least {min_mb}MB) on {path}"
        )
        return False
    return True


def run():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    log = setup_logger()
    had_warning = False  # tracks non-fatal failures in optional steps for the final RESULT line

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

    # 0. Make sure there's enough room before the network call, so a full disk
    #    fails fast instead of burning through DOWNLOAD_RETRIES for nothing.
    if not has_enough_disk_space(IMAGES_DIR, MIN_FREE_SPACE_MB, log):
        log.error("RESULT: FAIL")
        sys.exit(1)

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
                elif not body.startswith(PNG_SIGNATURE) or len(body) < MIN_IMAGE_BYTES:
                    last_error = f"Response looked truncated/corrupted ({len(body)} bytes)"
                    log.warning(f"✗ {last_error} (attempt {attempt}/{DOWNLOAD_RETRIES})")
                else:
                    with open(output, "wb") as f:
                        f.write(body)
                    log.info(f"✓ Image saved: {output}")
                    downloaded = True
                    break
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.gaierror):
                last_error = f"DNS/connection error — check your internet connection ({e.reason})"
            else:
                last_error = str(e)
            log.warning(f"✗ Download error: {last_error} (attempt {attempt}/{DOWNLOAD_RETRIES})")
        except Exception as e:
            last_error = str(e)
            log.warning(f"✗ Download error: {e} (attempt {attempt}/{DOWNLOAD_RETRIES})")

        if attempt < DOWNLOAD_RETRIES:
            delay = RETRY_BACKOFF_SECS * (2 ** (attempt - 1))
            log.info(f"→ Retrying in {delay}s...")
            time.sleep(delay)

    if not downloaded:
        log.error(f"✗ Download failed after {DOWNLOAD_RETRIES} attempts: {last_error}")
        log.error("RESULT: FAIL")
        sys.exit(1)

    # 2. macOS — Photos app
    if IS_MACOS and SAVE_TO_PHOTOS:
        log.info("→ Importing to Photos app...")
        photos_ok = False
        for photos_attempt in range(1, PHOTOS_IMPORT_RETRIES + 1):
            try:
                result = subprocess.run(
                    [
                        "osascript", "-e",
                        f'tell application "Photos" to import POSIX file "{output}"',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=PHOTOS_IMPORT_TIMEOUT_SECS,
                )
                if result.returncode == 0:
                    log.info("✓ Imported to Photos app!")
                    photos_ok = True
                    break
                log.warning(
                    f"⚠ Photos app failed: {result.stderr.strip()} "
                    f"(attempt {photos_attempt}/{PHOTOS_IMPORT_RETRIES})"
                )
            except Exception as e:
                log.warning(
                    f"⚠ Photos app unavailable: {e} "
                    f"(attempt {photos_attempt}/{PHOTOS_IMPORT_RETRIES})"
                )
            if photos_attempt < PHOTOS_IMPORT_RETRIES:
                log.info("→ Retrying Photos import (app may still be launching)...")

        if not photos_ok:
            had_warning = True

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
            had_warning = True

    # 4. Custom destination (any OS)
    if SAVE_TO_CUSTOM:
        if not CUSTOM_PATH:
            log.warning("⚠ SAVE_TO_CUSTOM is True but CUSTOM_PATH is empty — skipping.")
            had_warning = True
        else:
            os.makedirs(CUSTOM_PATH, exist_ok=True)
            custom_dest = os.path.join(CUSTOM_PATH, filename)
            log.info(f"→ Copying to custom path: {CUSTOM_PATH}...")
            try:
                shutil.copy2(output, custom_dest)
                log.info(f"✓ Copied to: {custom_dest}")
            except Exception as e:
                log.error(f"✗ Custom copy error: {e}")
                had_warning = True

    if had_warning:
        log.warning("Done with warnings — see above.")
        log.warning("RESULT: PARTIAL")
    else:
        log.info("Done.")
        log.info("RESULT: OK")


if __name__ == "__main__":
    run()
