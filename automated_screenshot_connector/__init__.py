"""App-side connector for the automated-application-screenshots demo tool.

Core (stdlib-only): step model, socket client, CLI arg parsing.
Qt apps additionally import ``automated_screenshot_connector.qt`` for the
typing DemoPlayer and the demo QSettings bootstrap.
"""

from automated_screenshot_connector.args import DemoOptions, parse_demo_args
from automated_screenshot_connector.client import DemoClient
from automated_screenshot_connector.steps import (
    DEFAULT_CHAR_DELAY_MS,
    SCREENSHOT_SETTLE_MS,
    Action,
    Command,
    DemoScript,
    InsertChar,
    Pause,
    PressReturn,
    Screenshot,
    SendScreenshot,
    Step,
    TypeText,
    Wait,
    flatten,
)

__all__ = [
    "DEFAULT_CHAR_DELAY_MS",
    "SCREENSHOT_SETTLE_MS",
    "Action",
    "Command",
    "DemoClient",
    "DemoOptions",
    "DemoScript",
    "InsertChar",
    "Pause",
    "PressReturn",
    "Screenshot",
    "SendScreenshot",
    "Step",
    "TypeText",
    "Wait",
    "flatten",
    "parse_demo_args",
]
