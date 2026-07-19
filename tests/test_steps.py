"""Unit tests for the framework-free demo step model, flatten(), and localize_script()."""

import pytest

from automated_screenshot_connector.steps import (
    SCREENSHOT_SETTLE_MS,
    Command,
    DemoScript,
    InsertChar,
    Pause,
    PressReturn,
    Screenshot,
    SendScreenshot,
    TypeText,
    Wait,
    flatten,
    localize_script,
)


def test_type_text_expands_to_per_char_actions() -> None:
    actions = flatten((TypeText("1+1", char_delay_ms=50),))
    assert actions == [
        (50, InsertChar("1")),
        (50, InsertChar("+")),
        (50, InsertChar("1")),
    ]


def test_pause_becomes_wait_with_ms_delay() -> None:
    assert flatten((Pause(1.5),)) == [(1500, Wait())]


def test_command_types_chars_then_presses_return() -> None:
    actions = flatten((Command("/clear"),))
    assert actions[:-1] == [(60, InsertChar(c)) for c in "/clear"]
    assert actions[-1] == (60, PressReturn())


def test_screenshot_settles_before_sending() -> None:
    assert flatten((Screenshot("shot"),)) == [(SCREENSHOT_SETTLE_MS, SendScreenshot("shot"))]


def test_steps_flatten_in_order() -> None:
    actions = flatten((TypeText("2"), Pause(0.1), Screenshot("s")))
    assert [a for _, a in actions] == [InsertChar("2"), Wait(), SendScreenshot("s")]


LOCALIZABLE = DemoScript(
    id=1,
    name="demo",
    steps=(
        TypeText("{price} = 20\n", char_delay_ms=42),
        Pause(0.5),
        Command("/{cmd}"),
        Screenshot("still-{price}"),
    ),
)


def test_localize_script_substitutes_typetext_and_command() -> None:
    script = localize_script(LOCALIZABLE, {"price": "preis", "cmd": "clear"})
    assert script.steps[0] == TypeText("preis = 20\n", char_delay_ms=42)
    assert script.steps[2] == Command("/clear")


def test_localize_script_leaves_pause_and_screenshot_untouched() -> None:
    script = localize_script(LOCALIZABLE, {"price": "preis", "cmd": "clear"})
    assert script.steps[1] == Pause(0.5)
    assert script.steps[3] == Screenshot("still-{price}")


def test_localize_script_empty_texts_returns_script_unchanged() -> None:
    assert localize_script(LOCALIZABLE, {}) is LOCALIZABLE


def test_localize_script_missing_placeholder_raises_value_error() -> None:
    with pytest.raises(ValueError, match="cmd"):
        localize_script(LOCALIZABLE, {"price": "preis"})
