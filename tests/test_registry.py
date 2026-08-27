import pytest

from automated_screenshot_connector import (
    DemoRegistry,
    DemoScript,
    Pause,
    Screenshot,
    UnknownDemoError,
)


def script(demo_id=1, name="overview"):
    return DemoScript(id=demo_id, name=name, steps=(Pause(1.0),))


def test_add_and_get():
    registry = DemoRegistry()
    demo = script()
    registry.add(demo)
    assert registry.get(1) is demo


def test_add_all_takes_a_demos_dict():
    registry = DemoRegistry()
    demos = {1: script(1, "a"), 2: script(2, "b")}
    registry.add_all(demos)
    assert registry.ids() == [1, 2]
    assert registry.get(2).name == "b"


def test_factory_is_called_at_lookup_with_the_params():
    registry = DemoRegistry()

    def build(names):
        return DemoScript(
            id=2, name="themes", steps=tuple(Screenshot(n) for n in names)
        )

    registry.add_factory(2, "themes", build)
    built = registry.get(2, names=["Dark", "Light"])
    assert [s.name for s in built.steps] == ["Dark", "Light"]


def test_params_are_ignored_by_a_finished_script():
    # The app passes the same params for every id; only factories read them.
    registry = DemoRegistry()
    registry.add(script())
    assert registry.get(1, names=["Dark"]).name == "overview"


def test_factory_returning_a_mismatched_id_is_an_error():
    registry = DemoRegistry()
    registry.add_factory(2, "themes", lambda: script(99, "themes"))
    with pytest.raises(ValueError, match="id 99"):
        registry.get(2)


def test_unknown_id_lists_the_available_ones():
    registry = DemoRegistry()
    registry.add(script(1, "a"), script(3, "b"))
    registry.add_factory(2, "themes", lambda: script(2, "themes"))
    with pytest.raises(UnknownDemoError, match=r"id 7 \(available: 1, 2, 3\)"):
        registry.get(7)


def test_duplicate_id_is_rejected_at_registration():
    registry = DemoRegistry()
    registry.add(script(1))
    with pytest.raises(ValueError, match="already registered"):
        registry.add_factory(1, "themes", lambda: script(1, "themes"))


def test_name_of_does_not_build_the_factory_script():
    registry = DemoRegistry()

    def explode():
        raise AssertionError("factory must not run for a name lookup")

    registry.add_factory(2, "themes", explode)
    assert registry.name_of(2) == "themes"


def test_contains():
    registry = DemoRegistry()
    registry.add(script(1))
    assert 1 in registry
    assert 2 not in registry
