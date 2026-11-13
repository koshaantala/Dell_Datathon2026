"""Plain-language summary of a Stay Score.

The vision-language model (Qwen on the GB10 via vLLM) rewrites the computed facts
in friendly words. If the model is off, unreachable, or adds a number that is not
in the facts, we fall back to a fixed template, so the page always has a summary.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from highground.models import Site, StayScore

log = logging.getLogger(__name__)

LANGUAGE_NAMES = {"en": "English", "es": "Spanish"}
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def build_facts(site: Site, score: StayScore, band_label: str | None = None) -> dict[str, Any]:
    """The only information the model is allowed to use.

    band_label is the risk level in the reader's language (from site.*.yaml band_names).
    """
    return {
        "place": site.locality,
        "risk_level": band_label or score.band.name,
        "points": score.points,
        "points_available": score.available,
        "reasons": [f.text for f in score.checked],
        "not_checked_yet": [f.label for f in score.not_checked],
    }


def template_summary(facts: dict[str, Any], lang: str) -> str:
    reasons = " ".join(facts["reasons"][:2])
    if lang == "es":
        level = facts["risk_level"].lower()
        return f"Este lugar cerca de {facts['place']} tiene un riesgo {level}. {reasons}"
    return f"This spot near {facts['place']} has {facts['risk_level'].lower()} risk. {reasons}"


def introduces_new_numbers(text: str, facts: dict[str, Any]) -> bool:
    """True if the text contains a number that does not appear in the facts."""
    allowed = {n.replace(",", ".") for n in NUMBER.findall(json.dumps(facts, ensure_ascii=False))}
    found = {n.replace(",", ".") for n in NUMBER.findall(text)}
    return not found <= allowed


class SummaryService:
    def __init__(
        self,
        prompts: dict[str, Any],
        *,
        enabled: bool,
        base_url: str,
        model: str,
        api_key: str,
        timeout_s: float,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.prompts = prompts
        self.enabled = enabled
        self.model = model
        self._client = client or AsyncOpenAI(
            base_url=base_url, api_key=api_key, timeout=timeout_s, max_retries=0
        )

    async def summarize(self, facts: dict[str, Any], lang: str) -> tuple[str, str]:
        """Return (summary, source) where source is "model" or "template"."""
        if not self.enabled:
            return template_summary(facts, lang), "template"
        prompt = self.prompts["summary"]
        user = prompt["user"].format(
            language=LANGUAGE_NAMES.get(lang, "English"),
            facts_json=json.dumps(facts, ensure_ascii=False, indent=2),
        )
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=200,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": user},
                ],
            )
            text = (response.choices[0].message.content or "").strip()
        except Exception as exc:  # any model/network failure falls back to the template
            log.warning("Summary model unavailable: %s", exc)
            return template_summary(facts, lang), "template"
        if not text or introduces_new_numbers(text, facts):
            log.warning("Summary rejected (empty or added numbers): %r", text)
            return template_summary(facts, lang), "template"
        return text, "model"
