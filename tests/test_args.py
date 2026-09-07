"""Unit tests for the automation-demo command-line parsing."""

import json
from pathlib import Path

import pytest

from automated_screenshot_connector.args import is_demo_argv, parse_demo_args


def write_settings(tmp_path: Path, data: object) -> str:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_defaults_without_args() -> None:
    options, rest = parse_demo_args([])
    assert options.demo is None
    assert options.demo_port is None
    assert options.demo_width is None
    assert options.demo_height is None
    assert options.demo_settings == ()
    assert options.demo_language is None
    assert rest == []


def test_demo_language_parsed() -> None:
    options, _ = parse_demo_args(["--automation-demo", "1", "--automation-demo-language", "de"])
    assert options.demo_language == "de"


def test_demo_texts_loaded_from_json_file(tmp_path: Path) -> None:
    path = write_settings(tmp_path, {"price": "preis"})
    options, _ = parse_demo_args(["--automation-demo", "1", "--automation-demo-texts", path])
    assert options.demo_texts == (("price", "preis"),)


def test_demo_texts_default_empty() -> None:
    options, _ = parse_demo_args(["--automation-demo", "1"])
    assert options.demo_texts == ()


def test_demo_texts_missing_file_errors(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        parse_demo_args(
            ["--automation-demo", "1", "--automation-demo-texts", str(tmp_path / "nope.json")]
        )


def test_demo_texts_non_object_json_errors(tmp_path: Path) -> None:
    path = write_settings(tmp_path, ["not", "an", "object"])
    with pytest.raises(SystemExit):
        parse_demo_args(["--automation-demo", "1", "--automation-demo-texts", path])


def test_demo_alone() -> None:
    options, rest = parse_demo_args(["--automation-demo", "1"])
    assert options.demo == 1
    assert rest == []


def test_demo_with_port_and_size() -> None:
    options, _ = parse_demo_args(
        [
            "--automation-demo",
            "2",
            "--automation-demo-port",
            "51234",
            "--automation-demo-width",
            "640",
            "--automation-demo-height",
            "420",
        ]
    )
    assert options.demo == 2
    assert options.demo_port == 51234
    assert options.demo_width == 640
    assert options.demo_height == 420


def test_app_own_args_are_returned_untouched() -> None:
    options, rest = parse_demo_args(["--my-flag", "--automation-demo", "1", "positional"])
    assert options.demo == 1
    assert rest == ["--my-flag", "positional"]


def test_demo_settings_loaded_from_json_file(tmp_path: Path) -> None:
    path = write_settings(tmp_path, {"editor/font_point_size": 18, "window/theme": "dark"})
    options, _ = parse_demo_args(["--automation-demo", "1", "--automation-demo-settings", path])
    assert options.demo_settings == (
        ("editor/font_point_size", "18"),
        ("window/theme", "dark"),
    )


def test_demo_settings_missing_file_errors(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        parse_demo_args(
            ["--automation-demo", "1", "--automation-demo-settings", str(tmp_path / "nope.json")]
        )


def test_demo_settings_non_object_json_errors(tmp_path: Path) -> None:
    path = write_settings(tmp_path, ["not", "an", "object"])
    with pytest.raises(SystemExit):
        parse_demo_args(["--automation-demo", "1", "--automation-demo-settings", path])


def test_demo_settings_invalid_json_errors(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SystemExit):
        parse_demo_args(["--automation-demo", "1", "--automation-demo-settings", str(path)])


def test_settings_file_without_demo_errors(tmp_path: Path) -> None:
    path = write_settings(tmp_path, {"a": "b"})
    with pytest.raises(SystemExit):
        parse_demo_args(["--automation-demo-settings", path])


@pytest.mark.parametrize(
    "argv",
    [
        ["--automation-demo-port", "5000"],
        ["--automation-demo-width", "640"],
        ["--automation-demo-height", "420"],
        ["--automation-demo-language", "de"],
        ["--automation-demo-texts", "texts.json"],
    ],
)
def test_demo_options_without_demo_error(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        parse_demo_args(argv)


def test_is_demo_argv_spots_the_flag():
    assert is_demo_argv(["--automation-demo", "1"])
    assert is_demo_argv(["--gui", "--automation-demo=2", "5m"])


def test_is_demo_argv_ignores_a_run_that_is_not_a_demo():
    assert not is_demo_argv(["--gui", "5m"])
    # The sub-options alone are not a demo run: parse_demo_args rejects them.
    assert not is_demo_argv(["--automation-demo-port", "51942"])
