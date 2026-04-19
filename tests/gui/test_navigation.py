"""Navigation polish — view zoom, library panel, simulation presets."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("pytestqt")

from pytestqt.qtbot import QtBot

from automata_simulator.core.models import AutomatonType
from automata_simulator.gui.canvas import AutomatonView
from automata_simulator.gui.main_window import MainWindow
from automata_simulator.gui.panels import LibraryPanel
from automata_simulator.gui.panels.test_presets import presets_for


# ------------------------------------------------------------ view nav
class TestViewZoom:
    def test_zoom_in_and_out(self, qtbot: QtBot) -> None:
        view = AutomatonView()
        qtbot.addWidget(view)
        start = view.zoom_factor
        view.zoom_in()
        after_in = view.zoom_factor
        assert after_in > start
        view.zoom_out()
        assert view.zoom_factor == pytest.approx(start)

    def test_zoom_respects_bounds(self, qtbot: QtBot) -> None:
        view = AutomatonView()
        qtbot.addWidget(view)
        for _ in range(20):
            view.zoom_in()
        # Shouldn't exceed the 4.0× ceiling.
        assert view.zoom_factor <= 4.0
        for _ in range(40):
            view.zoom_out()
        assert view.zoom_factor >= 0.25

    def test_fit_in_view_handles_empty_scene(self, qtbot: QtBot) -> None:
        view = AutomatonView()
        qtbot.addWidget(view)
        view.zoom_in()
        view.fit_in_view()
        # Empty scene resets to 1.0.
        assert view.zoom_factor == 1.0

    def test_fit_in_view_adjusts_to_content(self, qtbot: QtBot) -> None:
        view = AutomatonView()
        qtbot.addWidget(view)
        scene = view.automaton_scene
        scene.add_state(0.0, 0.0, state_id="a")
        scene.add_state(1000.0, 0.0, state_id="b")
        view.fit_in_view()
        assert view.zoom_factor != 1.0  # some scale was applied


# ------------------------------------------------------------ library
class TestLibraryPanel:
    def test_populate_from_directory(
        self, qtbot: QtBot, tmp_path: Path,
    ) -> None:
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.jff").write_text("<x/>")
        (tmp_path / "ignore.txt").write_text("nope")
        panel = LibraryPanel(examples_dir=tmp_path)
        qtbot.addWidget(panel)
        names = {p.name for p in panel.entries()}
        assert names == {"a.json", "b.jff"}

    def test_add_entry_dedupes_and_moves_to_top(self, qtbot: QtBot) -> None:
        panel = LibraryPanel()
        qtbot.addWidget(panel)
        panel.add_entry(Path("/tmp/x.json"))
        panel.add_entry(Path("/tmp/y.json"))
        panel.add_entry(Path("/tmp/x.json"))  # dedup + bump
        entries = panel.entries()
        assert entries[0] == Path("/tmp/x.json").resolve()
        assert len(entries) == 2

    def test_load_signal_emits_on_double_click(
        self, qtbot: QtBot, tmp_path: Path,
    ) -> None:
        (tmp_path / "one.json").write_text("{}")
        panel = LibraryPanel(examples_dir=tmp_path)
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.load_requested, timeout=1000) as blocker:
            panel._list.itemActivated.emit(panel._list.item(0))
        assert isinstance(blocker.args[0], Path)
        assert blocker.args[0].name == "one.json"


# ------------------------------------------------------------ presets
class TestPresets:
    def test_known_name_returns_specific_list(self) -> None:
        assert "abb" in presets_for("contains-abb", AutomatonType.DFA)

    def test_unknown_name_falls_back_to_type_default(self) -> None:
        result = presets_for("custom-xyz", AutomatonType.TM)
        assert result  # non-empty


# ------------------------------------------------------------ main window
class TestMainWindowIntegration:
    def test_library_dock_created(self, qtbot: QtBot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        # Library dock widget is reachable as a private attribute.
        assert window._library_panel is not None

    def test_load_path_adds_to_library(self, qtbot: QtBot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        window.load_path(Path("examples/dfa_contains_abb.json"))
        names = {p.name for p in window._library_panel.entries()}
        assert "dfa_contains_abb.json" in names
