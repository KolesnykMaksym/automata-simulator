"""Smoke tests: package imports cleanly and exposes a version string."""

from __future__ import annotations

import re

from click.testing import CliRunner

import automata_simulator
from automata_simulator.cli.main import main as cli_main
from automata_simulator.gui import main as gui_main_module


def test_version_is_pep440_string() -> None:
    assert isinstance(automata_simulator.__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+", automata_simulator.__version__)


def test_cli_help_runs() -> None:
    result = CliRunner().invoke(cli_main, ["--help"])
    assert result.exit_code == 0
    assert "automata" in result.output.lower()


def test_gui_entry_point_is_callable() -> None:
    # We don't actually invoke main() — it would start Qt's event loop.
    # The MainWindow itself is exercised by tests/gui/test_main_window.py.
    assert callable(gui_main_module.main)
