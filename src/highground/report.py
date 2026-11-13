"""Assembles everything a Stay Report shows, for both the HTML page and the JSON API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from highground.content import ContentStore
from highground.gauges import GaugeNetwork
from highground.models import Gauge, Site, StayScore
from highground.scoring import score_site
from highground.services.summary import build_facts, template_summary

LFS_POINTER_PREFIX = b"version https://git-lfs"


@dataclass
class StayReport:
    site: Site
    score: StayScore
    gauge: Gauge | None
    upstream_gauge: Gauge | None
    fallback_summary: str
    has_image: bool


def real_image_path(images_dir: Path | None, site: Site) -> Path | None:
    """The site's image file if it exists and is a real image, not a Git LFS pointer."""
    if images_dir is None or not site.image_path:
        return None
    path = (images_dir / Path(site.image_path).name).resolve()
    if not path.is_file() or images_dir.resolve() not in path.parents:
        return None
    with path.open("rb") as handle:
        if handle.read(len(LFS_POINTER_PREFIX)) == LFS_POINTER_PREFIX:
            return None
    return path


def band_name(content: ContentStore, score: StayScore, lang: str) -> str:
    """The risk band's display name in the reader's language."""
    names = content.site_text(lang).get("band_names", {})
    return names.get(score.band.name, score.band.name)


def build_report(
    site: Site,
    content: ContentStore,
    gauges: GaugeNetwork,
    images_dir: Path | None,
    lang: str,
) -> StayReport:
    score = score_site(site, content.scoring_rules(), lang)
    band_label = band_name(content, score, lang)
    return StayReport(
        site=site,
        score=score,
        gauge=gauges.get(site.gauge_id),
        upstream_gauge=gauges.upstream_of(site.gauge_id),
        fallback_summary=template_summary(build_facts(site, score, band_label), lang),
        has_image=real_image_path(images_dir, site) is not None,
    )
