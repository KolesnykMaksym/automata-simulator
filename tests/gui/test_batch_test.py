"""BatchTestDialog tests (pytest-qt, offscreen)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("pytestqt")

from pytestqt.qtbot import QtBot

from automata_simulator.gui.canvas import AutomatonScene, AutomatonView
from automata_simulator.gui.dialogs import BatchTestDialog


@pytest.fixture
def view(qtbot: QtBot) -> AutomatonView:
    v = AutomatonView()
    qtbot.addWidget(v)
    return v


@pytest.fixture
def scene(view: AutomatonView) -> AutomatonScene:
    return view.automaton_scene


def _wire_dfa_ends_ab(scene: AutomatonScene) -> None:
    """DFA over {a,b} accepting strings ending in 'ab'."""
    q0 = scene.add_state(0.0, 0.0, state_id="q0")
    q1 = scene.add_state(100.0, 0.0, state_id="q1")
    q2 = scene.add_state(200.0, 0.0, state_id="q2")
    scene.set_initial(q0)
    q2.set_accepting(True)
    scene.add_transition(q0, q1, "a")
    scene.add_transition(q0, q0, "b")
    scene.add_transition(q1, q1, "a")
    scene.add_transition(q1, q2, "b")
    scene.add_transition(q2, q1, "a")
    scene.add_transition(q2, q0, "b")


class TestBatchTestDialog:
    def test_run_populates_results(self, qtbot: QtBot, scene: AutomatonScene) -> None:
        _wire_dfa_ends_ab(scene)
        dialog = BatchTestDialog(scene)
        qtbot.addWidget(dialog)
        rows = dialog.run_with_inputs(["ab", "aab", "a", "bab"])
        assert len(rows) == 4
        by_input = {r.input: r for r in rows}
        assert by_input["ab"].accepted is True
        assert by_input["aab"].accepted is True
        assert by_input["a"].accepted is False
        assert by_input["bab"].accepted is True

    def test_ui_button_fills_table(self, qtbot: QtBot, scene: AutomatonScene) -> None:
        _wire_dfa_ends_ab(scene)
        dialog = BatchTestDialog(scene)
        qtbot.addWidget(dialog)
        dialog._input_edit.setPlainText("ab\nba\n")
        dialog._run_batch()
        assert dialog._table.rowCount() == 2
        first_cell = dialog._table.item(0, 0)
        assert first_cell is not None
        assert first_cell.text() == "ab"

    def test_export_csv(
        self,
        qtbot: QtBot,
        scene: AutomatonScene,
        tmp_path: Path,
    ) -> None:
        _wire_dfa_ends_ab(scene)
        dialog = BatchTestDialog(scene)
        qtbot.addWidget(dialog)
        dialog._input_edit.setPlainText("ab\nba\n")
        dialog._run_batch()
        path = tmp_path / "report.csv"
        dialog.export_csv(path)
        content = path.read_text()
        assert "input,verdict,accepted,time_ms" in content
        assert "ab" in content
        assert "ba" in content

    def test_export_json(
        self,
        qtbot: QtBot,
        scene: AutomatonScene,
        tmp_path: Path,
    ) -> None:
        _wire_dfa_ends_ab(scene)
        dialog = BatchTestDialog(scene)
        qtbot.addWidget(dialog)
        dialog._input_edit.setPlainText("ab\nbab\n")
        dialog._run_batch()
        path = tmp_path / "report.json"
        dialog.export_json(path)
        payload = json.loads(path.read_text())
        assert len(payload) == 2
        assert payload[0]["input"] == "ab"
        assert isinstance(payload[0]["accepted"], bool)

    def test_raises_on_scene_without_initial(
        self,
        qtbot: QtBot,
        scene: AutomatonScene,
    ) -> None:
        scene.add_state(0.0, 0.0)  # no initial marker
        dialog = BatchTestDialog(scene)
        qtbot.addWidget(dialog)
        with pytest.raises(ValueError, match="initial"):
            dialog.run_with_inputs(["a"])
