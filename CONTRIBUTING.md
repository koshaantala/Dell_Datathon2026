# Working together

## Workflow

1. Pull the latest `main`: `git pull`.
2. Make a branch for one change: `git checkout -b short-description`.
3. Commit small, clear steps: `git commit -m "Add Spanish text for plan page"`.
4. Run `make check` (lint + tests). CI runs the same checks on every pull request.
5. Push and open a pull request. One teammate reviews before merging.

## Code standards

- Python 3.10+, formatted and linted with `ruff` (`make format`). `make install` adds a
  pre-commit hook that does this automatically.
- Keep wording out of code and templates: it belongs in `content/*.yaml`.
- Keep scoring rules transparent: thresholds in `scoring.yaml`, logic in `scoring.py`.
- Outside services (model, NWS, USGS) must fail gracefully. A page should never break
  because a service is down.
- Add or update a test for every behavior change. Tests must not call the network.
- Never commit `.env`, API keys or personal data.

## Data honesty

- Show where every number comes from. Add sources to `about.sources` in the content file.
- Never invent data. If something is missing, show "not checked yet."
- Never call a place "safe."
