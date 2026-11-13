"""Build docs/index.html, the one-page HighGround site served by GitHub Pages.

The page's wording, score rules and styling live in pages/simple_template.html.
This script inlines the site data from data/hill_country_sites.csv and the gauge
order from content/gauges.yaml, so the page needs no server.

    python scripts/build_simple_page.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

PLACEHOLDER = "__SITES__"
NOTE_SUFFIXES = (
    "; screening note, human annotation pending.",
    "; screening note, annotation pending.",
)


def clean_note(note: str) -> str:
    for suffix in NOTE_SUFFIXES:
        if note.endswith(suffix):
            return note[: -len(suffix)] + "."
    return note


def load_sites(csv_path: Path, gauges_path: Path) -> list[dict]:
    gauges = yaml.safe_load(gauges_path.read_text(encoding="utf-8"))["gauges"]
    order = [g["id"] for g in gauges]
    names = {g["id"]: g["name"] for g in gauges}
    sites = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            gauge_id = row["usgs_gage_height_station_id"]
            index = order.index(gauge_id) if gauge_id in order else -1
            sites.append(
                {
                    "id": row["image_id"],
                    "town": row["locality"].split(" / ")[0],
                    "county": row["county_name"],
                    "lat": round(float(row["latitude"]), 5),
                    "lon": round(float(row["longitude"]), 5),
                    "fema": json.loads(row["fema_zone_subtypes"] or "[]")
                    + json.loads(row["fema_flood_zones"] or "[]"),
                    "height": round(
                        max(0.0, float(row["elevation_m"]) - float(row["terrain_elevation_min_m"])),
                        1,
                    ),
                    "hwmKm": round(float(row["nearest_high_water_mark_distance_km"]), 3),
                    "gauge": names.get(gauge_id, row["usgs_gage_height_station_name"]),
                    "gaugeKm": round(float(row["usgs_gage_height_station_distance_km"]), 1),
                    "upstream": names[order[index - 1]] if index > 0 else None,
                    "notes": clean_note(row["screening_notes"]),
                    "noaa": row["source_url"],
                    "date": row["acquisition_date"],
                }
            )
    return sites


def build(template: Path, csv_path: Path, gauges_path: Path, out: Path) -> int:
    html = template.read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        raise SystemExit(f"{template} has no {PLACEHOLDER} placeholder")
    sites = load_sites(csv_path, gauges_path)
    data = json.dumps(sites, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html.replace(PLACEHOLDER, data), encoding="utf-8")
    return len(sites)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--template", type=Path, default=Path("pages/simple_template.html"))
    parser.add_argument("--sites", type=Path, default=Path("data/hill_country_sites.csv"))
    parser.add_argument("--gauges", type=Path, default=Path("content/gauges.yaml"))
    parser.add_argument("--out", type=Path, default=Path("docs/index.html"))
    args = parser.parse_args(argv)
    count = build(args.template, args.sites, args.gauges, args.out)
    print(f"Wrote {args.out} with {count} sites")
    return 0


if __name__ == "__main__":
    sys.exit(main())
