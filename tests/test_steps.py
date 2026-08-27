"""Unit tests for the framework-free demo step model, flatten(), and localize_script()."""

import pytest

from automated_screenshot_connector.steps import (
    DEFAULT_CHAR_DELAY_MS,
    SCREENSHOT_SETTLE_MS,
    Command,
    CustomStep,
    DemoScript,
    InsertChar,
    Pause,
    PressKey,
    PressReturn,
    Screenshot,
    SendKey,
    SendScreenshot,
    TypeText,
    Wait,
    estimated_duration,
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


def test_press_key_becomes_send_key() -> None:
    assert flatten((PressKey("Ctrl+Shift+P"),)) == [
        (DEFAULT_CHAR_DELAY_MS, SendKey("Ctrl+Shift+P"))
    ]
    assert flatten((PressKey("Down", delay_ms=200),)) == [(200, SendKey("Down"))]


def test_unknown_step_becomes_custom_step() -> None:
    class OpenFile:
        pass

    step = OpenFile()
    assert flatten((step,)) == [(DEFAULT_CHAR_DELAY_MS, CustomStep(step))]  # type: ignore[arg-type]


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


def test_estimated_duration_counts_delays_and_the_player_hold():
    demo = DemoScript(
        id=1,
        name="d",
        steps=(TypeText("ab", char_delay_ms=100), Pause(2.0), Screenshot("s")),
    )
    # 500 start + 2x100 typing + 2000 pause + 400 screenshot settle + 1000 hold
    assert estimated_duration(demo) == pytest.approx(4.1)


def test_estimated_duration_of_an_empty_script_is_the_hold_alone():
    assert estimated_duration(DemoScript(id=1, name="d", steps=())) == pytest.approx(1.5)
