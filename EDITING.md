# Editing HighGround

You can change almost everything on the site without writing Python.

## Before you start

1. Run the site: `make dev`, then open http://localhost:8080.
2. Make a branch: `git checkout -b wording-update`.
3. Edit a file, save it, and reload the page.
4. Run `make test` before you commit. It catches broken YAML and missing translations.

## Change wording

All English text is in `content/site.en.yaml`, grouped by page:

```yaml
home:
  title: Is this riverside stay a good idea?   # ← edit the text after the colon
```

Rules for YAML:

- Keep the indentation (two spaces). Never use tabs.
- Put text in quotes if it contains a colon `:` or starts with `{`.
- Long text can use `>-` and continue on indented lines below.
- Keep anything in `{curly braces}` exactly as it is. The site fills those in.
- Lists start each item with `- `.

Spanish is in `content/site.es.yaml` with the same keys. Leave a key out and the
English text is used. `make test` fails if Spanish has a key English doesn't (a typo).

## Change the score

Open `content/scoring.yaml`.

- **Thresholds:** change `below_m`, `within_km` or `points` in a factor's `levels`.
- **Bands:** change `min_share` (0.5 = half the available points) or `color`.
- **Explanations:** edit the `en:` and `es:` text under each level.

After editing, run `make test`. Some tests check the documented thresholds; update them
if you meant to change the rules.

## Change colors and fonts

Open `static/css/theme.css`. Every color and font the site uses is a variable there,
for example `--river: #1f7a8c;`. Change the value and reload.

## Change a page's layout

Pages are in `templates/`. Each one extends `base.html`, which holds the header and
footer. Text comes from the YAML as `{{ t.section.key }}`. To add a sentence:

1. Add the text to `content/site.en.yaml`, e.g. under `report:` add `tip: Check the forecast.`
2. Show it in the template: `<p>{{ t.report.tip }}</p>`.
3. Optionally add the Spanish under the same key in `site.es.yaml`.

## Change emergency contacts

In `content/site.en.yaml` under `plan: contacts:`, add verified numbers only:

```yaml
  contacts:
    - name: Emergency
      number: "911"
    - name: County emergency management
      number: "000-000-0000"   # replace with the real, verified number
```

## Change the AI summary

`content/prompts.yaml` holds the instructions sent to Qwen. Keep the rule that it uses
only the given facts. The app rejects any summary that adds a number not in the facts.
