"""Framework-free demo step model and its scheduler.

A demo is a tuple of high-level steps; ``flatten`` expands them into atomic
timed actions a player executes one timer shot at a time.
"""

from __future__ import annotations

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
