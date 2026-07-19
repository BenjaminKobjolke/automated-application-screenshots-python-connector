"""Unit tests for the automation-demo command-line parsing."""

import pytest

from automated_screenshot_connector.args import parse_demo_args


def test_defaults_without_args() -> None:
    options, rest = parse_demo_args([])
    assert options.demo is None
    assert options.demo_port is None
    assert options.demo_width is None
    assert options.demo_height is None
    assert options.demo_settings == ()
    assert rest == []


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


def test_demo_settings_single_and_repeated() -> None:
    options, _ = parse_demo_args(
        [
            "--automation-demo",
            "1",
            "--automation-demo-set",
            "editor/font_point_size=18",
            "--automation-demo-set",
            "window/theme=dark",
        ]
    )
    assert options.demo_settings == (
        ("editor/font_point_size", "18"),
        ("window/theme", "dark"),
    )


def test_demo_settings_value_may_contain_equals() -> None:
    options, _ = parse_demo_args(["--automation-demo", "1", "--automation-demo-set", "k=a=b"])
    assert options.demo_settings == (("k", "a=b"),)


def test_demo_settings_without_equals_errors() -> None:
    with pytest.raises(SystemExit):
        parse_demo_args(["--automation-demo", "1", "--automation-demo-set", "no-equals-here"])


@pytest.mark.parametrize(
    "argv",
    [
        ["--automation-demo-port", "5000"],
        ["--automation-demo-width", "640"],
        ["--automation-demo-height", "420"],
        ["--automation-demo-set", "a=b"],
    ],
)
def test_demo_options_without_demo_error(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        parse_demo_args(argv)
