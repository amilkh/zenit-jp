#!/usr/bin/python3
"""Download original Wix-hosted images for the static ZenIT archive."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "archive" / "source.json"
ASSETS = ROOT / "assets" / "images"
MAPPING = ROOT / "archive" / "assets.json"


def main() -> None:
    records = json.loads(SOURCE.read_text(encoding="utf-8"))
    originals = sorted(
        {
            image["src"].split("/v1/", 1)[0]
            for record in records
            for image in record["images"]
            if "static.wixstatic.com/media/" in image["src"]
        }
    )
    ASSETS.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}

    for index, url in enumerate(originals, start=1):
        filename = Path(urlparse(url).path).name
        destination = ASSETS / filename
        mapping[url] = f"assets/images/{filename}"
        if destination.exists() and destination.stat().st_size:
            continue
        print(f"[{index}/{len(originals)}] {filename}", flush=True)
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())

    MAPPING.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"Downloaded {len(mapping)} images to {ASSETS}")


if __name__ == "__main__":
    main()
