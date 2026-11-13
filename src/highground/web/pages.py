"""HTML pages. Wording comes from content/site.*.yaml; layout from templates/."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from highground.content import SUPPORTED_LANGUAGES, localize
from highground.report import build_report
from highground.watch import first_rise_alert, load_replay
from highground.web.deps import AppServices, get_language, get_services, require_site

router = APIRouter(include_in_schema=False)

Services = Annotated[AppServices, Depends(get_services)]
Language = Annotated[str, Depends(get_language)]


def render(
    request: Request, services: AppServices, lang: str, template: str, **context: Any
) -> HTMLResponse:
    other = next(code for code in SUPPORTED_LANGUAGES if code != lang)
    switch_params = dict(request.query_params) | {"lang": other}
    response = services.templates.TemplateResponse(
        request,
        template,
        {
            "t": services.content.site_text(lang),
            "lang": lang,
            "switch_url": request.url.include_query_params(**switch_params),
            "site_count": len(services.sites),
            "max_snap_km": services.settings.max_snap_km,
            **context,
        },
    )
    if request.query_params.get("lang") in SUPPORTED_LANGUAGES:
        response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, samesite="lax")
    return response


@router.get("/", response_class=HTMLResponse)
def home(request: Request, services: Services, lang: Language) -> HTMLResponse:
    return render(request, services, lang, "index.html", page="home")


@router.get("/report", response_class=HTMLResponse)
def report(
    request: Request,
    services: Services,
    lang: Language,
    site: str | None = None,
    lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
) -> Response:
    distance_m = None
    if site:
        chosen = require_site(services, site)
    elif lat is not None and lon is not None:
        match = services.sites.nearest(lat, lon, services.settings.max_snap_km)
        if match is None:
            return render(request, services, lang, "outside.html", page="report", lat=lat, lon=lon)
        chosen, distance_m = match.site, match.distance_m
    else:
        return RedirectResponse("/", status_code=303)

    result = build_report(
        chosen, services.content, services.gauges, services.settings.images_dir, lang
    )
    return render(
        request,
        services,
        lang,
        "report.html",
        page="report",
        report=result,
        distance_m=distance_m,
        live_enabled=services.settings.live_data_enabled,
    )


@router.get("/plan", response_class=HTMLResponse)
def plan(request: Request, services: Services, lang: Language, site: str) -> HTMLResponse:
    chosen = require_site(services, site)
    result = build_report(chosen, services.content, services.gauges, None, lang)
    return render(request, services, lang, "plan.html", page="plan", report=result)


@router.get("/watch", response_class=HTMLResponse)
def watch(
    request: Request, services: Services, lang: Language, site: str | None = None
) -> HTMLResponse:
    rules = services.content.watch_rules()
    rules_text = [
        line.format(
            events=" / ".join(rules["nws_events"]),
            upstream_rise_ft_per_hour=rules["upstream_rise_ft_per_hour"],
            local_rise_ft_per_hour=rules["local_rise_ft_per_hour"],
        )
        for line in localize(rules["rules_text"], lang)
    ]
    replay = load_replay(services.settings.replay_dir)
    replay_rows = []
    if replay is not None:
        for gauge in services.gauges.gauges:
            series = replay.get(gauge.id)
            if series:
                when = first_rise_alert(series, rules["local_rise_ft_per_hour"])
                replay_rows.append({"gauge": gauge, "alert_at": when, "readings": len(series)})
    chosen = services.sites.get(site) if site else None
    return render(
        request,
        services,
        lang,
        "watch.html",
        page="watch",
        rules_text=rules_text,
        replay_available=replay is not None,
        replay_rows=replay_rows,
        site=chosen,
    )


@router.get("/about", response_class=HTMLResponse)
def about(request: Request, services: Services, lang: Language) -> HTMLResponse:
    return render(request, services, lang, "about.html", page="about")
