"""NFASimulator tests — covers both NFA and ε-NFA on classic examples."""

from __future__ import annotations

import pytest

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
)
from automata_simulator.core.simulators import (
    DFASimulator,
    NFASimulator,
    Verdict,
    WrongAutomatonTypeError,
)


def _nfa_ends_in_01() -> Automaton:
    """NFA over {0,1} accepting strings that end in '01'."""
    return Automaton(
        type=AutomatonType.NFA,
        name="ends-in-01",
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


def _nfa_third_from_end_is_one() -> Automaton:
    """NFA over {0,1} accepting strings whose 3rd-from-last symbol is '1'.

    Sipser Example 1.31 — a textbook example where a small NFA has an
    exponential-size DFA equivalent.
    """
    return Automaton(
        type=AutomatonType.NFA,
        name="3rd-from-end-is-1",
        states=[State(id="q0"), State(id="q1"), State(id="q2"), State(id="q3")],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q3"],
        transitions=[
            FATransition(source="q0", target="q0", read="0"),
            FATransition(source="q0", target="q0", read="1"),
            FATransition(source="q0", target="q1", read="1"),
            FATransition(source="q1", target="q2", read="0"),
            FATransition(source="q1", target="q2", read="1"),
            FATransition(source="q2", target="q3", read="0"),
            FATransition(source="q2", target="q3", read="1"),
        ],
    )


def _enfa_a_star_b_star() -> Automaton:
    """ε-NFA for the language a*b*."""
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        name="a-star-b-star",
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


def _enfa_thompson_a_or_b() -> Automaton:
    """ε-NFA produced by Thompson's construction for (a|b)."""
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        name="a-or-b",
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


class TestNFAEndsIn01:
    @pytest.mark.parametrize("word", ["01", "001", "101", "111001", "01" + "0" * 0 + "01"])
    def test_accepts(self, word: str) -> None:
        assert NFASimulator(_nfa_ends_in_01()).accepts(word) is True

    @pytest.mark.parametrize("word", ["", "0", "1", "10", "011", "110"])
    def test_rejects(self, word: str) -> None:
        assert NFASimulator(_nfa_ends_in_01()).accepts(word) is False


class TestThirdFromEnd:
    @pytest.mark.parametrize("word", ["100", "1111", "0100", "1010101", "0011110"])
    def test_accepts(self, word: str) -> None:
        # third-from-end is '1' in every one of the above
        assert NFASimulator(_nfa_third_from_end_is_one()).accepts(word) is True

    @pytest.mark.parametrize(
        "word",
        ["", "10", "000", "0000", "0010", "010010", "11011010"],
    )
    def test_rejects(self, word: str) -> None:
        # third-from-end is '0' or the string is too short
        assert NFASimulator(_nfa_third_from_end_is_one()).accepts(word) is False


class TestEpsilonNFA:
    @pytest.mark.parametrize("word", ["", "a", "b", "ab", "aaabbb", "aaa", "bbb"])
    def test_a_star_b_star_accepts(self, word: str) -> None:
        assert NFASimulator(_enfa_a_star_b_star()).accepts(word) is True

    @pytest.mark.parametrize("word", ["ba", "abab", "aba", "bab"])
    def test_a_star_b_star_rejects(self, word: str) -> None:
        assert NFASimulator(_enfa_a_star_b_star()).accepts(word) is False

    @pytest.mark.parametrize("word", ["a", "b"])
    def test_thompson_a_or_b_accepts(self, word: str) -> None:
        assert NFASimulator(_enfa_thompson_a_or_b()).accepts(word) is True

    @pytest.mark.parametrize("word", ["", "aa", "bb", "ab", "c"])
    def test_thompson_a_or_b_rejects(self, word: str) -> None:
        assert NFASimulator(_enfa_thompson_a_or_b()).accepts(word) is False


class TestFrontierMechanics:
    def test_initial_frontier_is_epsilon_closed(self) -> None:
        sim = NFASimulator(_enfa_a_star_b_star())
        sim.reset("")
        # q0 --ε--> q1, so the initial frontier includes both
        assert sim.current_states == frozenset({"q0", "q1"})

    def test_empty_configuration_rejection(self) -> None:
        # NFA ends-in-01 reading an invalid prefix
        sim = NFASimulator(_nfa_ends_in_01())
        sim.reset("001")  # should ultimately accept
        sim.step()  # 0 -> {q0, q1}
        sim.step()  # 0 -> {q0, q1}  (q1 has no transition on 0)
        sim.step()  # 1 -> {q0, q2}
        assert sim.is_halted is False  # still running
        assert sim.step() is None  # now halted, accepting
        assert sim.is_accepted is True

    def test_empty_frontier_yields_dedicated_verdict(self) -> None:
        nfa = Automaton(
            type=AutomatonType.NFA,
            states=[State(id="q0"), State(id="q1")],
            alphabet=["a"],
            initial_state="q0",
            accepting_states=["q1"],
            transitions=[FATransition(source="q0", target="q1", read="a")],
        )
        trace = NFASimulator(nfa).run("aa")
        assert trace.verdict is Verdict.REJECTED_EMPTY_CONFIG


class TestTypeValidation:
    def test_rejects_dfa(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0", is_initial=True)],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(WrongAutomatonTypeError):
            NFASimulator(dfa)

    def test_dfa_still_handled_by_its_own_simulator(self) -> None:
        # Sanity check that the two simulators don't collide via shared symbols.
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0"), State(id="q1")],
            alphabet=["a"],
            initial_state="q0",
            accepting_states=["q1"],
            transitions=[
                FATransition(source="q0", target="q1", read="a"),
                FATransition(source="q1", target="q1", read="a"),
            ],
        )
        assert DFASimulator(dfa).accepts("aa") is True
