"""App-side connector for the automated-application-screenshots demo tool.

Core (stdlib-only): step model, demo registry, socket client, CLI parsing.
Qt apps additionally import ``automated_screenshot_connector.qt`` for the
two players and the demo QSettings bootstrap; it works with PySide6 or
PyQt5, whichever the app has.
"""

from automated_screenshot_connector.args import (
    DEMO_FLAG,
    DemoOptions,
    is_demo_argv,
    parse_demo_args,
)
from automated_screenshot_connector.client import DemoClient
from automated_screenshot_connector.registry import (
    DemoRegistry,
    ScriptFactory,
    UnknownDemoError,
)
from automated_screenshot_connector.steps import (
    DEFAULT_CHAR_DELAY_MS,
    END_HOLD_MS,
    SCREENSHOT_SETTLE_MS,
    START_DELAY_MS,
    Action,
    Command,
    CustomStep,
    DemoScript,
    InsertChar,
    Pause,
    PressKey,
    PressReturn,
    Screenshot,
    SendKey,
    SendScreenshot,
    Step,
    TypeText,
    Wait,
    estimated_duration,
    flatten,
    localize_script,
)

__all__ = [
    "DEFAULT_CHAR_DELAY_MS",
    "END_HOLD_MS",
    "SCREENSHOT_SETTLE_MS",
    "START_DELAY_MS",
    "Action",
    "Command",
    "CustomStep",
    "DemoClient",
    "DEMO_FLAG",
    "DemoOptions",
    "DemoRegistry",
    "DemoScript",
    "InsertChar",
    "Pause",
    "PressKey",
    "PressReturn",
    "Screenshot",
    "SendKey",
    "ScriptFactory",
    "SendScreenshot",
    "Step",
    "TypeText",
    "UnknownDemoError",
    "Wait",
    "estimated_duration",
    "flatten",
    "localize_script",
    "is_demo_argv",
    "parse_demo_args",
]
