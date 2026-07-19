"""Qt integration: the typing DemoPlayer and demo-settings bootstrap.

Importing this module requires PySide6 (which a Qt app already has); the rest
of the library stays stdlib-only for non-Qt apps.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from automated_screenshot_connector.client import DemoClient
from automated_screenshot_connector.steps import (
    Action,
    DemoScript,
    InsertChar,
    PressReturn,
    SendScreenshot,
    flatten,
)

# Give the window one moment to finish first paint before typing starts.
START_DELAY_MS = 500
# Keep the finished state on screen briefly so the recording doesn't end abruptly.
END_HOLD_MS = 1000


def prepare_demo_settings(app_name: str, settings: Iterable[tuple[str, str]]) -> None:
    """Redirect QSettings to a wiped temp INI namespace and seed app settings.

    Gives every demo run a deterministic clean state without touching the
    user's real settings (registry keys can refuse deletion). Call after
    creating the QApplication and before building the main window.

    Args:
        app_name: Demo application name (e.g. "MyApp-Demo") — also names the
            temp settings folder.
        settings: (QSettings key, value) pairs from --automation-demo-set.
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
