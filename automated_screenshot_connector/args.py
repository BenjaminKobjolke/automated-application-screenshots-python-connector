"""Command-line parsing for the automation-demo contract.

``parse_demo_args`` consumes only the ``--automation-demo*`` options and
returns everything else, so apps keep their own CLI untouched.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class DemoOptions:
    """Parsed automation-demo command-line options."""

    demo: int | None = None
    demo_port: int | None = None
    demo_width: int | None = None
    demo_height: int | None = None
    demo_settings: tuple[tuple[str, str], ...] = ()


def parse_demo_args(argv: Sequence[str]) -> tuple[DemoOptions, list[str]]:
    """Parse the automation-demo options out of ``argv``.

    Returns:
        The parsed options and the leftover arguments that belong to the app.

    Raises:
        SystemExit: On demo options given without --automation-demo, or a
            malformed --automation-demo-set entry.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--automation-demo", type=int, dest="demo", metavar="ID")
    parser.add_argument("--automation-demo-port", type=int, dest="demo_port", metavar="PORT")
    parser.add_argument("--automation-demo-width", type=int, dest="demo_width", metavar="PX")
    parser.add_argument("--automation-demo-height", type=int, dest="demo_height", metavar="PX")
    parser.add_argument(
        "--automation-demo-set",
        action="append",
        dest="demo_settings",
        default=[],
        metavar="KEY=VALUE",
        help="app-specific demo setting, repeatable",
    )
    ns, rest = parser.parse_known_args(list(argv))
    if ns.demo is None and (
        ns.demo_port is not None
        or ns.demo_width is not None
        or ns.demo_height is not None
        or ns.demo_settings
    ):
        parser.error("--automation-demo-* options require --automation-demo")
    pairs = []
    for entry in ns.demo_settings:
        key, sep, value = entry.partition("=")
        if not sep or not key:
            parser.error(f"--automation-demo-set expects KEY=VALUE, got '{entry}'")
        pairs.append((key, value))
    options = DemoOptions(
        demo=ns.demo,
        demo_port=ns.demo_port,
        demo_width=ns.demo_width,
        demo_height=ns.demo_height,
        demo_settings=tuple(pairs),
    )
    return options, rest
