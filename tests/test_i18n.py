from __future__ import annotations

from asset_allocator.i18n import _BUCKETS, _UI, LANGUAGES, bucket_label, normalize_lang, t
from asset_allocator.report import format_money


def test_every_language_has_the_same_keys() -> None:
    ui_keys = set(_UI["en"])
    bucket_keys = set(_BUCKETS["en"])
    for lang in LANGUAGES:
        assert set(_UI[lang]) == ui_keys, f"{lang} UI keys differ"
        assert set(_BUCKETS[lang]) == bucket_keys, f"{lang} bucket keys differ"


def test_translate_and_fallbacks() -> None:
    assert t("vi", "net_worth") == "Giá trị ròng"
    assert t("en", "net_worth") == "Net worth"
    assert t("xx", "net_worth") == "Net worth"  # unknown language falls back to en
    assert t("en", "no_such_key") == "no_such_key"  # unknown key falls back to raw


def test_bucket_label() -> None:
    assert bucket_label("vi", "real_estate") == "Bất động sản"
    assert bucket_label("en", "real_estate") == "Real estate"
    assert bucket_label("vi", "unknown_bucket") == "unknown_bucket"


def test_normalize_lang() -> None:
    assert normalize_lang("vi") == "vi"
    assert normalize_lang("en") == "en"
    assert normalize_lang("fr") == "en"


def test_format_money_grouping() -> None:
    assert format_money(34110, "VND", "en") == "34,110 VND"
    assert format_money(34110, "VND", "vi") == "34.110 VND"
    assert format_money(-280, "", "vi") == "-280"
    assert format_money(446.1, "", "en") == "446.10"
    assert format_money(446.1, "", "vi") == "446,10"
    assert format_money(0, "X", "en") == "0 X"
    assert format_money(1234.999, "", "en") == "1,235"  # rounds up cleanly
