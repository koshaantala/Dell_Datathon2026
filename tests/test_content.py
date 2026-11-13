"""Guards for the editable YAML files, so a typo is caught by `make test`, not at the demo."""

import pytest

from highground.content import ContentError, ContentStore, deep_merge, localize


def leaf_keys(data, prefix=""):
    if isinstance(data, dict):
        for key, value in data.items():
            yield from leaf_keys(value, f"{prefix}{key}.")
    else:
        yield prefix.rstrip(".")


@pytest.mark.parametrize(
    "name",
    ["site.en.yaml", "site.es.yaml", "scoring.yaml", "watch.yaml", "prompts.yaml", "gauges.yaml"],
)
def test_every_content_file_loads(content, name):
    assert content.load(name)


def test_spanish_keys_all_exist_in_english(content):
    english = set(leaf_keys(content.load("site.en.yaml")))
    spanish = set(leaf_keys(content.load("site.es.yaml")))
    assert spanish - english == set(), "site.es.yaml has keys that site.en.yaml does not"


def test_spanish_falls_back_to_english(content):
    text = content.site_text("es")
    assert text["brand"]["name"] == "HighGround"  # only in English file
    assert text["nav"]["home"] == "Revisar un lugar"


def test_every_band_has_a_message_and_name(content):
    for lang in ("en", "es"):
        text = content.site_text(lang)
        for band in content.scoring_rules()["bands"]:
            assert band["name"] in text["bands"]
            assert band["name"] in text["band_names"]


def test_deep_merge_and_localize():
    assert deep_merge({"a": {"b": 1, "c": 2}}, {"a": {"b": 3}}) == {"a": {"b": 3, "c": 2}}
    assert localize({"en": "Hi", "es": "Hola"}, "es") == "Hola"
    assert localize({"en": "Hi"}, "es") == "Hi"
    assert localize("plain", "es") == "plain"


def test_bad_yaml_gives_clear_error(tmp_path):
    (tmp_path / "site.en.yaml").write_text("title: [unclosed")
    with pytest.raises(ContentError, match="not valid YAML"):
        ContentStore(tmp_path).load("site.en.yaml")
