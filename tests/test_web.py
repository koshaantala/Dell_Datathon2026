import pytest


@pytest.mark.parametrize(
    "path",
    ["/", "/report?site=HC001", "/plan?site=HC001", "/watch", "/watch?site=HC001", "/about"],
)
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "HighGround" in response.text


def test_report_shows_score_and_reasons(client):
    html = client.get("/report?site=HC001").text
    assert "Severe" in html and "FEMA floodway" in html


def test_dropped_pin_snaps_to_nearest_site(client):
    html = client.get("/report?lat=30.0727&lon=-99.3370").text
    assert "Hunt / Guadalupe River" in html and "nearest assessed spot" in html


def test_pin_outside_coverage(client):
    assert "data for this spot yet" in client.get("/report?lat=29.4&lon=-98.5").text


def test_unknown_site_is_404_page(client):
    response = client.get("/report?site=NOPE")
    assert response.status_code == 404
    assert "find that page or place" in response.text


def test_language_switch_sets_cookie(client):
    response = client.get("/?lang=es")
    assert "Revisar un lugar" in response.text
    assert client.cookies.get("lang") == "es"
    assert "Revisar un lugar" in client.get("/about").text  # remembered


def test_api_report(client):
    data = client.get("/api/report?site=HC016").json()
    assert data["score"]["band"]["name"] == "Lower"
    assert data["gauge"]["id"] == "USGS-08166140"
    assert data["upstream_gauge"]["id"] == "USGS-08165500"


def test_api_report_needs_a_location(client):
    assert client.get("/api/report").status_code == 422
    assert client.get("/api/report?lat=29.4&lon=-98.5").status_code == 404


def test_api_summary_and_live_without_services(client):
    assert client.get("/api/summary?site=HC001").json()["source"] == "template"
    assert client.get("/api/live?site=HC001").json() == {
        "enabled": False,
        "alerts": None,
        "gauge": None,
    }


def test_api_sites_and_health(client):
    assert len(client.get("/api/sites").json()["features"]) == 50
    assert client.get("/api/health").json()["sites"] == 50


def test_image_404_when_files_are_lfs_pointers(client):
    assert client.get("/api/images/HC001").status_code == 404
