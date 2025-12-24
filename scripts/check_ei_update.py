import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests

DEFAULT_VERSION_FILE = Path(os.getenv("EI_VERSION_FILE", "ei_version.txt")).resolve()
REPO_API = "https://api.github.com/repos/baaron4/GW2-Elite-Insights-Parser/releases/latest"


def read_local_version(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return None


def fetch_latest_release() -> tuple[str, list[str]]:
    resp = requests.get(REPO_API, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")
    data = resp.json()
    tag = data.get("tag_name", "").strip()
    assets = data.get("assets", [])
    urls = [a.get("browser_download_url") for a in assets if a.get("browser_download_url")]
    return tag, urls


def main() -> int:
    current = read_local_version(DEFAULT_VERSION_FILE) or "unknown"
    try:
        latest, urls = fetch_latest_release()
    except Exception as e:
        print(f"Failed to check EI updates: {e}", file=sys.stderr)
        return 1

    if not latest:
        print("Could not determine latest EI version.")
        return 1

    if current != latest:
        print(f"New EI version available: {latest} (current: {current})")
        if urls:
            print("Download URLs:")
            for u in urls:
                print(f" - {u}")
        else:
            print("No asset URLs found in release.")
    else:
        print(f"EI is up to date (version {current})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
