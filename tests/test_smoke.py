"""Smoke tests: package imports cleanly and exposes a version string."""

from __future__ import annotations

import re

import automata_simulator
from automata_simulator.cli.main import main as cli_main
from automata_simulator.gui.main import main as gui_main


def test_version_is_pep440_string() -> None:
    assert isinstance(automata_simulator.__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+", automata_simulator.__version__)


def test_cli_stub_runs() -> None:
    assert cli_main() == 0


def test_gui_stub_runs() -> None:
    assert gui_main() == 0
