"""Qt integration: the two demo players and the demo-settings bootstrap.

Importing this module requires a Qt binding - PySide6 or PyQt5, whichever the
app already has (see ``_qtbind``). The rest of the library stays stdlib-only
for non-Qt apps.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from automated_screenshot_connector._qtbind import (
    QApplication,
    QCoreApplication,
    QEvent,
    QKeyEvent,
    QKeySequence,
    QObject,
    QPlainTextEdit,
    QSettings,
    Qt,
    QTimer,
    QWidget,
    key_of,
    split_combo,
)
from automated_screenshot_connector.client import DemoClient
from automated_screenshot_connector.steps import (
    END_HOLD_MS,
    START_DELAY_MS,
    Action,
    CustomStep,
    DemoScript,
    InsertChar,
    PressReturn,
    SendKey,
    SendScreenshot,
    flatten,
)

# START_DELAY_MS/END_HOLD_MS are re-exported: they belong to the players, but
# live in steps.py so estimated_duration can count them without importing Qt.
__all__ = [
    "END_HOLD_MS",
    "START_DELAY_MS",
    "DemoPlayer",
    "KeyEventDemoPlayer",
    "prepare_demo_settings",
]


def prepare_demo_settings(app_name: str, settings: Iterable[tuple[str, str]]) -> None:
    """Redirect QSettings to a wiped temp INI namespace and seed app settings.

    Gives every demo run a deterministic clean state without touching the
    user's real settings (registry keys can refuse deletion). Call after
    creating the QApplication and before building the main window.

    Args:
        app_name: Demo application name (e.g. "MyApp-Demo") - also names the
            temp settings folder.
        settings: (QSettings key, value) pairs from --automation-demo-settings.
    """
    settings_dir = Path(tempfile.gettempdir()) / f"{app_name.lower()}-settings"
    shutil.rmtree(settings_dir, ignore_errors=True)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(settings_dir))
    QCoreApplication.setApplicationName(app_name)
    seeded = QSettings()
    for key, value in settings:
        seeded.setValue(key, value)
    seeded.sync()


class DemoPlayer(QObject):
    """Plays one DemoScript against a QPlainTextEdit, then quits the app.

    Drives everything through single-shot QTimers so the event loop never
    blocks and live updates/painting happen exactly as with human typing.
    """

    def __init__(
        self,
        input_edit: QPlainTextEdit,
        client: DemoClient,
        script: DemoScript,
        hwnd: int | None,
    ) -> None:
        super().__init__(input_edit)
        self._input = input_edit
        self._client = client
        self._script = script
        self._hwnd = hwnd
        self._actions = flatten(script.steps)
        self._index = 0

    def start(self) -> None:
        QTimer.singleShot(START_DELAY_MS, self._begin)

    def _begin(self) -> None:
        self._client.send_started(self._script.id, self._hwnd)
        self._advance()

    def _advance(self) -> None:
        if self._index >= len(self._actions):
            self._finish()
            return
        delay, action = self._actions[self._index]
        self._index += 1
        QTimer.singleShot(delay, lambda: self._execute(action))

    def _execute(self, action: Action) -> None:
        if isinstance(action, InsertChar):
            self._type_char(action.char)
        elif isinstance(action, PressReturn):
            self._press_return()
        elif isinstance(action, SendScreenshot):
            self._client.send_screenshot(action.name)
        # Wait: the delay already happened in the timer.
        self._advance()

    def _type_char(self, ch: str) -> None:
        # Plain cursor insertion fires textChanged, so the app reacts exactly
        # as it would to human typing.
        self._input.textCursor().insertText(ch)

    def _press_return(self) -> None:
        # A real key event so the widget's keyPressEvent runs (commands etc.)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        QApplication.postEvent(self._input, event)

    def _finish(self) -> None:
        self._client.send_ended(self._script.id)
        self._client.close()
        instance = QApplication.instance()
        if instance is not None:
            QTimer.singleShot(END_HOLD_MS, instance.quit)


class KeyEventDemoPlayer(QObject):
    """Plays a DemoScript by posting real key events to the focused widget.

    For shortcut-driven apps (command palettes, search dialogs, viewers):
    TypeText chars and PressKey chords arrive as QKeyEvents at
    ``QApplication.focusWidget()``, so modal ``exec()`` dialogs receive them
    too - QTimers keep firing inside nested modal event loops.

    Subclass and override ``handle_step`` to execute app-specific steps; any
    step type ``flatten`` doesn't know arrives there wrapped unchanged.
    """

    def __init__(
        self,
        window: QWidget,
        client: DemoClient,
        script: DemoScript,
        hwnd: int | None,
    ) -> None:
        super().__init__(window)
        self._window = window
        self._client = client
        self._script = script
        self._hwnd = hwnd
        self._actions = flatten(script.steps)
        self._index = 0
        self._check_chords()

    def start(self) -> None:
        QTimer.singleShot(START_DELAY_MS, self._begin)

    def handle_step(self, step: object) -> None:
        """Execute an app-defined step. Default: unknown steps are an error."""
        raise ValueError(f"Unhandled demo step: {step!r}")

    def _check_chords(self) -> None:
        """Reject an unparsable chord now, not minutes into a recording."""
        for _, action in self._actions:
            if isinstance(action, SendKey):
                self._parse_chord(action.chord)

    def _begin(self) -> None:
        self._client.send_started(self._script.id, self._hwnd)
        self._advance()

    def _advance(self) -> None:
        if self._index >= len(self._actions):
            self._finish()
            return
        delay, action = self._actions[self._index]
        self._index += 1
        QTimer.singleShot(delay, lambda: self._execute(action))

    def _execute(self, action: Action) -> None:
        if isinstance(action, InsertChar):
            self._send_char(action.char)
        elif isinstance(action, PressReturn):
            self._send_chord("Return")
        elif isinstance(action, SendKey):
            self._send_chord(action.chord)
        elif isinstance(action, SendScreenshot):
            self._client.send_screenshot(action.name)
        elif isinstance(action, CustomStep):
            self.handle_step(action.step)
        # Wait: the delay already happened in the timer.
        self._advance()

    def _target(self) -> QWidget:
        return QApplication.focusWidget() or self._window

    def _send_char(self, ch: str) -> None:
        # Real press+release carrying the char as text, so line edits and
        # views react exactly as to human typing (live filtering included).
        key = key_of(QKeySequence(ch.upper()))
        self._post(self._target(), key, Qt.KeyboardModifier.NoModifier, ch)

    def _parse_chord(self, chord: str) -> tuple[Any, Any]:
        seq = QKeySequence.fromString(chord)
        if seq.count() != 1:
            raise ValueError(f"Not a single key chord: {chord!r}")
        return split_combo(seq)

    def _send_chord(self, chord: str) -> None:
        key, mods = self._parse_chord(chord)
        self._post(self._target(), key, mods)

    def _post(self, target: QWidget, key: Any, mods: Any, text: str = "") -> None:
        QApplication.postEvent(target, QKeyEvent(QEvent.Type.KeyPress, key, mods, text))
        QApplication.postEvent(target, QKeyEvent(QEvent.Type.KeyRelease, key, mods, text))

    def _finish(self) -> None:
        self._client.send_ended(self._script.id)
        self._client.close()
        instance = QApplication.instance()
        if instance is not None:
            QTimer.singleShot(END_HOLD_MS, instance.quit)
