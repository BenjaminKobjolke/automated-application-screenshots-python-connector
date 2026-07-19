"""Framework-free demo step model and its scheduler.

A demo is a tuple of high-level steps; ``flatten`` expands them into atomic
timed actions a player executes one timer shot at a time.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_CHAR_DELAY_MS = 60
# Delay before a screenshot so the UI has settled from the previous action
# (>= the recording tool's frame interval).
SCREENSHOT_SETTLE_MS = 400


@dataclass(frozen=True)
class TypeText:
    """Type ``text`` char by char, like a human ('\\n' starts a new line)."""

    text: str
    char_delay_ms: int = DEFAULT_CHAR_DELAY_MS


@dataclass(frozen=True)
class Pause:
    """Do nothing for ``seconds`` (lets viewers read the result)."""

    seconds: float


@dataclass(frozen=True)
class Command:
    """Type a full command line (e.g. "/clear") and press Return."""

    line: str


@dataclass(frozen=True)
class Screenshot:
    """Ask the recording tool to save a named still of the current state."""

    name: str


Step = TypeText | Pause | Command | Screenshot


@dataclass(frozen=True)
class DemoScript:
    """One playable demo: a stable id, an output-folder-friendly name, steps."""

    id: int
    name: str
    steps: tuple[Step, ...]


def localize_script(script: DemoScript, texts: Mapping[str, str]) -> DemoScript:
    """Fill ``{placeholder}``s in TypeText/Command steps from ``texts``.

    Empty ``texts`` returns the script unchanged, so non-localized demos and
    manual runs (no --automation-demo-texts) keep working. Screenshot names
    are never localized — they must stay stable filenames.
    """
    if not texts:
        return script
    steps: list[Step] = []
    for step in script.steps:
        try:
            if isinstance(step, TypeText):
                step = TypeText(step.text.format(**texts), step.char_delay_ms)
            elif isinstance(step, Command):
                step = Command(step.line.format(**texts))
        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Demo '{script.name}': no text for placeholder {e} "
                f"(available: {', '.join(sorted(texts))})"
            ) from e
        steps.append(step)
    return DemoScript(id=script.id, name=script.name, steps=tuple(steps))


# --- atomic actions a player executes ---------------------------------------


@dataclass(frozen=True)
class InsertChar:
    char: str


@dataclass(frozen=True)
class PressReturn:
    pass


@dataclass(frozen=True)
class SendScreenshot:
    name: str


@dataclass(frozen=True)
class Wait:
    pass


Action = InsertChar | PressReturn | SendScreenshot | Wait


def flatten(steps: tuple[Step, ...]) -> list[tuple[int, Action]]:
    """Expand steps into ``(delay_ms_before_action, action)`` pairs, in order."""
    actions: list[tuple[int, Action]] = []
    for step in steps:
        if isinstance(step, TypeText):
            actions.extend((step.char_delay_ms, InsertChar(c)) for c in step.text)
        elif isinstance(step, Pause):
            actions.append((int(step.seconds * 1000), Wait()))
        elif isinstance(step, Command):
            actions.extend((DEFAULT_CHAR_DELAY_MS, InsertChar(c)) for c in step.line)
            actions.append((DEFAULT_CHAR_DELAY_MS, PressReturn()))
        else:
            actions.append((SCREENSHOT_SETTLE_MS, SendScreenshot(step.name)))
    return actions
