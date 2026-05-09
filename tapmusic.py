"""
tapmusic.py — Last.fm weekly album collage generator via tapmusic.net
Usage: python tapmusic.py
Output: saves image to Imagens/; on macOS also imports to Photos and iCloud Drive
"""

import urllib.request
import subprocess
import shutil
import os
import sys
import platform
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────
USERNAME  = "pedrosexo"   # your Last.fm username
PERIOD    = "7day"        # 7day | 1month | 3month | 6month | 12month | overall
SIZE      = "3x3"         # 3x3 | 4x4 | 5x5 | 10x10
CAPTIONS  = False         # show album/artist name on collage
PLAYCOUNT = False         # show play count on collage

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR    = os.path.join(BASE_DIR, "Imagens")
LOGS_DIR      = os.path.join(BASE_DIR, "Logs")

# macOS only — iCloud Drive destination
ICLOUD_FOLDER = os.path.expanduser(
    "~/Library/Mobile Documents/com~apple~CloudDocs/Tapmusic"
)
# ──────────────────────────────────────────────────────────────────────────────

IS_MACOS = platform.system() == "Darwin"


def run():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    if IS_MACOS:
        os.makedirs(ICLOUD_FOLDER, exist_ok=True)

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

    print(f"→ Generating collage for '{USERNAME}' ({PERIOD}, {SIZE})...")
    print(f"→ URL: {url}")

    # 1. Download the image
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type:
                print(f"✗ Unexpected response: {content_type}")
                sys.exit(1)
            with open(output, "wb") as f:
                f.write(response.read())
        print(f"✓ Image saved: {output}")
    except Exception as e:
        print(f"✗ Download error: {e}")
        sys.exit(1)

    # 2. macOS: try Photos app, then always copy to iCloud Drive
    if IS_MACOS:
        print("→ Importing to Photos app...")
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
                print("✓ Imported to Photos app!")
            else:
                print(f"⚠ Photos app failed: {result.stderr.strip()}")
        except Exception as e:
            print(f"⚠ Photos app unavailable: {e}")

        icloud_dest = os.path.join(ICLOUD_FOLDER, filename)
        print(f"→ Copying to iCloud Drive/Tapmusic/{filename}...")
        try:
            shutil.copy2(output, icloud_dest)
            print(f"✓ Copied to iCloud: {icloud_dest}")
        except Exception as e:
            print(f"✗ iCloud copy error: {e}")

    print("Done.")


if __name__ == "__main__":
    run()
