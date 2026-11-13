from highground.sites import SiteRepository, haversine_m, site_from_row


def test_haversine_one_degree_latitude():
    assert abs(haversine_m(30, -99, 31, -99) - 111_195) < 100


def test_real_data_loads(settings):
    sites = SiteRepository.from_csv(settings.sites_csv)
    assert len(sites) == 50
    assert all(site.id.startswith("HC") for site in sites.all())


def test_nearest_within_and_outside_range(settings):
    sites = SiteRepository.from_csv(settings.sites_csv)
    hc001 = sites.get("HC001")
    match = sites.nearest(hc001.latitude + 0.001, hc001.longitude, max_km=1.0)
    assert match is not None and match.distance_m < 200
    assert sites.nearest(29.4, -98.5, max_km=1.0) is None  # San Antonio: not covered


def test_row_parsing_handles_blanks_and_json():
    row = {
        "image_id": "HC999",
        "latitude": "30",
        "longitude": "-99",
        "fema_flood_zones": '["AE"]',
        "fema_zone_subtypes": "",
        "elevation_m": "",
        "west": "",
    }
    site = site_from_row(row)
    assert site.fema_zones == ["AE"]
    assert site.fema_subtypes == []
    assert site.elevation_m is None
    assert site.bounds is None


def test_geojson_uses_tile_polygons(settings):
    geojson = SiteRepository.from_csv(settings.sites_csv).to_geojson()
    assert geojson["features"][0]["geometry"]["type"] == "Polygon"
