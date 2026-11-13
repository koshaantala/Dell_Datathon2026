"""River gauges in upstream-to-downstream order, from content/gauges.yaml."""

from __future__ import annotations

from typing import Any

from highground.models import Gauge


class GaugeNetwork:
    def __init__(self, gauges: list[Gauge]) -> None:
        self.gauges = gauges
        self._index = {g.id: i for i, g in enumerate(gauges)}

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> GaugeNetwork:
        return cls([Gauge(**g) for g in config.get("gauges", [])])

    def get(self, gauge_id: str) -> Gauge | None:
        index = self._index.get(gauge_id)
        return self.gauges[index] if index is not None else None

    def upstream_of(self, gauge_id: str) -> Gauge | None:
        """The next gauge upstream, or None for the top gauge or an unknown id."""
        index = self._index.get(gauge_id)
        if index is None or index == 0:
            return None
        return self.gauges[index - 1]
