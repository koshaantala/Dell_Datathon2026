import asyncio
from types import SimpleNamespace

from highground.scoring import score_site
from highground.services.summary import (
    SummaryService,
    build_facts,
    introduces_new_numbers,
    template_summary,
)


class FakeCompletions:
    def __init__(self, reply=None, error=None):
        self.reply, self.error = reply, error

    async def create(self, **_kwargs):
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def service(content, reply=None, error=None, enabled=True):
    fake = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(reply, error)))
    return SummaryService(
        content.prompts(),
        enabled=enabled,
        base_url="http://x",
        model="m",
        api_key="k",
        timeout_s=1,
        client=fake,
    )


def facts(content, make_site):
    site = make_site()
    return build_facts(site, score_site(site, content.scoring_rules()), "Severe")


def test_number_guard():
    data = {"points": 10, "reasons": ["Only 0.9 m above"]}
    assert not introduces_new_numbers("Scored 10 points, only 0.9 m up.", data)
    assert introduces_new_numbers("Flooded 3 times.", data)


def test_disabled_uses_template(content, make_site):
    text, source = asyncio.run(
        service(content, enabled=False).summarize(facts(content, make_site), "en")
    )
    assert source == "template" and "severe risk" in text


def test_model_text_is_used_when_clean(content, make_site):
    svc = service(content, reply="This spot is in the floodway. Have a plan.")
    assert asyncio.run(svc.summarize(facts(content, make_site), "en")) == (
        "This spot is in the floodway. Have a plan.",
        "model",
    )


def test_model_adding_numbers_falls_back(content, make_site):
    svc = service(content, reply="This spot flooded 7 times since 1990.")
    assert asyncio.run(svc.summarize(facts(content, make_site), "en"))[1] == "template"


def test_model_error_falls_back(content, make_site):
    svc = service(content, error=ConnectionError("server down"))
    assert asyncio.run(svc.summarize(facts(content, make_site), "en"))[1] == "template"


def test_spanish_template_uses_spanish_band(content, make_site):
    site = make_site()
    data = build_facts(site, score_site(site, content.scoring_rules(), "es"), "Severo")
    assert "riesgo severo" in template_summary(data, "es")
