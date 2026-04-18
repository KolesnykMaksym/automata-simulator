"""Smoke tests: package imports cleanly and exposes a version string."""

from __future__ import annotations

import re

from click.testing import CliRunner

import automata_simulator
from automata_simulator.cli.main import main as cli_main
from automata_simulator.gui.main import main as gui_main


def test_version_is_pep440_string() -> None:
    assert isinstance(automata_simulator.__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+", automata_simulator.__version__)


def test_cli_help_runs() -> None:
    result = CliRunner().invoke(cli_main, ["--help"])
    assert result.exit_code == 0
    assert "automata" in result.output.lower()


def test_gui_stub_runs() -> None:
    assert gui_main() == 0
