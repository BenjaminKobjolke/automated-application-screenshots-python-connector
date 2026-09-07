"""Command-line parsing for the automation-demo contract.

``parse_demo_args`` consumes only the ``--automation-demo*`` options and
returns everything else, so apps keep their own CLI untouched.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# The flag that turns a normal launch into a demo run. Apps have to look for it
# in raw argv before their own parsing, so it is a constant here rather than a
# string each of them repeats.
DEMO_FLAG = "--automation-demo"


@dataclass(frozen=True)
class DemoOptions:
    """Parsed automation-demo command-line options."""

    demo: int | None = None
    demo_port: int | None = None
    demo_width: int | None = None
    demo_height: int | None = None
    demo_settings: tuple[tuple[str, str], ...] = ()
    demo_language: str | None = None
    demo_texts: tuple[tuple[str, str], ...] = ()


def is_demo_argv(argv: Sequence[str]) -> bool:
    """Is this a demo run? Cheap enough for the first line of an entry point.

    Only ``--automation-demo`` itself counts: the ``-port``/``-width``/... options
    are not a demo run on their own (``parse_demo_args`` rejects them), and this
    is called before any parsing has happened.
    """
    return any(arg == DEMO_FLAG or arg.startswith(f"{DEMO_FLAG}=") for arg in argv)


def parse_demo_args(argv: Sequence[str]) -> tuple[DemoOptions, list[str]]:
    """Parse the automation-demo options out of ``argv``.

    Returns:
        The parsed options and the leftover arguments that belong to the app.

    Raises:
        SystemExit: On demo options given without --automation-demo, or a
            malformed --automation-demo-set entry.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(DEMO_FLAG, type=int, dest="demo", metavar="ID")
    parser.add_argument(f"{DEMO_FLAG}-port", type=int, dest="demo_port", metavar="PORT")
    parser.add_argument(f"{DEMO_FLAG}-width", type=int, dest="demo_width", metavar="PX")
    parser.add_argument(f"{DEMO_FLAG}-height", type=int, dest="demo_height", metavar="PX")
    parser.add_argument(
        f"{DEMO_FLAG}-settings",
        dest="demo_settings_file",
        metavar="PATH",
        help="JSON file (one object) with app-specific demo settings",
    )
    parser.add_argument(
        f"{DEMO_FLAG}-language",
        dest="demo_language",
        metavar="LANG",
        help="UI language code the app should use for this demo run (e.g. 'de')",
    )
    parser.add_argument(
        f"{DEMO_FLAG}-texts",
        dest="demo_texts_file",
        metavar="PATH",
        help="JSON file (one object) with localized demo placeholder texts",
    )
    ns, rest = parser.parse_known_args(list(argv))
    if ns.demo is None and (
        ns.demo_port is not None
        or ns.demo_width is not None
        or ns.demo_height is not None
        or ns.demo_settings_file is not None
        or ns.demo_language is not None
        or ns.demo_texts_file is not None
    ):
        parser.error(f"{DEMO_FLAG}-* options require {DEMO_FLAG}")
    options = DemoOptions(
        demo=ns.demo,
        demo_port=ns.demo_port,
        demo_width=ns.demo_width,
        demo_height=ns.demo_height,
        demo_settings=_load_json_object_file(
            parser, f"{DEMO_FLAG}-settings", ns.demo_settings_file
        ),
        demo_language=ns.demo_language,
        demo_texts=_load_json_object_file(parser, f"{DEMO_FLAG}-texts", ns.demo_texts_file),
    )
    return options, rest


def _load_json_object_file(
    parser: argparse.ArgumentParser, option: str, path: str | None
) -> tuple[tuple[str, str], ...]:
    """Load and validate a one-JSON-object file; values are coerced to strings."""
    if path is None:
        return ()
    file = Path(path)
    if not file.is_file():
        parser.error(f"{option} file not found: {path}")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        parser.error(f"{option} is not valid JSON: {e}")
    if not isinstance(data, dict):
        parser.error(f"{option} must contain a JSON object")
    return tuple((str(key), str(value)) for key, value in data.items())
