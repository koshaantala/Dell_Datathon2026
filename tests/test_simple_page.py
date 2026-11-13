"""The GitHub Pages copy (docs/index.html) must match what the build script produces."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_simple_page", ROOT / "scripts/build_simple_page.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_docs_page_is_up_to_date(tmp_path):
    builder = load_builder()
    out = tmp_path / "index.html"
    count = builder.build(
        ROOT / "pages/simple_template.html",
        ROOT / "data/hill_country_sites.csv",
        ROOT / "content/gauges.yaml",
        out,
    )
    assert count == 50
    assert out.read_text() == (ROOT / "docs/index.html").read_text(), (
        "docs/index.html is out of date. Run: python scripts/build_simple_page.py"
    )
