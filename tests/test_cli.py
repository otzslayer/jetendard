"""Tests for the Jetendard CLI helpers."""

from __future__ import annotations

import pytest

from jetendard.builder import DEFAULT_VARIANTS, get_variants_by_names
from jetendard.cli import (
    family_file_stem,
    select_variants,
    validate_styles,
    validate_weights,
    write_css,
)


def test_family_file_stem_removes_spaces() -> None:
    assert family_file_stem("Jetendard Mono") == "JetendardMono"


def test_validate_weights_accepts_supported_weights() -> None:
    assert validate_weights(["Regular", "Light", "Bold"]) == ["Regular", "Light", "Bold"]


def test_validate_weights_rejects_unknown_weight() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        validate_weights(["Regular", "Book"])


def test_validate_weights_rejects_black_until_matching_latin_source_exists() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        validate_weights(["Black"])


def test_validate_styles_accepts_supported_styles() -> None:
    assert validate_styles(["normal", "italic", "normal"]) == ["normal", "italic"]


def test_validate_styles_rejects_unknown_style() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        validate_styles(["oblique"])


def test_select_variants_defaults_to_full_coverage() -> None:
    assert select_variants() == list(DEFAULT_VARIANTS)


def test_select_variants_weights_default_to_upright() -> None:
    variants = select_variants(weights=["Regular", "Bold"])
    assert [variant.output_suffix for variant in variants] == ["Regular", "Bold"]


def test_select_variants_weights_and_styles_cross_product() -> None:
    variants = select_variants(weights=["Regular", "Bold"], styles=["normal", "italic"])
    assert [variant.output_suffix for variant in variants] == [
        "Regular",
        "Italic",
        "Bold",
        "BoldItalic",
    ]


def test_select_variants_explicit_names() -> None:
    variants = select_variants(variant_names=["Regular", "BoldItalic"])
    assert [variant.output_suffix for variant in variants] == ["Regular", "BoldItalic"]


def test_select_variants_defaults_to_non_mono_base() -> None:
    variants = select_variants(variant_names=["Regular", "BoldItalic"])
    assert [variant.latin_filename for variant in variants] == [
        "JetBrainsMonoNerdFont-Regular.ttf",
        "JetBrainsMonoNerdFont-BoldItalic.ttf",
    ]


def test_select_variants_mono_flag_uses_mono_base() -> None:
    variants = select_variants(mono=True, variant_names=["Regular", "BoldItalic"])
    assert [variant.latin_filename for variant in variants] == [
        "JetBrainsMonoNerdFontMono-Regular.ttf",
        "JetBrainsMonoNerdFontMono-BoldItalic.ttf",
    ]
    assert select_variants(mono=True)[0].latin_filename == ("JetBrainsMonoNerdFontMono-Thin.ttf")


def test_select_variants_rejects_ambiguous_combinations() -> None:
    with pytest.raises(ValueError, match="--all cannot be combined"):
        select_variants(all_variants=True, weights=["Regular"])
    with pytest.raises(ValueError, match="--variants cannot be combined"):
        select_variants(variant_names=["Regular"], styles=["italic"])


def test_write_css_generates_font_face_rules(tmp_path) -> None:
    variants = get_variants_by_names(["Regular", "Italic", "BoldItalic"])
    css_path = write_css(tmp_path, "Jetendard", variants)
    content = css_path.read_text(encoding="utf-8")

    assert css_path.name == "jetendard.css"
    assert "font-family: 'Jetendard';" in content
    assert "Jetendard-Regular.woff2" in content
    assert "font-weight: 400;" in content
    assert "font-style: normal;" in content
    assert "Jetendard-Italic.woff2" in content
    assert "font-style: italic;" in content
    assert "Jetendard-BoldItalic.woff2" in content
    assert "font-weight: 700;" in content
