"""The Stay Score: fixed, transparent rules read from content/scoring.yaml.

Each factor turns one piece of site data into points and a sentence. Factors with
no data for a site, or marked `planned`, are "not checked" and are left out of the
band calculation, so missing data never makes a place look safer.

To add a factor: write an evaluator below, register it in EVALUATORS, and add its
levels to scoring.yaml under the same key.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from highground.content import localize
from highground.models import Band, Factor, Site, StayScore

# An evaluator returns (points, sentence) or None when the site has no data for it.
Evaluator = Callable[[Site, dict[str, Any], str], "tuple[int, str] | None"]


class ScoringConfigError(ValueError):
    """scoring.yaml is missing something the rules need."""


def _as_list(value: Any) -> list[str]:
    return [str(v).upper() for v in (value if isinstance(value, list) else [value])]


def _threshold(value: Any) -> float:
    return math.inf if value in (None, ".inf") else float(value)


def evaluate_fema_zone(site: Site, config: dict[str, Any], lang: str) -> tuple[int, str] | None:
    labels = [s.upper() for s in site.fema_subtypes] + [z.upper() for z in site.fema_zones]
    if not labels:
        return None
    # Use the worst (highest-point) level any of the site's labels matches.
    for level in sorted(config["levels"], key=lambda lv: lv["points"], reverse=True):
        if set(_as_list(level["match"])) & set(labels):
            return level["points"], localize(level["text"], lang)
    return None


def evaluate_height(site: Site, config: dict[str, Any], lang: str) -> tuple[int, str] | None:
    value = site.height_above_low_ground_m
    if value is None:
        return None
    for level in config["levels"]:
        if value < _threshold(level["below_m"]):
            return level["points"], localize(level["text"], lang).format(value=value)
    return None


def evaluate_high_water_mark(
    site: Site, config: dict[str, Any], lang: str
) -> tuple[int, str] | None:
    km = site.high_water_mark_km
    if km is None:
        return None
    for level in config["levels"]:
        if km <= _threshold(level["within_km"]):
            text = localize(level["text"], lang).format(value_km=km, value_m=km * 1000)
            return level["points"], text
    return None


EVALUATORS: dict[str, Evaluator] = {
    "fema_zone": evaluate_fema_zone,
    "height_above_low_ground": evaluate_height,
    "high_water_mark": evaluate_high_water_mark,
}

NO_DATA_TEXT = {"en": "No data for this spot yet.", "es": "Aún no hay datos para este lugar."}


def pick_band(share: float, bands: list[dict[str, Any]]) -> Band:
    for band in sorted(bands, key=lambda b: b["min_share"], reverse=True):
        if share >= band["min_share"]:
            return Band(**band)
    raise ScoringConfigError("scoring.yaml bands must include one with min_share: 0")


def score_site(site: Site, rules: dict[str, Any], lang: str = "en") -> StayScore:
    factors: list[Factor] = []
    for key, config in rules.get("factors", {}).items():
        label = localize(config["label"], lang)
        factor = Factor(key=key, label=label, max_points=int(config["max_points"]))
        if config.get("planned"):
            factor.text = localize(config.get("text", ""), lang)
        elif key in EVALUATORS:
            result = EVALUATORS[key](site, config, lang)
            if result is None:
                factor.text = NO_DATA_TEXT.get(lang, NO_DATA_TEXT["en"])
            else:
                factor.points, factor.text = result
        else:
            raise ScoringConfigError(f"No evaluator for factor '{key}' in scoring.yaml")
        factors.append(factor)

    checked = [f for f in factors if f.checked]
    points = sum(f.points or 0 for f in checked)
    available = sum(f.max_points for f in checked)
    share = points / available if available else 0.0
    return StayScore(
        points=points,
        available=available,
        band=pick_band(share, rules["bands"]),
        factors=factors,
    )
