"""Fill latitude/longitude for each gauge in content/gauges.yaml from the USGS API.

Needs internet. Run from the project folder:  python scripts/fetch_gauge_locations.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
import yaml

DEFAULT_API = "https://api.waterdata.usgs.gov/ogcapi/v0"


def fetch_location(client: httpx.Client, api: str, gauge_id: str) -> tuple[float, float] | None:
    response = client.get(
        f"{api}/collections/monitoring-locations/items/{gauge_id}", params={"f": "json"}
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    lon, lat = response.json()["geometry"]["coordinates"][:2]
    return float(lat), float(lon)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=Path("content/gauges.yaml"))
    parser.add_argument("--api", default=DEFAULT_API)
    args = parser.parse_args(argv)

    config = yaml.safe_load(args.file.read_text(encoding="utf-8"))
    with httpx.Client(timeout=20, headers={"User-Agent": "HighGround/0.1"}) as client:
        for gauge in config["gauges"]:
            location = fetch_location(client, args.api, gauge["id"])
            if location is None:
                print(f"  {gauge['id']}: not found, left blank")
                continue
            gauge["latitude"], gauge["longitude"] = location
            print(f"  {gauge['id']}: {location[0]:.5f}, {location[1]:.5f}")

    # Note: rewriting the file drops its comments; they are restored from git if needed.
    header = "# USGS river gauges, upstream to downstream. Coordinates from the USGS API.\n"
    args.file.write_text(header + yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    print(f"Updated {args.file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
