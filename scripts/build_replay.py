"""Download river levels for the Night Watch replay into data/replay/july2025.json.

Uses the USGS Water Data API (continuous gauge height, parameter 00065) for every
gauge in content/gauges.yaml. Needs internet:

    python scripts/build_replay.py --start 2025-07-03 --end 2025-07-06
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
import yaml

DEFAULT_API = "https://api.waterdata.usgs.gov/ogcapi/v0"


def fetch_series(client: httpx.Client, api: str, gauge_id: str, start: str, end: str) -> list:
    """All (time, value) readings in the window, following the API's next-page links."""
    url: str | None = f"{api}/collections/continuous/items"
    params: dict | None = {
        "f": "json",
        "monitoring_location_id": gauge_id,
        "parameter_code": "00065",
        "time": f"{start}T00:00:00Z/{end}T00:00:00Z",
        "limit": 10000,
    }
    points = []
    while url:
        response = client.get(url, params=params)
        response.raise_for_status()
        body = response.json()
        for feature in body.get("features", []):
            props = feature.get("properties", {})
            if props.get("value") not in (None, ""):
                points.append([props["time"], float(props["value"])])
        url = next(
            (link["href"] for link in body.get("links", []) if link.get("rel") == "next"), None
        )
        params = None  # the next link already carries the query
    return sorted(points)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", required=True, help="YYYY-MM-DD (UTC)")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD (UTC, exclusive)")
    parser.add_argument("--gauges", type=Path, default=Path("content/gauges.yaml"))
    parser.add_argument("--out", type=Path, default=Path("data/replay/july2025.json"))
    parser.add_argument("--api", default=DEFAULT_API)
    args = parser.parse_args(argv)

    gauge_ids = [g["id"] for g in yaml.safe_load(args.gauges.read_text())["gauges"]]
    result = {"source": "USGS Water Data API, parameter 00065 (ft)", "gauges": {}}
    with httpx.Client(timeout=60, headers={"User-Agent": "HighGround/0.1"}) as client:
        for gauge_id in gauge_ids:
            series = fetch_series(client, args.api, gauge_id, args.start, args.end)
            result["gauges"][gauge_id] = series
            print(f"  {gauge_id}: {len(series)} readings")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
