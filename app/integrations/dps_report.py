from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import httpx

from app.config import settings


class DPSReportError(RuntimeError):
    """Raised when dps.report calls fail."""


def _cache_path(cache_dir: Path, permalink_or_id: str) -> Path:
    slug = permalink_or_id.rstrip("/").split("/")[-1]
    return cache_dir / f"{slug}.json"


async def upload_log(file_path: Path) -> Dict[str, Any]:
    """
    Upload an EVTC/ZEVTC log to dps.report and return the API response.
    """
    if not file_path.exists():
        raise DPSReportError(f"File not found: {file_path}")

    url = f"{settings.DPS_REPORT_BASE_URL}/uploadContent"
    params = {"json": 1}

    async with httpx.AsyncClient(timeout=60) as client:
        with file_path.open("rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            resp = await client.post(url, params=params, files=files)

    if resp.status_code != 200:
        raise DPSReportError(f"Upload failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    if "permalink" not in data:
        raise DPSReportError(f"dps.report response missing permalink: {data}")

    return data


async def get_json(permalink_or_id: str) -> Dict[str, Any]:
    """
    Fetch EI-like JSON from dps.report getJson endpoint.
    """
    url = f"{settings.DPS_REPORT_BASE_URL}/getJson"
    params = {"permalink": permalink_or_id}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        raise DPSReportError(f"getJson failed ({resp.status_code}): {resp.text}")

    return resp.json()


async def ensure_log_imported(file_path: Path, existing_permalink: str | None = None) -> Tuple[Dict[str, Any], str, Path]:
    """
    Ensure a log is uploaded and EI JSON is available (with caching).

    Returns (json_data, permalink, json_path)
    """
    cache_dir = settings.DPS_REPORT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    permalink: str
    json_data: Dict[str, Any]

    # If a permalink is provided and cached, use it
    if existing_permalink:
        cache_file = _cache_path(cache_dir, existing_permalink)
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8")), existing_permalink, cache_file

    # Upload if no permalink
    if existing_permalink:
        permalink = existing_permalink
    else:
        upload_resp = await upload_log(file_path)
        permalink = upload_resp.get("permalink") or ""
        if not permalink:
            raise DPSReportError("No permalink returned by dps.report upload")

    cache_file = _cache_path(cache_dir, permalink)

    # Try cache first (may be warmed)
    if cache_file.exists():
        json_data = json.loads(cache_file.read_text(encoding="utf-8"))
        return json_data, permalink, cache_file

    json_data = await get_json(permalink)
    cache_file.write_text(json.dumps(json_data), encoding="utf-8")
    return json_data, permalink, cache_file


def ensure_log_imported_sync(file_path: Path, existing_permalink: str | None = None) -> Tuple[Dict[str, Any], str, Path]:
    """
    Sync helper that wraps the async ensure_log_imported for synchronous code paths.
    """
    return asyncio.run(ensure_log_imported(file_path, existing_permalink))
