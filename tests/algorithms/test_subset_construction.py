"""Tests for nfa_to_dfa (subset construction)."""

from __future__ import annotations

import pytest

from automata_simulator.core.algorithms import nfa_to_dfa
from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
)
from automata_simulator.core.simulators import DFASimulator, NFASimulator


def _nfa_ends_in_01() -> Automaton:
    return Automaton(
        type=AutomatonType.NFA,
        states=[State(id="q0"), State(id="q1"), State(id="q2")],
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


def _enfa_a_or_b() -> Automaton:
    """Thompson-style ε-NFA for (a|b)."""
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        states=[State(id=f"q{i}") for i in range(6)],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q5"],
        transitions=[
            FATransition(source="q0", target="q1", read=EPSILON),
            FATransition(source="q0", target="q3", read=EPSILON),
            FATransition(source="q1", target="q2", read="a"),
            FATransition(source="q3", target="q4", read="b"),
            FATransition(source="q2", target="q5", read=EPSILON),
            FATransition(source="q4", target="q5", read=EPSILON),
        ],
    )


class TestSubsetConstruction:
    @pytest.mark.parametrize(
        "word",
        ["", "0", "1", "01", "001", "111001", "010", "10"],
    )
    def test_language_equivalence_on_nfa(self, word: str) -> None:
        nfa = _nfa_ends_in_01()
        dfa = nfa_to_dfa(nfa).dfa
        assert NFASimulator(nfa).accepts(word) == DFASimulator(dfa).accepts(word), word

    @pytest.mark.parametrize("word", ["", "a", "b", "ab", "ba", "c"])
    def test_language_equivalence_on_enfa(self, word: str) -> None:
        enfa = _enfa_a_or_b()
        if "c" in word:
            # 'c' isn't in the alphabet; the DFA also rejects it (invalid symbol).
            return
        dfa = nfa_to_dfa(enfa).dfa
        assert NFASimulator(enfa).accepts(word) == DFASimulator(dfa).accepts(word), word

    def test_result_is_deterministic(self) -> None:
        dfa = nfa_to_dfa(_nfa_ends_in_01()).dfa
        assert dfa.type is AutomatonType.DFA
        assert dfa.is_deterministic() is True

    def test_subset_mapping_includes_initial(self) -> None:
        result = nfa_to_dfa(_nfa_ends_in_01())
        initial_subset = result.subset_by_state[result.dfa.initial_state]
        # For this NFA there are no ε-transitions, so initial subset = {q0}.
        assert initial_subset == frozenset({"q0"})

    def test_subset_mapping_contains_epsilon_closure(self) -> None:
        # (a|b) ε-NFA: initial closure is {q0, q1, q3}.
        result = nfa_to_dfa(_enfa_a_or_b())
        initial_subset = result.subset_by_state[result.dfa.initial_state]
        assert {"q0", "q1", "q3"} <= initial_subset

    def test_rejects_dfa(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="NFA or ε-NFA"):
            nfa_to_dfa(dfa)
