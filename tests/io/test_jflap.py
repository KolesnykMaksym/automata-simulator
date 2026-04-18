"""JFLAP .jff round-trip tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from automata_simulator.core.io import automaton_from_jff, automaton_to_jff, load_jff, save_jff
from automata_simulator.core.models import (
    DEFAULT_BLANK,
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    MealyTransition,
    MooreTransition,
    PDATransition,
    State,
    TapeMove,
    TMTransition,
)
from automata_simulator.core.simulators import DFASimulator, NFASimulator, PDASimulator


def _dfa() -> Automaton:
    return Automaton(
        type=AutomatonType.DFA,
        name="dfa",
        states=[State(id="q0"), State(id="q1")],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions=[
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q0", target="q0", read="b"),
            FATransition(source="q1", target="q1", read="a"),
            FATransition(source="q1", target="q0", read="b"),
        ],
    )


def _epsilon_nfa() -> Automaton:
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        name="enfa",
        states=[State(id="q0"), State(id="q1")],
        alphabet=["a"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions=[
            FATransition(source="q0", target="q1", read=EPSILON),
            FATransition(source="q0", target="q0", read="a"),
        ],
    )


class TestFARoundTrip:
    def test_dfa_language_preserved(self) -> None:
        original = _dfa()
        xml = automaton_to_jff(original)
        restored = automaton_from_jff(xml)
        assert restored.type is AutomatonType.DFA
        for word in ("", "a", "ab", "aa", "aba"):
            assert DFASimulator(original).accepts(word) == DFASimulator(restored).accepts(word)

    def test_epsilon_nfa_classified_correctly(self) -> None:
        original = _epsilon_nfa()
        restored = automaton_from_jff(automaton_to_jff(original))
        assert restored.type is AutomatonType.EPSILON_NFA
        for word in ("", "a", "aa"):
            assert NFASimulator(original).accepts(word) == NFASimulator(restored).accepts(word)


class TestPDARoundTrip:
    def test_language_preserved_on_a_n_b_n(self) -> None:
        original = Automaton(
            type=AutomatonType.PDA,
            name="a-n-b-n",
            states=[State(id=s) for s in ("q0", "q1", "qf")],
            alphabet=["a", "b"],
            stack_alphabet=["Z", "A"],
            stack_start="Z",
            initial_state="q0",
            accepting_states=["qf"],
            transitions=[
                PDATransition(source="q0", target="qf", read=EPSILON, pop="Z", push=("Z",)),
                PDATransition(source="q0", target="q0", read="a", pop="Z", push=("A", "Z")),
                PDATransition(source="q0", target="q0", read="a", pop="A", push=("A", "A")),
                PDATransition(source="q0", target="q1", read="b", pop="A", push=()),
                PDATransition(source="q1", target="q1", read="b", pop="A", push=()),
                PDATransition(source="q1", target="qf", read=EPSILON, pop="Z", push=("Z",)),
            ],
        )
        restored = automaton_from_jff(automaton_to_jff(original))
        assert restored.type is AutomatonType.PDA
        for word in ("", "ab", "aabb", "aaabbb"):
            assert PDASimulator(original).accepts(word) == PDASimulator(restored).accepts(word)


class TestTMRoundTrip:
    def test_single_tape(self) -> None:
        original = Automaton(
            type=AutomatonType.TM,
            name="bit-flip",
            tape_count=1,
            states=[State(id="q0"), State(id="halt")],
            alphabet=["0", "1"],
            tape_alphabet=["0", "1", DEFAULT_BLANK],
            initial_state="q0",
            accepting_states=["halt"],
            transitions=[
                TMTransition(
                    source="q0",
                    target="halt",
                    read=("0",),
                    write=("1",),
                    move=(TapeMove.RIGHT,),
                ),
            ],
        )
        restored = automaton_from_jff(automaton_to_jff(original))
        assert restored.type is AutomatonType.TM
        assert restored.tape_count == 1
        assert len(restored.transitions) == 1


class TestMealyMooreRoundTrip:
    def test_mealy(self) -> None:
        original = Automaton(
            type=AutomatonType.MEALY,
            name="mealy",
            states=[State(id="S0")],
            alphabet=["a"],
            output_alphabet=["x"],
            initial_state="S0",
            transitions=[MealyTransition(source="S0", target="S0", read="a", write="x")],
        )
        restored = automaton_from_jff(automaton_to_jff(original))
        assert restored.type is AutomatonType.MEALY
        assert len(restored.transitions) == 1

    def test_moore(self) -> None:
        original = Automaton(
            type=AutomatonType.MOORE,
            name="moore",
            states=[State(id="r0", moore_output="0")],
            alphabet=["a"],
            output_alphabet=["0"],
            initial_state="r0",
            transitions=[MooreTransition(source="r0", target="r0", read="a")],
        )
        restored = automaton_from_jff(automaton_to_jff(original))
        assert restored.type is AutomatonType.MOORE
        assert restored.get_state("r0").moore_output == "0"


class TestFileRoundTrip:
    def test_save_and_load(self, tmp_path: Path) -> None:
        original = _dfa()
        path = tmp_path / "auto.jff"
        save_jff(original, path)
        restored = load_jff(path)
        assert restored.type is AutomatonType.DFA


class TestMalformed:
    def test_missing_structure_raises(self) -> None:
        with pytest.raises(ValueError, match="Malformed JFLAP"):
            automaton_from_jff("<root></root>")
