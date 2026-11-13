# HighGround

**Know before you book. Know before the river does.**

HighGround checks the flood risk of a cabin, campsite or rental on the Guadalupe River
in the Texas Hill Country. Pick a spot on the map and get:

- a **Stay Score** (Lower / Elevated / High / Severe) with the reasons behind it,
- a plain-language summary written by Qwen on the GB10,
- the nearest **upstream river gauge** and live alerts,
- a printable **escape plan**, in English or Spanish.

Built for the UTSA Social Impact AI Datathon. It is a prototype and does not replace
official warnings.

**Try it now (no install):** https://koshaantala.github.io/Dell_Datathon2026/
That's the one-page version in `docs/`. The full version below adds the AI summary,
live alerts, Spanish and the printable plan.

## Quick start

```sh
# From this folder, inside your conda/venv environment (Python 3.10+)
python -m pip install -e ".[dev,data]"
cp .env.example .env        # optional: point it at your vLLM server
make dev                    # http://localhost:8080
```

No `make`? Run `python -m uvicorn highground.web.main:app --reload --port 8080`.

The site works without the model or internet. The summary falls back to a template,
and live data shows "unavailable." Map tiles need internet in the browser.

## Editing the website

Most changes never touch Python. See **[EDITING.md](EDITING.md)** for step-by-step help.

| To change… | Edit |
| --- | --- |
| Any wording (English) | `content/site.en.yaml` |
| Spanish wording | `content/site.es.yaml` (missing keys fall back to English) |
| Score thresholds, points, bands | `content/scoring.yaml` |
| Night Watch alert rules | `content/watch.yaml` |
| AI summary instructions | `content/prompts.yaml` |
| River gauges | `content/gauges.yaml` |
| Colors and fonts | `static/css/theme.css` |
| Page layout | `templates/*.html` |

With `make dev` running, save the file and reload the page.

## How it works

```text
browser ──► FastAPI (src/highground/web)
              ├─ pages.py ──► templates/*.html  (wording from content/*.yaml)
              └─ api.py   ──► /api/report, /api/summary, /api/live, /api/sites
                   ├─ scoring.py        fixed rules from content/scoring.yaml
                   ├─ sites.py          data/hill_country_sites.csv
                   ├─ services/summary  Qwen via vLLM, template fallback
                   ├─ services/nws      National Weather Service alerts
                   └─ services/usgs     USGS latest gauge height
```

**The score is rules, not AI.** Each factor in `scoring.yaml` turns site data into
points. Factors with no data are shown as "not checked" and left out of the band, so
missing data never makes a place look safer. The model only rewrites the computed facts.
If it adds any number that is not in the facts, its text is thrown away.

## Project layout

```text
content/      Editable YAML: wording, score rules, prompts, gauges
docs/         One-page site for GitHub Pages (built file; don't edit by hand)
pages/        Template for the one-page site
data/         Site data derived from the hackathon dataset (see data/README.md)
scripts/      Data-building scripts
src/highground/
  config.py   Settings from environment / .env
  content.py  Loads content/*.yaml, reloads on change
  scoring.py  Stay Score rules
  sites.py    Site lookup and nearest-site search
  watch.py    Night Watch rules and replay
  services/   NWS, USGS and model clients
  web/        FastAPI app, pages and API
templates/    Jinja2 HTML pages
static/       CSS, JavaScript, vendored Leaflet
tests/        pytest suite
```

## Common tasks

```sh
make test      # run tests
make lint      # check style (ruff)
make format    # fix style
make data SOURCE_CSV=path/to/image_metadata.csv   # rebuild site data
make page      # rebuild the GitHub Pages site in docs/
make gauges    # fill gauge coordinates from USGS (needs internet)
make replay    # download July 2025 river levels for Night Watch (needs internet)
make docker    # run in Docker
```

## The one-page site (GitHub Pages)

`docs/index.html` is a self-contained page that needs no server. Edit its wording,
score rules and colors in `pages/simple_template.html` (look for "EDIT THE WEBSITE
HERE"), then rebuild it with `make page` (or `python scripts/build_simple_page.py`)
and commit both files. A test fails if `docs/index.html` is out of date.

To publish: repo **Settings → Pages**, Source "Deploy from a branch", Branch `main`,
folder `/docs`.

## Running on the GB10

1. Start vLLM with Qwen3-VL-8B (see `UTSAworkbook.ipynb`). It listens on port 8000.
2. In `.env`, set `HIGHGROUND_VLM_BASE_URL=http://localhost:8000/v1`.
3. `make dev`, or to let teammates on the same network open it:
   `python -m uvicorn highground.web.main:app --host 0.0.0.0 --port 8080`.

## Adding a new factor

1. Add an evaluator function in `src/highground/scoring.py` and register it in `EVALUATORS`.
2. Add the factor's levels to `content/scoring.yaml` under the same key (remove `planned: true`).
3. Add a test in `tests/test_scoring.py`. Run `make check`.

## Known gaps

- Only 50 assessed spots (the July 2025 NOAA aerial tiles). Dropped pins snap to the
  nearest spot within 1 km.
- The image files in the dataset repo are Git LFS placeholders. Run `git lfs pull` there,
  then set `HIGHGROUND_IMAGES_DIR` to show the aerial photos.
- "Dry route out" and "Walk to higher ground" need road and terrain data from
  `observations.sqlite`, which is not included yet.
- Night Watch sign-up is not built. The rules and replay are.

## License

GPL-3.0, matching the workshop repository. Leaflet is BSD-2-Clause (`static/vendor/leaflet/LICENSE`).
