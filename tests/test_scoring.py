import pytest

from highground.scoring import ScoringConfigError, pick_band, score_site


def factor(score, key):
    return next(f for f in score.factors if f.key == key)


def test_worst_case_site_is_severe(content, make_site):
    score = score_site(make_site(), content.scoring_rules())
    assert score.points == score.available == 10
    assert score.band.name == "Severe"


@pytest.mark.parametrize(
    ("zones", "subtypes", "points"),
    [
        (["AE"], ["FLOODWAY"], 4),
        (["AE"], [], 3),
        (["X"], ["0.2 PCT ANNUAL CHANCE FLOOD HAZARD"], 1),
        (["X"], ["AREA OF MINIMAL FLOOD HAZARD"], 0),
    ],
)
def test_fema_zone_points(content, make_site, zones, subtypes, points):
    site = make_site(fema_zones=zones, fema_subtypes=subtypes)
    assert factor(score_site(site, content.scoring_rules()), "fema_zone").points == points


@pytest.mark.parametrize(("height", "points"), [(0.5, 4), (2.99, 4), (3.0, 2), (9.9, 2), (12, 0)])
def test_height_thresholds(content, make_site, height, points):
    site = make_site(elevation_m=500 + height, terrain_min_m=500)
    result = factor(score_site(site, content.scoring_rules()), "height_above_low_ground")
    assert result.points == points
    assert f"{height:.1f} m" in result.text


@pytest.mark.parametrize(("km", "points"), [(0.1, 2), (0.5, 2), (1.5, 1), (5.0, 0)])
def test_high_water_mark_distance(content, make_site, km, points):
    site = make_site(high_water_mark_km=km)
    assert factor(score_site(site, content.scoring_rules()), "high_water_mark").points == points


def test_missing_data_is_not_checked_and_not_counted(content, make_site):
    site = make_site(fema_zones=[], fema_subtypes=[], high_water_mark_km=None)
    score = score_site(site, content.scoring_rules())
    assert factor(score, "fema_zone").points is None
    assert score.available == 4  # only the height factor had data


def test_planned_factors_never_count(content, make_site):
    score = score_site(make_site(), content.scoring_rules())
    planned = [f for f in score.factors if f.key in ("way_out", "walk_to_higher_ground")]
    assert planned and all(not f.checked for f in planned)


def test_text_is_translated(content, make_site):
    score = score_site(make_site(), content.scoring_rules(), lang="es")
    assert factor(score, "fema_zone").text.startswith("En el cauce")


def test_unknown_factor_raises(content, make_site):
    rules = content.scoring_rules() | {"factors": {"mystery": {"label": "?", "max_points": 1}}}
    with pytest.raises(ScoringConfigError):
        score_site(make_site(), rules)


def test_band_boundaries(content):
    bands = content.scoring_rules()["bands"]
    assert pick_band(0.0, bands).name == "Lower"
    assert pick_band(0.25, bands).name == "Elevated"
    assert pick_band(0.5, bands).name == "High"
    assert pick_band(0.75, bands).name == "Severe"
