"""A Qt binding stand-in rich enough to run the players.

``test_qtbind.py`` has fakes of its own, but deliberately minimal ones: what it
tests is the one thing PySide6 and PyQt5 disagree about. The players need real
behaviour instead - a QObject to inherit from, a QTimer that hands its callbacks
to the test, an application whose exit is observable - so that fake lives here.

No Qt binding is installed in this repo (apps bring their own), which is why the
modules are fabricated into ``sys.modules`` rather than imported.
"""

from __future__ import annotations

import importlib
import sys
import types


class FakeTimer:
    """QTimer stand-in: singleShot queues the callback for the test to fire."""

    scheduled: list[tuple[int, object]] = []

    @staticmethod
    def singleShot(delay, callback, *rest):  # noqa: N802 - mirrors Qt's spelling
        # The three-argument form is (delay, context, callback).
        FakeTimer.scheduled.append((delay, rest[0] if rest else callback))

    @staticmethod
    def fire_all() -> None:
        """Run every queued callback, oldest first, clearing the queue."""
        while FakeTimer.scheduled:
            _delay, callback = FakeTimer.scheduled.pop(0)
            callback()


class FakeCoreApplication:
    """Records the exit the player asks for; ``quit`` records too, so a test can
    tell the two apart (only ``exit`` survives a window that refuses to close)."""

    exit_codes: list[int] = []
    quit_calls: int = 0

    @staticmethod
    def exit(code=0):
        FakeCoreApplication.exit_codes.append(code)

    @staticmethod
    def quit():
        FakeCoreApplication.quit_calls += 1

    @staticmethod
    def setApplicationName(name):  # noqa: N802 - mirrors Qt's spelling
        pass


class FakeApplication(FakeCoreApplication):
    """QApplication stand-in. ``focus`` is what the *application* reports, i.e.
    ``None`` whenever the window is not the active one."""

    focus = None
    posted: list[tuple[object, object]] = []
    running = FakeCoreApplication  # what instance() answers

    @staticmethod
    def instance():
        return FakeApplication.running

    @staticmethod
    def focusWidget():  # noqa: N802 - mirrors Qt's spelling
        return FakeApplication.focus

    @staticmethod
    def postEvent(target, event):  # noqa: N802 - mirrors Qt's spelling
        FakeApplication.posted.append((target, event))


class FakeObject:
    """QObject stand-in: takes a parent, keeps nothing."""

    def __init__(self, parent=None):
        self._parent = parent


class FakeWindow(FakeObject):
    """A window that records the activation the player performs on it."""

    def __init__(self, focus_child=None):
        super().__init__()
        self.focus_child = focus_child
        self.raised = 0
        self.activated = 0

    def focusWidget(self):  # noqa: N802 - mirrors Qt's spelling
        return self.focus_child

    def raise_(self):
        self.raised += 1

    def activateWindow(self):  # noqa: N802 - mirrors Qt's spelling
        self.activated += 1


def install(monkeypatch):
    """Put the fake PySide6 on sys.modules and return a fresh ``qt`` module."""
    FakeTimer.scheduled = []
    FakeCoreApplication.exit_codes = []
    FakeCoreApplication.quit_calls = 0
    FakeApplication.focus = None
    FakeApplication.posted = []
    FakeApplication.running = FakeCoreApplication

    monkeypatch.setitem(sys.modules, "PyQt5", None)
    for sub in ("QtCore", "QtGui", "QtWidgets"):
        monkeypatch.setitem(sys.modules, f"PyQt5.{sub}", None)

    root = types.ModuleType("PySide6")
    core = types.ModuleType("PySide6.QtCore")
    gui = types.ModuleType("PySide6.QtGui")
    widgets = types.ModuleType("PySide6.QtWidgets")

    class FakeModifier:
        NoModifier = 0
        ShiftModifier = 0x02000000
        ControlModifier = 0x04000000
        AltModifier = 0x08000000
        MetaModifier = 0x10000000
        KeypadModifier = 0x20000000
        GroupSwitchModifier = 0x40000000

    class FakeKey:
        Key_Return = 0x01000004
        Key_unknown = 0x01FFFFFF

        def __new__(cls, value):
            return value

    class FakeQt:
        KeyboardModifier = FakeModifier
        Key = FakeKey

        @staticmethod
        def KeyboardModifiers(value):  # noqa: N802 - mirrors PyQt5's spelling
            return value

    core.Qt = FakeQt
    core.QCoreApplication = FakeCoreApplication
    core.QObject = FakeObject
    core.QTimer = FakeTimer
    core.QEvent = type("QEvent", (), {"Type": type("Type", (), {"KeyPress": 6})})
    core.QSettings = type("QSettings", (), {})
    gui.QKeyEvent = type("QKeyEvent", (), {"__init__": lambda self, *a: None})
    gui.QKeySequence = type("QKeySequence", (), {})
    widgets.QApplication = FakeApplication
    widgets.QPlainTextEdit = FakeObject
    widgets.QWidget = FakeObject

    for name, module in (
        ("PySide6", root),
        ("PySide6.QtCore", core),
        ("PySide6.QtGui", gui),
        ("PySide6.QtWidgets", widgets),
    ):
        monkeypatch.setitem(sys.modules, name, module)
    for name in ("automated_screenshot_connector._qtbind", "automated_screenshot_connector.qt"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    return importlib.import_module("automated_screenshot_connector.qt")
