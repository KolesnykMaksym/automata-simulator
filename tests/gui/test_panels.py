"""Tests for TapeView / StackView / StepHistoryView / undo commands."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("pytestqt")

from pytestqt.qtbot import QtBot

from automata_simulator.gui.canvas import (
    AddStateCommand,
    AddTransitionCommand,
    AutomatonScene,
    AutomatonView,
    RemoveStateCommand,
)
from automata_simulator.gui.main_window import MainWindow
from automata_simulator.gui.panels import StackView, StepHistoryView, TapeView


@pytest.fixture
def view(qtbot: QtBot) -> AutomatonView:
    v = AutomatonView()
    qtbot.addWidget(v)
    return v


@pytest.fixture
def scene(view: AutomatonView) -> AutomatonScene:
    return view.automaton_scene


# ------------------------------------------------------------ TapeView
class TestTapeView:
    def test_initial_empty(self, qtbot: QtBot) -> None:
        tv = TapeView()
        qtbot.addWidget(tv)
        assert tv.tapes() == []

    def test_set_tapes_records_snapshots(self, qtbot: QtBot) -> None:
        tv = TapeView()
        qtbot.addWidget(tv)
        tv.set_tapes([(("0", "1", "0"), 1)])
        assert tv.tapes() == [(("0", "1", "0"), 1)]

    def test_clear(self, qtbot: QtBot) -> None:
        tv = TapeView()
        qtbot.addWidget(tv)
        tv.set_tapes([(("a",), 0)])
        tv.clear()
        assert tv.tapes() == []


# ------------------------------------------------------------ StackView
class TestStackView:
    def test_initial_empty(self, qtbot: QtBot) -> None:
        sv = StackView()
        qtbot.addWidget(sv)
        assert sv.stack() == ()

    def test_set_stack_updates(self, qtbot: QtBot) -> None:
        sv = StackView()
        qtbot.addWidget(sv)
        sv.set_stack(["Z", "A", "A"])
        assert sv.stack() == ("Z", "A", "A")

    def test_clear(self, qtbot: QtBot) -> None:
        sv = StackView()
        qtbot.addWidget(sv)
        sv.set_stack(["X"])
        sv.clear()
        assert sv.stack() == ()


# ------------------------------------------------------------ StepHistoryView
class TestStepHistoryView:
    def test_set_and_append(self, qtbot: QtBot) -> None:
        sh = StepHistoryView()
        qtbot.addWidget(sh)
        sh.set_steps(["step 0", "step 1"])
        assert sh.step_lines() == ["step 0", "step 1"]
        sh.append_step("step 2")
        assert sh.step_lines() == ["step 0", "step 1", "step 2"]


# ------------------------------------------------------------ Undo commands
class TestAddStateCommand:
    def test_redo_creates_undo_removes(self, scene: AutomatonScene) -> None:
        cmd = AddStateCommand(scene, 10.0, 20.0, state_id="s0")
        cmd.redo()
        assert any(s.state_id == "s0" for s in scene.state_items())
        cmd.undo()
        assert not any(s.state_id == "s0" for s in scene.state_items())
        cmd.redo()
        assert any(s.state_id == "s0" for s in scene.state_items())


class TestAddTransitionCommand:
    def test_round_trip(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0, state_id="a")
        b = scene.add_state(100.0, 0.0, state_id="b")
        cmd = AddTransitionCommand(scene, a, b, label="x")
        cmd.redo()
        assert any(
            tr.source.state_id == "a" and tr.target.state_id == "b"
            for tr in scene.transition_items()
        )
        cmd.undo()
        assert scene.transition_items() == []
        cmd.redo()
        assert any(
            tr.source.state_id == "a" and tr.target.state_id == "b"
            for tr in scene.transition_items()
        )


class TestRemoveStateCommand:
    def test_round_trip_with_transitions(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0, state_id="a")
        b = scene.add_state(100.0, 0.0, state_id="b")
        scene.add_transition(a, b, "x")
        scene.add_transition(b, a, "y")
        cmd = RemoveStateCommand(scene, a)
        cmd.redo()
        assert all(s.state_id != "a" for s in scene.state_items())
        # Transitions touching 'a' are gone too.
        assert scene.transition_items() == []
        cmd.undo()
        assert any(s.state_id == "a" for s in scene.state_items())
        assert len(scene.transition_items()) == 2


class TestMainWindowUndoStack:
    def test_ctrl_z_reverts_state_add(self, qtbot: QtBot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        scene = window.canvas_view.automaton_scene
        window.undo_stack.push(AddStateCommand(scene, 0.0, 0.0, state_id="x"))
        assert any(s.state_id == "x" for s in scene.state_items())
        window.undo_stack.undo()
        assert not any(s.state_id == "x" for s in scene.state_items())
        window.undo_stack.redo()
        assert any(s.state_id == "x" for s in scene.state_items())
