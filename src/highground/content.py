"""Loads the editable YAML files in content/.

Files are re-read whenever they change on disk, so wording edits show up on the
next page load without restarting the server.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_LANGUAGES = ("en", "es")
DEFAULT_LANGUAGE = "en"


class ContentError(ValueError):
    """A content file is missing or not valid YAML."""


def normalize_language(lang: str | None) -> str:
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return base with override's keys laid on top, recursing into dicts."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def localize(value: Any, lang: str) -> Any:
    """Pick the right language from {"en": ..., "es": ...}; plain values pass through."""
    if isinstance(value, dict) and DEFAULT_LANGUAGE in value:
        return value.get(lang) or value[DEFAULT_LANGUAGE]
    return value


class ContentStore:
    def __init__(self, content_dir: Path) -> None:
        self.content_dir = content_dir
        self._cache: dict[Path, tuple[float, Any]] = {}

    def load(self, name: str) -> Any:
        path = self.content_dir / name
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError as exc:
            raise ContentError(f"Content file not found: {path}") from exc
        cached = self._cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ContentError(f"{path.name} is not valid YAML: {exc}") from exc
        self._cache[path] = (mtime, data)
        return data

    def site_text(self, lang: str) -> dict[str, Any]:
        """All page wording for a language, falling back to English per key."""
        english = self.load("site.en.yaml")
        if lang == DEFAULT_LANGUAGE:
            return english
        return deep_merge(english, self.load(f"site.{lang}.yaml"))

    def scoring_rules(self) -> dict[str, Any]:
        return self.load("scoring.yaml")

    def watch_rules(self) -> dict[str, Any]:
        return self.load("watch.yaml")

    def prompts(self) -> dict[str, Any]:
        return self.load("prompts.yaml")

    def gauges(self) -> dict[str, Any]:
        return self.load("gauges.yaml")
