"""Data shapes shared across the app."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Site(BaseModel):
    """One assessed location: a ~275 m map tile with its matched context."""

    id: str
    locality: str
    county: str = ""
    acquisition_date: str = ""
    latitude: float
    longitude: float
    bounds: tuple[float, float, float, float] | None = None  # west, south, east, north
    fema_zones: list[str] = Field(default_factory=list)
    fema_subtypes: list[str] = Field(default_factory=list)
    elevation_m: float | None = None
    terrain_min_m: float | None = None
    terrain_max_m: float | None = None
    slope_mean_deg: float | None = None
    high_water_mark_key: str = ""
    high_water_mark_km: float | None = None
    gauge_id: str = ""
    gauge_name: str = ""
    gauge_km: float | None = None
    image_path: str = ""
    source_url: str = ""
    attribution: str = ""
    reuse: str = ""
    license_url: str = ""
    notes: str = ""

    @property
    def height_above_low_ground_m(self) -> float | None:
        if self.elevation_m is None or self.terrain_min_m is None:
            return None
        return max(0.0, self.elevation_m - self.terrain_min_m)


class SiteMatch(BaseModel):
    site: Site
    distance_m: float


class Factor(BaseModel):
    key: str
    label: str
    max_points: int
    points: int | None = None  # None = not checked (planned, or no data here)
    text: str = ""

    @property
    def checked(self) -> bool:
        return self.points is not None


class Band(BaseModel):
    name: str
    color: str
    min_share: float


class StayScore(BaseModel):
    points: int
    available: int
    band: Band
    factors: list[Factor]

    @property
    def share(self) -> float:
        return self.points / self.available if self.available else 0.0

    @property
    def checked(self) -> list[Factor]:
        return [f for f in self.factors if f.checked]

    @property
    def not_checked(self) -> list[Factor]:
        return [f for f in self.factors if not f.checked]


class Gauge(BaseModel):
    id: str
    name: str
    latitude: float | None = None
    longitude: float | None = None

    @property
    def usgs_url(self) -> str:
        return f"https://waterdata.usgs.gov/monitoring-location/{self.id}/"


class GaugeReading(BaseModel):
    gauge_id: str
    value: float
    unit: str
    time: str


class Alert(BaseModel):
    event: str
    headline: str = ""
    severity: str = ""
    ends: str | None = None
