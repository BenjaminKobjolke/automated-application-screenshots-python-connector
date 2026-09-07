# automated-screenshot-connector

App-side Python connector for the
[automated-application-screenshots](../automated-application-screenshots) demo
recording tool. Implements the automation contract (see that repo's
`docs/AUTOMATION_INTERFACE.md`): CLI args, socket events, a demo registry, and
— for Qt apps — two players and deterministic demo settings.

## What's inside

| Module | Needs | Purpose |
|---|---|---|
| `automated_screenshot_connector.steps` | stdlib | Step model (`TypeText`, `Pause`, `Command`, `Screenshot`, `PressKey`), `DemoScript`, `flatten` scheduler, `localize_script` (fills `{placeholder}`s from the `--automation-demo-texts` JSON), `estimated_duration` |
| `automated_screenshot_connector.registry` | stdlib | `DemoRegistry` — id → script lookup, demos generated on demand by a factory, `UnknownDemoError` listing the available ids |
| `automated_screenshot_connector.client` | stdlib | `DemoClient` — sends `demo_started`/`screenshot`/`demo_ended` JSON events; no-op without a port |
| `automated_screenshot_connector.args` | stdlib | `is_demo_argv(argv)` (is this a demo run?), `DEMO_FLAG`, `parse_demo_args(argv) -> (DemoOptions, leftover_args)` — consumes only `--automation-demo*` options, incl. `--automation-demo-language` (per-run UI language, `options.demo_language`) |
| `automated_screenshot_connector.qt` | PySide6 or PyQt5 (yours) | `DemoPlayer` (types into a `QPlainTextEdit` via QTimer chain), `KeyEventDemoPlayer` (posts real `QKeyEvent`s to the focused widget, so command palettes and modal dialogs work) + `prepare_demo_settings` (wiped temp-INI QSettings namespace, seeds the pairs loaded from `--automation-demo-settings`) |

The library has **no runtime dependencies**. `qt` imports a Qt binding only
when you import it, and takes PySide6 or PyQt5 — whichever the app already has
— so a PyQt5 app does not have to fork the player. Non-Qt apps just use the
core modules and write their own.

## Install (uv path dependency)

```toml
# pyproject.toml
dependencies = ["automated-screenshot-connector"]

[tool.uv.sources]
automated-screenshot-connector = { path = "../automated-application-screenshots-python-connector" }
```

## Usage (Qt app)

```python
import sys
from automated_screenshot_connector import DemoClient, parse_demo_args

def main() -> int:
    options, _rest = parse_demo_args(sys.argv[1:])
    app = QApplication(sys.argv)
    app.setOrganizationName("YourOrg")
    if options.demo is not None:
        from automated_screenshot_connector.qt import DemoPlayer, prepare_demo_settings
        prepare_demo_settings("YourApp-Demo", options.demo_settings)
    else:
        app.setApplicationName("YourApp")
    window = MainWindow()
    if options.demo is not None:
        from automated_screenshot_connector.qt import DemoPlayer
        from your_app.demo_scripts import REGISTRY   # your DemoRegistry
        if options.demo_width is not None and options.demo_height is not None:
            window.resize(options.demo_width, options.demo_height)
        client = DemoClient(options.demo_port)
        window.show()
        player = DemoPlayer(window.input_edit, client, REGISTRY.get(options.demo),
                            hwnd=int(window.winId()))
        player.start()
    else:
        window.show()
    return app.exec()
```

Demo content stays in your app — `DemoScript`s built from the step types and
registered in a `DemoRegistry`; see [docs/WRITING_DEMOS.md](docs/WRITING_DEMOS.md) for the step
reference and authoring guidelines. FastCalculator (`../calculator`) is the
working reference. The full tool-side contract lives in the tool repo's
`docs/AUTOMATION_INTERFACE.md`.

## Development

```
install.bat           # uv sync
tools\run_tests.bat   # pytest
```

## Dependencies

- Runtime: none (stdlib). `qt` module expects the consuming app to provide PySide6 or PyQt5.
- Dev: pytest, ruff, mypy.
