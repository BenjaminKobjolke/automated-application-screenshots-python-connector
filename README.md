# automated-screenshot-connector

App-side Python connector for the
[automated-application-screenshots](../automated-application-screenshots) demo
recording tool. Implements the automation contract (see that repo's
`docs/AUTOMATION_INTERFACE.md`): CLI args, socket events, and — for Qt apps —
a typing player and deterministic demo settings.

## What's inside

| Module | Needs | Purpose |
|---|---|---|
| `automated_screenshot_connector.steps` | stdlib | Step model (`TypeText`, `Pause`, `Command`, `Screenshot`), `DemoScript`, `flatten` scheduler |
| `automated_screenshot_connector.client` | stdlib | `DemoClient` — sends `demo_started`/`screenshot`/`demo_ended` JSON events; no-op without a port |
| `automated_screenshot_connector.args` | stdlib | `parse_demo_args(argv) -> (DemoOptions, leftover_args)` — consumes only `--automation-demo*` options |
| `automated_screenshot_connector.qt` | PySide6 (yours) | `DemoPlayer` (types into a `QPlainTextEdit` via QTimer chain) + `prepare_demo_settings` (wiped temp-INI QSettings namespace, seeds `--automation-demo-set` pairs) |

The library has **no runtime dependencies**. `qt` imports PySide6 only when
you import it — non-Qt apps just use the core modules and write their own
player.

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
        from your_app.demo_scripts import DEMOS   # your DemoScript content
        if options.demo_width is not None and options.demo_height is not None:
            window.resize(options.demo_width, options.demo_height)
        client = DemoClient(options.demo_port)
        window.show()
        player = DemoPlayer(window.input_edit, client, DEMOS[options.demo],
                            hwnd=int(window.winId()))
        player.start()
    else:
        window.show()
    return app.exec()
```

Demo content stays in your app — a `DEMOS: dict[int, DemoScript]` built from
the step types; see [docs/WRITING_DEMOS.md](docs/WRITING_DEMOS.md) for the step
reference and authoring guidelines. FastCalculator (`../calculator`) is the
working reference. The full tool-side contract lives in the tool repo's
`docs/AUTOMATION_INTERFACE.md`.

## Development

```
install.bat           # uv sync
tools\run_tests.bat   # pytest
```

## Dependencies

- Runtime: none (stdlib). `qt` module expects the consuming app to provide PySide6.
- Dev: pytest, ruff, mypy.
