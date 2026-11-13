"""Night Watch rules. The river series here are synthetic test inputs, not real readings."""

import json
from datetime import datetime, timedelta

from highground.models import Alert
from highground.watch import alert_triggers, first_rise_alert, load_replay, rise_per_hour

START = datetime(2025, 1, 1, 0, 0)


def series(values, step_min=15):
    return [(START + timedelta(minutes=i * step_min), v) for i, v in enumerate(values)]


def test_rise_needs_a_reading_an_hour_earlier():
    data = series([1.0, 1.0, 1.0, 1.0, 1.5])
    assert rise_per_hour(data, 0) is None
    assert rise_per_hour(data, 4) == 0.5


def test_first_rise_alert_finds_the_fast_rise():
    data = series([1.0, 1.0, 1.0, 1.0, 1.2, 2.0, 3.5, 5.0])
    assert first_rise_alert(data, threshold_ft_per_hour=2.0) == START + timedelta(minutes=90)
    assert first_rise_alert(series([1, 1.1, 1.2, 1.3, 1.4]), 2.0) is None


def test_alert_triggers_match_configured_events(content):
    alerts = [Alert(event="Flash Flood Warning"), Alert(event="Heat Advisory")]
    assert [a.event for a in alert_triggers(alerts, content.watch_rules())] == [
        "Flash Flood Warning"
    ]


def test_load_replay(tmp_path):
    assert load_replay(tmp_path) is None
    (tmp_path / "july2025.json").write_text(
        json.dumps(
            {
                "gauges": {
                    "G1": [["2025-07-04T02:00:00+00:00", 3.0], ["2025-07-04T01:00:00+00:00", 1.0]]
                }
            }
        )
    )
    loaded = load_replay(tmp_path)
    assert [v for _t, v in loaded["G1"]] == [1.0, 3.0]  # sorted by time
