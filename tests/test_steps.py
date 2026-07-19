"""Unit tests for the framework-free demo step model and flatten()."""

from automated_screenshot_connector.steps import (
    SCREENSHOT_SETTLE_MS,
    Command,
    InsertChar,
    Pause,
    PressReturn,
    Screenshot,
    SendScreenshot,
    TypeText,
    Wait,
    flatten,
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
