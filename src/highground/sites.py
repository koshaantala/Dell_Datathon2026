"""Loads assessed sites and finds the one nearest a dropped pin."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from highground.models import Site, SiteMatch

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value]
    return [str(item) for item in parsed] if isinstance(parsed, list) else [str(parsed)]


def site_from_row(row: dict[str, str]) -> Site:
    bounds_raw = [_float(row.get(k)) for k in ("west", "south", "east", "north")]
    bounds = tuple(bounds_raw) if all(v is not None for v in bounds_raw) else None
    return Site(
        id=row["image_id"],
        locality=row.get("locality", ""),
        county=row.get("county_name", ""),
        acquisition_date=row.get("acquisition_date", ""),
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        bounds=bounds,
        fema_zones=_json_list(row.get("fema_flood_zones")),
        fema_subtypes=_json_list(row.get("fema_zone_subtypes")),
        elevation_m=_float(row.get("elevation_m")),
        terrain_min_m=_float(row.get("terrain_elevation_min_m")),
        terrain_max_m=_float(row.get("terrain_elevation_max_m")),
        slope_mean_deg=_float(row.get("terrain_slope_mean_degrees")),
        high_water_mark_key=row.get("nearest_high_water_mark_key", ""),
        high_water_mark_km=_float(row.get("nearest_high_water_mark_distance_km")),
        gauge_id=row.get("usgs_gage_height_station_id", ""),
        gauge_name=row.get("usgs_gage_height_station_name", ""),
        gauge_km=_float(row.get("usgs_gage_height_station_distance_km")),
        image_path=row.get("image_path", ""),
        source_url=row.get("source_url", ""),
        attribution=row.get("attribution", ""),
        reuse=row.get("reuse", ""),
        license_url=row.get("license_url", ""),
        notes=row.get("screening_notes", ""),
    )


class SiteRepository:
    def __init__(self, sites: list[Site]) -> None:
        self._sites = sites
        self._by_id = {site.id: site for site in sites}

    @classmethod
    def from_csv(cls, path: Path) -> SiteRepository:
        with path.open(newline="", encoding="utf-8") as handle:
            return cls([site_from_row(row) for row in csv.DictReader(handle)])

    def __len__(self) -> int:
        return len(self._sites)

    def all(self) -> list[Site]:
        return list(self._sites)

    def get(self, site_id: str) -> Site | None:
        return self._by_id.get(site_id)

    def nearest(self, lat: float, lon: float, max_km: float) -> SiteMatch | None:
        """Nearest site centre within max_km of the point, or None."""
        best: SiteMatch | None = None
        for site in self._sites:
            distance = haversine_m(lat, lon, site.latitude, site.longitude)
            if best is None or distance < best.distance_m:
                best = SiteMatch(site=site, distance_m=distance)
        if best is None or best.distance_m > max_km * 1000:
            return None
        return best

    def to_geojson(self) -> dict[str, Any]:
        """Each site as a polygon (its tile) for the map."""
        features = []
        for site in self._sites:
            if site.bounds:
                w, s, e, n = site.bounds
                geometry = {
                    "type": "Polygon",
                    "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]],
                }
            else:
                geometry = {"type": "Point", "coordinates": [site.longitude, site.latitude]}
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": site.id,
                        "locality": site.locality,
                        "latitude": site.latitude,
                        "longitude": site.longitude,
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
