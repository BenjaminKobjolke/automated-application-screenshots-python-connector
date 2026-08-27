"""Qt binding shim: PySide6 if it is installed, otherwise PyQt5.

The player only needs a handful of Qt symbols, and the two bindings agree on
all of them except one: indexing a QKeySequence. PySide6 returns a
QKeyCombination with ``.key()``/``.keyboardModifiers()``; PyQt5 returns a
single int with the key and its modifier bits packed together. ``split_combo``
is that difference, and the only reason this module exists — without it a
PyQt5 app has to fork the whole player to change six lines.

Enums are addressed in the scoped Qt 6 style (``Qt.Key.Key_Return``,
``QEvent.Type.KeyPress``) throughout the package; PyQt5 accepts that spelling
too, so nothing else here has to branch.
"""

from __future__ import annotations

from typing import Any

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, Qt, QTimer
    from PySide6.QtGui import QKeyEvent, QKeySequence
    from PySide6.QtWidgets import QApplication, QPlainTextEdit, QWidget

    BINDING = "PySide6"
except ImportError:  # pragma: no cover - depends on what the app installed
    try:
        from PyQt5.QtCore import QCoreApplication, QEvent, QObject, QSettings, Qt, QTimer
        from PyQt5.QtGui import QKeyEvent, QKeySequence
        from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QWidget

        BINDING = "PyQt5"
    except ImportError as e:
        raise ImportError(
            "automated_screenshot_connector.qt needs PySide6 or PyQt5; the app "
            "is expected to bring one of them."
        ) from e

__all__ = [
    "BINDING",
    "QApplication",
    "QCoreApplication",
    "QEvent",
    "QKeyEvent",
    "QKeySequence",
    "QObject",
    "QPlainTextEdit",
    "QSettings",
    "QTimer",
    "QWidget",
    "Qt",
    "key_of",
    "split_combo",
]

# Every keyboard-modifier bit, for un-packing a PyQt5 combination.
_MODIFIER_MASK = int(
    Qt.KeyboardModifier.ShiftModifier
    | Qt.KeyboardModifier.ControlModifier
    | Qt.KeyboardModifier.AltModifier
    | Qt.KeyboardModifier.MetaModifier
    | Qt.KeyboardModifier.KeypadModifier
    | Qt.KeyboardModifier.GroupSwitchModifier
)


def split_combo(sequence: Any, index: int = 0) -> tuple[Any, Any]:
    """The ``(key, modifiers)`` of one combination of a QKeySequence."""
    combo = sequence[index]
    if isinstance(combo, int):
        # PyQt5: key and modifiers packed into one int.
        return Qt.Key(combo & ~_MODIFIER_MASK), Qt.KeyboardModifiers(combo & _MODIFIER_MASK)
    return Qt.Key(combo.key()), combo.keyboardModifiers()


def key_of(sequence: Any) -> Any:
    """The plain key of the first combination; Key_unknown if there is none."""
    if not sequence.count():
        return Qt.Key.Key_unknown
    return split_combo(sequence)[0]
