"""Transformation-dialog tests (pytest-qt, offscreen)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("pytestqt")

from pytestqt.qtbot import QtBot

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
)
from automata_simulator.gui.canvas import (
    AutomatonScene,
    AutomatonView,
    automaton_to_scene,
    scene_to_automaton,
)
from automata_simulator.gui.dialogs import (
    ConvertToDFADialog,
    FAToRegexDialog,
    MinimizeDFADialog,
    RegexToNFADialog,
    RemoveEpsilonDialog,
)


@pytest.fixture
def view(qtbot: QtBot) -> AutomatonView:
    v = AutomatonView()
    qtbot.addWidget(v)
    return v


@pytest.fixture
def scene(view: AutomatonView) -> AutomatonScene:
    return view.automaton_scene


def _nfa_ends_in_01() -> Automaton:
    return Automaton(
        type=AutomatonType.NFA,
        states=[State(id=s) for s in ("q0", "q1", "q2")],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q2"],
        transitions=[
            FATransition(source="q0", target="q0", read="0"),
            FATransition(source="q0", target="q0", read="1"),
            FATransition(source="q0", target="q1", read="0"),
            FATransition(source="q1", target="q2", read="1"),
        ],
    )


def _dfa_redundant() -> Automaton:
    return Automaton(
        type=AutomatonType.DFA,
        states=[State(id=s) for s in ("q0", "q1", "q2")],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q2"],
        transitions=[
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q0", target="q0", read="b"),
            FATransition(source="q1", target="q1", read="a"),
            FATransition(source="q1", target="q2", read="b"),
            FATransition(source="q2", target="q1", read="a"),
            FATransition(source="q2", target="q0", read="b"),
        ],
    )


def _enfa() -> Automaton:
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        states=[State(id="q0"), State(id="q1")],
        alphabet=["a"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions=[
            FATransition(source="q0", target="q1", read=EPSILON),
            FATransition(source="q1", target="q1", read="a"),
        ],
    )


# ------------------------------------------------------------ ConvertToDFADialog
class TestConvertToDFADialog:
    def test_apply_returns_dfa(self, qtbot: QtBot) -> None:
        dialog = ConvertToDFADialog(_nfa_ends_in_01())
        qtbot.addWidget(dialog)
        dialog._on_apply()
        assert dialog.applied_automaton is not None
        assert dialog.applied_automaton.type is AutomatonType.DFA

    def test_rejects_dfa_input(self, qtbot: QtBot) -> None:  # noqa: ARG002
        with pytest.raises(ValueError, match="NFA"):
            ConvertToDFADialog(_dfa_redundant())


# ------------------------------------------------------------ MinimizeDFADialog
class TestMinimizeDFADialog:
    def test_apply_returns_min_dfa(self, qtbot: QtBot) -> None:
        dialog = MinimizeDFADialog(_dfa_redundant())
        qtbot.addWidget(dialog)
        dialog._on_apply()
        assert dialog.applied_automaton is not None
        assert dialog.applied_automaton.type is AutomatonType.DFA

    def test_rejects_nfa(self, qtbot: QtBot) -> None:  # noqa: ARG002
        with pytest.raises(ValueError, match="DFA"):
            MinimizeDFADialog(_nfa_ends_in_01())


# ------------------------------------------------------------ RegexToNFADialog
class TestRegexToNFADialog:
    def test_valid_regex_applies(self, qtbot: QtBot) -> None:
        dialog = RegexToNFADialog()
        qtbot.addWidget(dialog)
        dialog._regex_edit.setText("(a|b)*abb")
        dialog._on_apply()
        assert dialog.applied_automaton is not None
        assert dialog.applied_automaton.type is AutomatonType.EPSILON_NFA

    def test_empty_shows_message(self, qtbot: QtBot) -> None:
        dialog = RegexToNFADialog()
        qtbot.addWidget(dialog)
        dialog._on_apply()
        assert dialog.applied_automaton is None

    def test_invalid_shows_error(self, qtbot: QtBot) -> None:
        dialog = RegexToNFADialog()
        qtbot.addWidget(dialog)
        dialog._regex_edit.setText("(a|b")
        dialog._on_apply()
        assert dialog.applied_automaton is None


# ------------------------------------------------------------ FAToRegexDialog
class TestFAToRegexDialog:
    def test_produces_regex_text(self, qtbot: QtBot) -> None:
        dialog = FAToRegexDialog(_dfa_redundant())
        qtbot.addWidget(dialog)
        assert dialog.regex_text  # non-empty

    def test_apply_returns_nfa(self, qtbot: QtBot) -> None:
        dialog = FAToRegexDialog(_dfa_redundant())
        qtbot.addWidget(dialog)
        dialog._on_apply()
        assert dialog.applied_automaton is not None
        assert dialog.applied_automaton.type is AutomatonType.EPSILON_NFA

    def test_rejects_pda(self, qtbot: QtBot) -> None:  # noqa: ARG002
        pda = Automaton(
            type=AutomatonType.PDA,
            states=[State(id="q0")],
            alphabet=["a"],
            stack_alphabet=["Z"],
            stack_start="Z",
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="DFA/NFA"):
            FAToRegexDialog(pda)


# ------------------------------------------------------------ RemoveEpsilonDialog
class TestRemoveEpsilonDialog:
    def test_apply_returns_nfa(self, qtbot: QtBot) -> None:
        dialog = RemoveEpsilonDialog(_enfa())
        qtbot.addWidget(dialog)
        dialog._on_apply()
        assert dialog.applied_automaton is not None
        assert dialog.applied_automaton.type is AutomatonType.NFA

    def test_rejects_dfa(self, qtbot: QtBot) -> None:  # noqa: ARG002
        with pytest.raises(ValueError, match="ε-NFA"):
            RemoveEpsilonDialog(_dfa_redundant())


# ------------------------------------------------------------ scene round-trip
class TestAutomatonToScene:
    def test_round_trip_through_scene(self, scene: AutomatonScene) -> None:
        original = _nfa_ends_in_01()
        automaton_to_scene(original, scene)
        rebuilt = scene_to_automaton(scene)
        # Basic structural equivalence.
        assert rebuilt.type is AutomatonType.NFA
        assert {s.id for s in rebuilt.states} == {s.id for s in original.states}
        assert len(rebuilt.transitions) == len(original.transitions)

    def test_clears_prior_scene_contents(self, scene: AutomatonScene) -> None:
        scene.add_state(0.0, 0.0, state_id="stale")
        automaton_to_scene(_dfa_redundant(), scene)
        ids = {s.state_id for s in scene.state_items()}
        assert "stale" not in ids
