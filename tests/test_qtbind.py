"""The binding shim, against fake Qt modules.

Neither PySide6 nor PyQt5 is installed here (apps bring their own), so both
branches are exercised with stand-ins. What is actually under test is the one
thing the bindings disagree on: how a QKeySequence combination unpacks.
"""

import importlib
import sys
import types

import pytest

# The real Qt modifier bits, so the packing under test is the real packing.
SHIFT = 0x02000000
CONTROL = 0x04000000
ALT = 0x08000000
META = 0x10000000
KEYPAD = 0x20000000
GROUP_SWITCH = 0x40000000
KEY_P = 0x50
KEY_UNKNOWN = 0x01FFFFFF


class _FakeModifier:
    ShiftModifier = SHIFT
    ControlModifier = CONTROL
    AltModifier = ALT
    MetaModifier = META
    KeypadModifier = KEYPAD
    GroupSwitchModifier = GROUP_SWITCH
    NoModifier = 0


class _FakeKey:
    Key_unknown = KEY_UNKNOWN

    def __new__(cls, value):
        return value


class _FakeQt:
    KeyboardModifier = _FakeModifier
    Key = _FakeKey

    @staticmethod
    def KeyboardModifiers(value):  # noqa: N802 - mirrors PyQt5's spelling
        return value


def _install_fake_binding(monkeypatch, name):
    """Put a minimal ``name`` Qt binding on sys.modules and import the shim."""
    for module in ("PySide6", "PyQt5"):
        # None makes `import module` raise ImportError, so only `name` is found.
        monkeypatch.setitem(sys.modules, module, None)
        for sub in ("QtCore", "QtGui", "QtWidgets"):
            monkeypatch.setitem(sys.modules, f"{module}.{sub}", None)

    root = types.ModuleType(name)
    core = types.ModuleType(f"{name}.QtCore")
    gui = types.ModuleType(f"{name}.QtGui")
    widgets = types.ModuleType(f"{name}.QtWidgets")
    core.Qt = _FakeQt
    for symbol in ("QCoreApplication", "QEvent", "QObject", "QSettings", "QTimer"):
        setattr(core, symbol, type(symbol, (), {}))
    for symbol in ("QKeyEvent", "QKeySequence"):
        setattr(gui, symbol, type(symbol, (), {}))
    for symbol in ("QApplication", "QPlainTextEdit", "QWidget"):
        setattr(widgets, symbol, type(symbol, (), {}))

    for module, obj in (
        (name, root),
        (f"{name}.QtCore", core),
        (f"{name}.QtGui", gui),
        (f"{name}.QtWidgets", widgets),
    ):
        monkeypatch.setitem(sys.modules, module, obj)
    monkeypatch.delitem(sys.modules, "automated_screenshot_connector._qtbind", raising=False)
    return importlib.import_module("automated_screenshot_connector._qtbind")


class _FakeSequence:
    """Stands in for a QKeySequence holding one combination."""

    def __init__(self, *combos):
        self._combos = combos

    def __getitem__(self, index):
        return self._combos[index]

    def count(self):
        return len(self._combos)


class _FakeCombination:
    """PySide6's QKeyCombination: key and modifiers already separate."""

    def __init__(self, key, modifiers):
        self._key = key
        self._modifiers = modifiers

    def key(self):
        return self._key

    def keyboardModifiers(self):  # noqa: N802 - mirrors Qt's spelling
        return self._modifiers


def test_pyqt5_split_combo_unpacks_the_int(monkeypatch):
    qtbind = _install_fake_binding(monkeypatch, "PyQt5")
    assert qtbind.BINDING == "PyQt5"
    key, mods = qtbind.split_combo(_FakeSequence(KEY_P | CONTROL | SHIFT))
    assert key == KEY_P
    assert mods == CONTROL | SHIFT


def test_pyqt5_split_combo_without_modifiers(monkeypatch):
    qtbind = _install_fake_binding(monkeypatch, "PyQt5")
    key, mods = qtbind.split_combo(_FakeSequence(KEY_P))
    assert key == KEY_P
    assert mods == 0


def test_pyside6_split_combo_reads_the_combination(monkeypatch):
    qtbind = _install_fake_binding(monkeypatch, "PySide6")
    assert qtbind.BINDING == "PySide6"
    key, mods = qtbind.split_combo(_FakeSequence(_FakeCombination(KEY_P, CONTROL)))
    assert key == KEY_P
    assert mods == CONTROL


@pytest.mark.parametrize("binding", ["PyQt5", "PySide6"])
def test_key_of_empty_sequence_is_unknown(monkeypatch, binding):
    qtbind = _install_fake_binding(monkeypatch, binding)
    assert qtbind.key_of(_FakeSequence()) == KEY_UNKNOWN


def test_key_of_drops_the_modifiers(monkeypatch):
    qtbind = _install_fake_binding(monkeypatch, "PyQt5")
    assert qtbind.key_of(_FakeSequence(KEY_P | ALT)) == KEY_P


def test_no_binding_is_an_actionable_import_error(monkeypatch):
    for module in ("PySide6", "PyQt5"):
        monkeypatch.setitem(sys.modules, module, None)
        for sub in ("QtCore", "QtGui", "QtWidgets"):
            monkeypatch.setitem(sys.modules, f"{module}.{sub}", None)
    monkeypatch.delitem(sys.modules, "automated_screenshot_connector._qtbind", raising=False)
    with pytest.raises(ImportError, match="PySide6 or PyQt5"):
        importlib.import_module("automated_screenshot_connector._qtbind")
