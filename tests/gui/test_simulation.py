"""SimulationPanel + scene_to_automaton tests (pytest-qt, offscreen)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("pytestqt")

from pytestqt.qtbot import QtBot

from automata_simulator.core.models import EPSILON, AutomatonType
from automata_simulator.core.simulators import DFASimulator, NFASimulator, Verdict
from automata_simulator.gui.canvas import (
    AutomatonScene,
    AutomatonView,
    SceneConversionError,
    scene_to_automaton,
)
from automata_simulator.gui.panels import SimulationPanel


@pytest.fixture
def view(qtbot: QtBot) -> AutomatonView:
    v = AutomatonView()
    qtbot.addWidget(v)
    return v


@pytest.fixture
def scene(view: AutomatonView) -> AutomatonScene:
    return view.automaton_scene


def _wire_dfa_ab(scene: AutomatonScene) -> None:
    """Canvas for DFA over {a,b} accepting strings ending in 'ab'."""
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


class TestSceneConversion:
    def test_classifies_dfa(self, scene: AutomatonScene) -> None:
        _wire_dfa_ab(scene)
        auto = scene_to_automaton(scene)
        assert auto.type is AutomatonType.DFA
        assert auto.initial_state == "q0"
        assert "q2" in auto.accepting_states

    def test_classifies_nfa_on_duplicate_outgoing(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0, state_id="q0")
        b = scene.add_state(100.0, 0.0, state_id="q1")
        scene.set_initial(a)
        b.set_accepting(True)
        scene.add_transition(a, a, "a")
        scene.add_transition(a, b, "a")  # same (state, symbol) → NFA
        auto = scene_to_automaton(scene)
        assert auto.type is AutomatonType.NFA

    def test_classifies_epsilon_nfa_on_epsilon_label(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0, state_id="q0")
        b = scene.add_state(100.0, 0.0, state_id="q1")
        scene.set_initial(a)
        b.set_accepting(True)
        scene.add_transition(a, b, EPSILON)
        auto = scene_to_automaton(scene)
        assert auto.type is AutomatonType.EPSILON_NFA

    def test_no_states_raises(self, scene: AutomatonScene) -> None:
        with pytest.raises(SceneConversionError, match="no states"):
            scene_to_automaton(scene)

    def test_missing_initial_raises(self, scene: AutomatonScene) -> None:
        scene.add_state(0.0, 0.0)
        with pytest.raises(SceneConversionError, match="no initial state"):
            scene_to_automaton(scene)

    def test_empty_label_raises(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0)
        b = scene.add_state(100.0, 0.0)
        scene.set_initial(a)
        scene.add_transition(a, b, "")
        with pytest.raises(SceneConversionError, match="empty label"):
            scene_to_automaton(scene)


class TestSimulationPanel:
    def test_step_advances_simulator(self, qtbot: QtBot, scene: AutomatonScene) -> None:
        _wire_dfa_ab(scene)
        panel = SimulationPanel(scene)
        qtbot.addWidget(panel)
        panel._input_edit.setText("ab")
        panel.step_once()
        assert isinstance(panel.simulator, DFASimulator)
        # After one step we've consumed 'a' and moved to q1.
        assert panel.simulator.current_state == "q1"

    def test_step_run_to_accept(self, qtbot: QtBot, scene: AutomatonScene) -> None:
        _wire_dfa_ab(scene)
        panel = SimulationPanel(scene)
        qtbot.addWidget(panel)
        panel._input_edit.setText("ab")
        panel.step_once()
        panel.step_once()
        panel.step_once()  # triggers acceptance check
        assert panel.simulator is not None
        assert panel.simulator.verdict is Verdict.ACCEPTED

    def test_reset_clears_simulator(self, qtbot: QtBot, scene: AutomatonScene) -> None:
        _wire_dfa_ab(scene)
        panel = SimulationPanel(scene)
        qtbot.addWidget(panel)
        panel._input_edit.setText("ab")
        panel.step_once()
        panel.reset()
        assert panel.simulator is None

    def test_highlight_follows_active_state(
        self, qtbot: QtBot, scene: AutomatonScene,
    ) -> None:
        _wire_dfa_ab(scene)
        panel = SimulationPanel(scene)
        qtbot.addWidget(panel)
        panel._input_edit.setText("ab")
        panel.step_once()
        # Expect q1 to be highlighted now (active state after reading 'a').
        highlighted_ids = [
            s.state_id for s in scene.state_items() if s._highlighted
        ]
        assert "q1" in highlighted_ids

    def test_epsilon_nfa_runs_with_nfa_simulator(
        self, qtbot: QtBot, scene: AutomatonScene,
    ) -> None:
        a = scene.add_state(0.0, 0.0, state_id="q0")
        b = scene.add_state(100.0, 0.0, state_id="q1")
        scene.set_initial(a)
        b.set_accepting(True)
        scene.add_transition(a, b, EPSILON)
        panel = SimulationPanel(scene)
        qtbot.addWidget(panel)
        panel._input_edit.setText("")
        panel.step_once()  # empty input → immediate verdict
        assert isinstance(panel.simulator, NFASimulator)
        assert panel.simulator.verdict is Verdict.ACCEPTED

    def test_missing_initial_shows_error(
        self, qtbot: QtBot, scene: AutomatonScene,
    ) -> None:
        scene.add_state(0.0, 0.0)  # no initial marker
        panel = SimulationPanel(scene)
        qtbot.addWidget(panel)
        panel.step_once()
        assert panel.simulator is None
