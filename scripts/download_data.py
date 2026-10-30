"""Fetch NOAA source snapshots and preserve a small, byte-faithful study extract.

Run from the repository root: python scripts/download_data.py
The committed lock file fixes source URLs, versions, and SHA-256 checksums.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
YEARS = range(2020, 2025)
TABLES = ("details", "locations", "fatalities")
LOCK = ROOT / "data/sources.lock.json"
RAW = ROOT / "data/raw"
CACHE = ROOT / "data/source_cache"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "flash-flood-portfolio/1.0 (public research)"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def discover() -> list[dict]:
    index = fetch(BASE).decode("utf-8")
    files = []
    for year in YEARS:
        for table in TABLES:
            pattern = rf"StormEvents_{table}-ftp_v1\.0_d{year}_c\d{{8}}\.csv\.gz"
            names = sorted(set(re.findall(pattern, index)))
            if not names:
                raise RuntimeError(f"No NOAA snapshot for {table}/{year}")
            files.append({"year": year, "table": table, "filename": names[-1], "url": BASE + names[-1]})
    return files


def download_one(item: dict) -> tuple[dict, bytes]:
    path = CACHE / item["filename"]
    content = path.read_bytes() if path.exists() else fetch(item["url"])
    digest = sha256(content)
    if item.get("sha256") and item["sha256"] != digest:
        raise RuntimeError(f"Source changed: {item['filename']}; refusing an unreviewed refresh")
    path.write_bytes(content)
    return dict(item, sha256=digest, bytes=len(content)), content


def rows(content: bytes) -> tuple[list[str], list[dict]]:
    text = gzip.decompress(content).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader.fieldnames), list(reader)


def write_extract(name: str, fields: list[str], records: list[dict]) -> dict:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    content = gzip.compress(buffer.getvalue().encode("utf-8"), mtime=0)
    path = RAW / name
    path.write_bytes(content)
    return {"path": str(path.relative_to(ROOT)), "rows": len(records), "sha256": sha256(content)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-lock", action="store_true", help="Explicitly discover and lock new NOAA snapshots")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    existing = json.loads(LOCK.read_text()) if LOCK.exists() and not args.refresh_lock else None
    sources = existing["sources"] if existing else discover()
    with ThreadPoolExecutor(max_workers=5) as pool:
        downloaded = list(pool.map(download_one, sources))
    files = {(item["year"], item["table"]): (item, content) for item, content in downloaded}
    extracts, locked = [], []
    for year in YEARS:
        item, content = files[(year, "details")]
        fields, records = rows(content)
        # No numeric, date, category, or missing-value corrections at this layer.
        selected = [row for row in records if row["EVENT_TYPE"].strip() == "Flash Flood"]
        ids = {row["EVENT_ID"] for row in selected}
        extracts.append(write_extract(f"details_{year}.csv.gz", fields, selected))
        locked.append(dict(item, full_source_rows=len(records)))
        for table in ("locations", "fatalities"):
            item, content = files[(year, table)]
            fields, records = rows(content)
            selected = [row for row in records if row["EVENT_ID"] in ids]
            extracts.append(write_extract(f"{table}_{year}.csv.gz", fields, selected))
            locked.append(dict(item, full_source_rows=len(records)))
    payload = {
        "publisher": "NOAA National Centers for Environmental Information / National Weather Service",
        "retrieved_at_utc": existing["retrieved_at_utc"] if existing else datetime.now(timezone.utc).isoformat(),
        "scope": "All Flash Flood records for 2020-2024; geography scoped in the cleaning pipeline",
        "extraction": "Exact CSV cell strings preserved; only event-type and linked-ID row filters applied",
        "sources": locked,
        "extracts": extracts,
    }
    LOCK.write_text(json.dumps(payload, indent=2) + "\n")
    for item in extracts:
        print(f"{item['path']}: {item['rows']:,} rows")
    print(f"Locked {len(locked)} source snapshots; original downloads cached outside Git tracking")


if __name__ == "__main__":
    main()
