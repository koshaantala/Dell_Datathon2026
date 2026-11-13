from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from highground.config import Settings
from highground.content import ContentStore
from highground.models import Site
from highground.web.app import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings() -> Settings:
    """Real content and data, with outside services switched off."""
    return Settings(
        project_root=PROJECT_ROOT,
        vlm_enabled=False,
        live_data_enabled=False,
        images_dir=None,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def content() -> ContentStore:
    return ContentStore(PROJECT_ROOT / "content")


@pytest.fixture
def make_site():
    def _make(**overrides) -> Site:
        values = {
            "id": "T1",
            "locality": "Test / Guadalupe River",
            "latitude": 30.0,
            "longitude": -99.3,
            "fema_zones": ["AE"],
            "fema_subtypes": ["FLOODWAY"],
            "elevation_m": 501.0,
            "terrain_min_m": 500.0,
            "high_water_mark_km": 0.2,
            "gauge_id": "USGS-08166140",
        }
        values.update(overrides)
        return Site(**values)

    return _make
