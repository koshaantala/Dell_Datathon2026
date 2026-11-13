"""The app instance the server runs: `uvicorn highground.web.main:app` (or `make dev`)."""

from highground.web.app import create_app

app = create_app()
