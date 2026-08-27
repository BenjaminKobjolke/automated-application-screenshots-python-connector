"""The demos an app can play, looked up by the id the tool asks for.

Apps otherwise grow a dict, a hand-written "unknown id" error and a lookup
function that special-cases the generated demos. This is that, once.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from automated_screenshot_connector.steps import DemoScript

ScriptFactory = Callable[..., DemoScript]


class UnknownDemoError(LookupError):
    """No demo with the requested id; the message lists the ones there are."""


class DemoRegistry:
    """Maps ``--automation-demo <id>`` to a DemoScript.

    A demo is registered either as a finished script or as a factory called at
    lookup time. The factory is what keeps a *generated* demo honest - one
    screenshot per installed theme, plugin or locale stays complete without
    anyone remembering to edit a list when one is added.
    """

    def __init__(self) -> None:
        self._scripts: dict[int, DemoScript] = {}
        self._factories: dict[int, tuple[str, ScriptFactory]] = {}

    def add(self, *scripts: DemoScript) -> None:
        """Register finished scripts."""
        for script in scripts:
            self._claim(script.id)
            self._scripts[script.id] = script

    def add_all(self, scripts: dict[int, DemoScript]) -> None:
        """Register an id -> script mapping (a module-level DEMOS dict)."""
        self.add(*scripts.values())

    def add_factory(self, demo_id: int, name: str, factory: ScriptFactory) -> None:
        """Register a demo built on demand; ``get`` passes its params through."""
        self._claim(demo_id)
        self._factories[demo_id] = (name, factory)

    def get(self, demo_id: int, **params: Any) -> DemoScript:
        """The script for ``demo_id``.

        ``params`` reach a factory as keyword arguments and are ignored by a
        finished script, so a caller can pass the same ones for every id.

        Raises:
            UnknownDemoError: No demo is registered under that id.
        """
        if demo_id in self._scripts:
            return self._scripts[demo_id]
        if demo_id in self._factories:
            name, factory = self._factories[demo_id]
            script = factory(**params)
            if script.id != demo_id:
                raise ValueError(
                    f"Factory for demo {demo_id} ('{name}') returned a script with "
                    f"id {script.id}; the ids must match or the tool records the "
                    f"wrong demo."
                )
            return script
        raise UnknownDemoError(
            f"No demo with id {demo_id} (available: "
            f"{', '.join(str(i) for i in self.ids())})"
        )

    def ids(self) -> list[int]:
        """Every registered id, sorted."""
        return sorted(set(self._scripts) | set(self._factories))

    def name_of(self, demo_id: int) -> str:
        """The demo's name, without building a factory's script."""
        if demo_id in self._scripts:
            return self._scripts[demo_id].name
        if demo_id in self._factories:
            return self._factories[demo_id][0]
        raise UnknownDemoError(f"No demo with id {demo_id}")

    def __contains__(self, demo_id: object) -> bool:
        return demo_id in self._scripts or demo_id in self._factories

    def _claim(self, demo_id: int) -> None:
        if demo_id in self:
            raise ValueError(f"Demo id {demo_id} is already registered")
