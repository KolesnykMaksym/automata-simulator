"""Tests for Hopcroft DFA minimisation and remove_unreachable_states."""

from __future__ import annotations

import pytest

from automata_simulator.core.algorithms import (
    minimize_dfa,
    remove_unreachable_states,
)
from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    FATransition,
    State,
)
from automata_simulator.core.simulators import DFASimulator


def _dfa_with_redundant_states() -> Automaton:
    """A DFA that has equivalent states and one unreachable state.

    Language: strings over {a, b} ending in "ab".
    States q3 and q4 will be equivalent (both non-accepting waystates); q5
    is unreachable.
    """
    return Automaton(
        type=AutomatonType.DFA,
        states=[State(id=s) for s in ("q0", "q1", "q2", "q3", "q4", "q5")],
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
            # q3 and q4 are reachable-but-equivalent dead ends.
            FATransition(source="q3", target="q3", read="a"),
            FATransition(source="q3", target="q3", read="b"),
            FATransition(source="q4", target="q4", read="a"),
            FATransition(source="q4", target="q4", read="b"),
            # q5 is unreachable.
            FATransition(source="q5", target="q5", read="a"),
            FATransition(source="q5", target="q5", read="b"),
        ],
    )


class TestRemoveUnreachable:
    def test_drops_unreachable(self) -> None:
        trimmed = remove_unreachable_states(_dfa_with_redundant_states())
        reachable_ids = {s.id for s in trimmed.states}
        assert reachable_ids == {"q0", "q1", "q2"}

    def test_preserves_language(self) -> None:
        dfa = _dfa_with_redundant_states()
        trimmed = remove_unreachable_states(dfa)
        for word in ("", "ab", "aab", "abab", "b", "aa", "aabab"):
            assert DFASimulator(dfa).accepts(word) == DFASimulator(trimmed).accepts(word)

    def test_rejects_nfa(self) -> None:
        nfa = Automaton(
            type=AutomatonType.NFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="DFA"):
            remove_unreachable_states(nfa)


class TestMinimizeDFA:
    def test_language_preserved_on_ending_in_ab(self) -> None:
        dfa = _dfa_with_redundant_states()
        minimized = minimize_dfa(dfa).dfa
        for word in ("", "ab", "aab", "abab", "b", "a", "bab", "abb"):
            assert DFASimulator(dfa).accepts(word) == DFASimulator(minimized).accepts(word)

    def test_minimized_state_count_is_optimal(self) -> None:
        # The canonical DFA for "ends in ab" has exactly 3 states.
        minimized = minimize_dfa(_dfa_with_redundant_states()).dfa
        assert len(minimized.states) == 3

    def test_even_zeros_is_already_minimal(self) -> None:
        even_zeros = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="even"), State(id="odd")],
            alphabet=["0", "1"],
            initial_state="even",
            accepting_states=["even"],
            transitions=[
                FATransition(source="even", target="odd", read="0"),
                FATransition(source="even", target="even", read="1"),
                FATransition(source="odd", target="even", read="0"),
                FATransition(source="odd", target="odd", read="1"),
            ],
        )
        result = minimize_dfa(even_zeros)
        assert len(result.dfa.states) == 2

    def test_equivalence_classes_cover_original_states(self) -> None:
        dfa = _dfa_with_redundant_states()
        result = minimize_dfa(dfa)
        covered: set[str] = set()
        for block in result.equivalence_classes.values():
            covered |= block
        reachable = {s.id for s in remove_unreachable_states(dfa).states}
        assert reachable <= covered

    def test_empty_language_produces_single_dead_state(self) -> None:
        empty_lang = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0"), State(id="q1")],
            alphabet=["a"],
            initial_state="q0",
            accepting_states=[],  # nothing accepts anything
            transitions=[FATransition(source="q0", target="q1", read="a")],
        )
        result = minimize_dfa(empty_lang)
        assert len(result.dfa.states) == 1
        # And it really accepts nothing.
        sim = DFASimulator(result.dfa)
        for word in ("", "a", "aa"):
            assert sim.accepts(word) is False

    def test_rejects_nfa(self) -> None:
        nfa = Automaton(
            type=AutomatonType.NFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="DFA"):
            minimize_dfa(nfa)
