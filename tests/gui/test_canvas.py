"""Canvas / scene tests (pytest-qt, offscreen)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("pytestqt")

from pytestqt.qtbot import QtBot

from automata_simulator.gui.canvas import (
    AutomatonScene,
    AutomatonView,
    StateItem,
    TransitionItem,
)
from automata_simulator.gui.main_window import MainWindow


@pytest.fixture
def view(qtbot: QtBot) -> AutomatonView:
    v = AutomatonView()
    qtbot.addWidget(v)
    return v


@pytest.fixture
def scene(view: AutomatonView) -> AutomatonScene:
    return view.automaton_scene


class TestSceneBasics:
    def test_starts_empty(self, scene: AutomatonScene) -> None:
        assert scene.state_items() == []
        assert scene.transition_items() == []
        assert scene.initial_state() is None

    def test_add_state_registers_item(self, scene: AutomatonScene) -> None:
        item = scene.add_state(50.0, 50.0)
        assert isinstance(item, StateItem)
        assert item in scene.state_items()
        assert item.state_id == "q0"

    def test_state_ids_increment(self, scene: AutomatonScene) -> None:
        ids = [scene.add_state(i * 30.0, 0.0).state_id for i in range(3)]
        assert ids == ["q0", "q1", "q2"]

    def test_explicit_state_id(self, scene: AutomatonScene) -> None:
        item = scene.add_state(0.0, 0.0, state_id="start")
        assert item.state_id == "start"

    def test_set_initial_is_exclusive(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0)
        b = scene.add_state(120.0, 0.0)
        scene.set_initial(a)
        initial_ids = [s.state_id for s in scene.state_items() if s.is_initial]
        assert initial_ids == [a.state_id]
        scene.set_initial(b)
        initial_ids = [s.state_id for s in scene.state_items() if s.is_initial]
        assert initial_ids == [b.state_id]


class TestTransitions:
    def test_add_transition_links_states(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0)
        b = scene.add_state(100.0, 0.0)
        tr = scene.add_transition(a, b, label="x")
        assert isinstance(tr, TransitionItem)
        assert tr.source is a
        assert tr.target is b
        assert tr.label == "x"
        assert tr in scene.transition_items()

    def test_remove_state_cascades_transitions(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0)
        b = scene.add_state(100.0, 0.0)
        scene.add_transition(a, b, label="x")
        scene.add_transition(b, a, label="y")
        scene.remove_state(a)
        assert scene.transition_items() == []

    def test_self_loop(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0)
        tr = scene.add_transition(a, a, label="r")
        assert tr.source is tr.target


class TestStateItem:
    def test_set_accepting_toggles_flag(self, scene: AutomatonScene) -> None:
        a = scene.add_state(0.0, 0.0)
        states = [a.is_accepting]
        a.set_accepting(True)
        states.append(a.is_accepting)
        a.set_accepting(False)
        states.append(a.is_accepting)
        assert states == [False, True, False]

    def test_centre_is_scene_position(self, scene: AutomatonScene) -> None:
        a = scene.add_state(45.0, 70.0)
        centre = a.centre()
        assert centre.x() == 45.0
        assert centre.y() == 70.0

    def test_rename_updates_label_when_label_mirrors_id(
        self, scene: AutomatonScene,
    ) -> None:
        a = scene.add_state(0.0, 0.0, state_id="q0")
        assert a.label == "q0"
        a.set_state_id("start")
        assert a.state_id == "start"
        assert a.label == "start"


class TestPopulateFromDefinitions:
    def test_repopulates(self, scene: AutomatonScene) -> None:
        scene.add_state(0.0, 0.0)
        scene.populate_from(
            states=[
                ("s0", 0.0, 0.0, True, False),
                ("s1", 120.0, 0.0, False, True),
            ],
            transitions=[("s0", "s1", "a"), ("s1", "s1", "b")],
        )
        ids = {s.state_id for s in scene.state_items()}
        assert ids == {"s0", "s1"}
        initial = scene.initial_state()
        assert initial is not None
        assert initial.state_id == "s0"
        accepting = next(s for s in scene.state_items() if s.state_id == "s1")
        assert accepting.is_accepting
        assert len(scene.transition_items()) == 2


class TestMainWindowIntegration:
    def test_central_widget_is_canvas(self, qtbot: QtBot) -> None:
        window = MainWindow()
        qtbot.addWidget(window)
        assert isinstance(window.canvas_view, AutomatonView)
        assert window.centralWidget() is window.canvas_view
