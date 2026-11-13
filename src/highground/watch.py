"""Night Watch: decide when to wake someone, and replay past floods against the rules."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from highground.models import Alert

Series = list[tuple[datetime, float]]  # (time, gauge height in feet), sorted by time


def alert_triggers(alerts: list[Alert], rules: dict[str, Any]) -> list[Alert]:
    """NWS alerts that match the configured event types."""
    events = {e.lower() for e in rules.get("nws_events", [])}
    return [a for a in alerts if a.event.lower() in events]


def rise_per_hour(series: Series, at_index: int, tolerance_min: int = 20) -> float | None:
    """Rise in feet over the hour before series[at_index], if a reading ~1 h earlier exists."""
    time, value = series[at_index]
    target = time - timedelta(hours=1)
    best = None
    for earlier_time, earlier_value in series[:at_index]:
        gap = abs((earlier_time - target).total_seconds()) / 60
        if gap <= tolerance_min and (best is None or gap < best[0]):
            best = (gap, earlier_value)
    return None if best is None else value - best[1]


def first_rise_alert(series: Series, threshold_ft_per_hour: float) -> datetime | None:
    """First time the river rose faster than the threshold."""
    for index in range(len(series)):
        rise = rise_per_hour(series, index)
        if rise is not None and rise >= threshold_ft_per_hour:
            return series[index][0]
    return None


def load_replay(replay_dir: Path, event: str = "july2025") -> dict[str, Series] | None:
    """Gauge series written by scripts/build_replay.py, or None if not downloaded yet."""
    path = replay_dir / f"{event}.json"
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        gauge_id: sorted((datetime.fromisoformat(t), float(v)) for t, v in points)
        for gauge_id, points in raw.get("gauges", {}).items()
    }
