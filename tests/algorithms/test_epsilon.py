"""Tests for epsilon_closure and remove_epsilon_transitions."""

from __future__ import annotations

import pytest

from automata_simulator.core.algorithms import (
    epsilon_closure,
    remove_epsilon_transitions,
)
from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
)
from automata_simulator.core.simulators import NFASimulator


def _enfa_a_star_b_star() -> Automaton:
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        states=[State(id="q0"), State(id="q1")],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions=[
            FATransition(source="q0", target="q0", read="a"),
            FATransition(source="q0", target="q1", read=EPSILON),
            FATransition(source="q1", target="q1", read="b"),
        ],
    )


class TestEpsilonClosure:
    def test_includes_seeds(self) -> None:
        auto = _enfa_a_star_b_star()
        assert "q0" in epsilon_closure(auto, {"q0"})

    def test_follows_single_epsilon_edge(self) -> None:
        auto = _enfa_a_star_b_star()
        assert epsilon_closure(auto, {"q0"}) == frozenset({"q0", "q1"})

    def test_idempotent_on_closed_set(self) -> None:
        auto = _enfa_a_star_b_star()
        closed = epsilon_closure(auto, {"q0"})
        assert epsilon_closure(auto, closed) == closed

    def test_transitive_epsilon_chain(self) -> None:
        chain = Automaton(
            type=AutomatonType.EPSILON_NFA,
            states=[State(id="a"), State(id="b"), State(id="c")],
            alphabet=["x"],
            initial_state="a",
            accepting_states=["c"],
            transitions=[
                FATransition(source="a", target="b", read=EPSILON),
                FATransition(source="b", target="c", read=EPSILON),
            ],
        )
        assert epsilon_closure(chain, {"a"}) == frozenset({"a", "b", "c"})

    def test_no_epsilons_returns_seeds(self) -> None:
        auto = Automaton(
            type=AutomatonType.NFA,
            states=[State(id="x"), State(id="y")],
            alphabet=["a"],
            initial_state="x",
            accepting_states=["y"],
            transitions=[FATransition(source="x", target="y", read="a")],
        )
        assert epsilon_closure(auto, {"x"}) == frozenset({"x"})


class TestRemoveEpsilonTransitions:
    def test_language_preserved_on_a_star_b_star(self) -> None:
        enfa = _enfa_a_star_b_star()
        result = remove_epsilon_transitions(enfa)
        nfa = result.nfa
        assert nfa.type is AutomatonType.NFA
        # The resulting NFA contains no ε-transitions.
        for tr in nfa.transitions:
            assert isinstance(tr, FATransition)
            assert tr.read != EPSILON
        # Language equivalence across a battery of words.
        sim_enfa = NFASimulator(enfa)
        sim_nfa = NFASimulator(nfa)
        for word in ("", "a", "b", "ab", "aaabbb", "ba", "abab"):
            assert sim_enfa.accepts(word) == sim_nfa.accepts(word), word

    def test_initial_state_accepting_when_closure_reaches_accepting(self) -> None:
        # q0 --ε--> q1 (accepting), so q0 must become accepting after removal.
        result = remove_epsilon_transitions(_enfa_a_star_b_star())
        assert "q0" in result.nfa.accepting_states

    def test_closure_mapping_populated(self) -> None:
        result = remove_epsilon_transitions(_enfa_a_star_b_star())
        assert result.closure_by_state["q0"] == frozenset({"q0", "q1"})
        assert result.closure_by_state["q1"] == frozenset({"q1"})

    def test_rejects_dfa(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="NFA or ε-NFA"):
            remove_epsilon_transitions(dfa)

    def test_noop_on_plain_nfa(self) -> None:
        nfa = Automaton(
            type=AutomatonType.NFA,
            states=[State(id="q0"), State(id="q1")],
            alphabet=["a"],
            initial_state="q0",
            accepting_states=["q1"],
            transitions=[FATransition(source="q0", target="q1", read="a")],
        )
        result = remove_epsilon_transitions(nfa)
        # Same language
        for word in ("", "a", "aa"):
            assert NFASimulator(nfa).accepts(word) == NFASimulator(result.nfa).accepts(word)
