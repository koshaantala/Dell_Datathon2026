"""Builds the FastAPI app. The runnable instance lives in highground.web.main."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from highground import __version__
from highground.config import Settings, get_settings
from highground.content import ContentStore
from highground.services.summary import SummaryService
from highground.sites import SiteRepository
from highground.web import api, pages
from highground.web.deps import AppServices, get_language


def fill(text: str, **values: object) -> str:
    """Jinja filter: fill {placeholders} in a content string."""
    return text.format(**values)


def build_templates(settings: Settings) -> Jinja2Templates:
    templates = Jinja2Templates(directory=str(settings.templates_dir))
    templates.env.filters["fill"] = fill
    templates.env.globals["version"] = __version__
    return templates


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=logging.INFO)
    content = ContentStore(settings.content_dir)
    services = AppServices(
        settings=settings,
        content=content,
        sites=SiteRepository.from_csv(settings.sites_csv),
        templates=build_templates(settings),
        summary=SummaryService(
            content.prompts(),
            enabled=settings.vlm_enabled,
            base_url=settings.vlm_base_url,
            model=settings.vlm_model,
            api_key=settings.vlm_api_key,
            timeout_s=settings.vlm_timeout_s,
        ),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        user_agent = f"HighGround/{__version__} ({settings.contact_email})"
        async with httpx.AsyncClient(
            timeout=settings.live_timeout_s, headers={"User-Agent": user_agent}
        ) as client:
            services.http = client
            yield
        services.http = None

    app = FastAPI(title="HighGround", version=__version__, lifespan=lifespan)
    app.state.services = services
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
    app.include_router(api.router)
    app.include_router(pages.router)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> Response:
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        lang = get_language(request)
        return services.templates.TemplateResponse(
            request,
            "error.html",
            {
                "t": content.site_text(lang),
                "lang": lang,
                "switch_url": request.url,
                "status": exc.status_code,
                "detail": exc.detail,
            },
            status_code=exc.status_code,
        )

    return app
