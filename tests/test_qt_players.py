"""The players' two contracts with the outside world: where keys land, and how
the app ends.

Both are invisible in a passing unit test elsewhere and expensive in a real
recording - a key posted to the wrong widget records an app doing nothing, and
an app that will not exit is killed by the tool after its grace period.
"""

from fake_qt import FakeApplication, FakeTimer, FakeWindow, install

from automated_screenshot_connector import DemoClient, DemoScript, Pause, Screenshot

SCRIPT = DemoScript(id=1, name="demo", steps=(Pause(0.1), Screenshot("still")))


def _player(qt, window, **kwargs):
    return qt.KeyEventDemoPlayer(window, DemoClient(None), SCRIPT, hwnd=None, **kwargs)


def test_keys_go_to_the_windows_focus_widget_when_the_window_is_not_active(monkeypatch):
    # QApplication.focusWidget() is None unless the window is *active*, which the
    # recording tool does not guarantee (it pins z-order without activating).
    qt = install(monkeypatch)
    focused = object()
    window = FakeWindow(focus_child=focused)
    FakeApplication.focus = None

    assert _player(qt, window)._target() is focused


def test_target_falls_back_to_the_window_when_nothing_has_focus(monkeypatch):
    qt = install(monkeypatch)
    window = FakeWindow(focus_child=None)

    assert _player(qt, window)._target() is window


def test_start_brings_the_window_forward(monkeypatch):
    qt = install(monkeypatch)
    window = FakeWindow()

    _player(qt, window).start()

    assert (window.raised, window.activated) == (1, 1)


def test_finish_exits_the_app_rather_than_asking_it_to_quit(monkeypatch):
    # quit() closes the windows first, and since Qt 6.5 a window that ignores its
    # close event cancels the whole quit - the app then lingers until it is killed.
    qt = install(monkeypatch)
    player = _player(qt, FakeWindow())

    player._finish()
    FakeTimer.fire_all()

    assert FakeApplication.exit_codes == [0]
    assert FakeApplication.quit_calls == 0


def test_exit_when_done_false_leaves_the_app_running(monkeypatch):
    qt = install(monkeypatch)
    player = _player(qt, FakeWindow(), exit_when_done=False)

    player._finish()
    FakeTimer.fire_all()

    assert FakeApplication.exit_codes == []


def test_typing_player_exits_the_same_way(monkeypatch):
    qt = install(monkeypatch)
    player = qt.DemoPlayer(FakeWindow(), DemoClient(None), SCRIPT, hwnd=None)

    player._finish()
    FakeTimer.fire_all()

    assert FakeApplication.exit_codes == [0]


def test_nothing_happens_without_a_running_application(monkeypatch):
    qt = install(monkeypatch)
    FakeApplication.running = None
    player = _player(qt, FakeWindow())

    player._finish()
    FakeTimer.fire_all()

    assert FakeApplication.exit_codes == []
