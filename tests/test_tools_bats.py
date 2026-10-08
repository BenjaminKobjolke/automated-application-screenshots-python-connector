"""Static checks for batch files offered as Tickets Watcher commands."""

import re
from pathlib import Path

import pytest


TOOLS = Path(__file__).parent.parent / "tools"
SCRIPTS = sorted((*TOOLS.glob("*.bat"), *TOOLS.glob("*.cmd")))


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda script: script.name)
def test_batch_command_compatibility(script: Path) -> None:
    lines = script.read_text(encoding="utf-8").splitlines()
    last_line = next((line for line in reversed(lines) if line.strip()), "")
    assert last_line.strip().lower().startswith("exit /b")
    for line in lines:
        stripped = line.strip()
        assert not re.fullmatch(r"@?pause(?:\s*[<>].*)?", stripped, re.IGNORECASE)
        if re.match(r"@?start\s", stripped, re.IGNORECASE):
            assert re.search(r"/wait\b", stripped, re.IGNORECASE)
