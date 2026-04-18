"""DFASimulator tests — classic examples from Sipser & Hopcroft-Ullman."""

from __future__ import annotations

import pytest

from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    FATransition,
    State,
)
from automata_simulator.core.simulators import (
    DFASimulator,
    SimulatorNotReadyError,
    Verdict,
    WrongAutomatonTypeError,
)


def _dfa_contains_abb() -> Automaton:
    """Sipser Example 1.9: L = {w ∈ {a,b}* : w contains 'abb' as substring}."""
    return Automaton(
        type=AutomatonType.DFA,
        name="contains-abb",
        states=[State(id=s) for s in ("q0", "q1", "q2", "q3")],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q3"],
        transitions=[
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q0", target="q0", read="b"),
            FATransition(source="q1", target="q1", read="a"),
            FATransition(source="q1", target="q2", read="b"),
            FATransition(source="q2", target="q1", read="a"),
            FATransition(source="q2", target="q3", read="b"),
            FATransition(source="q3", target="q3", read="a"),
            FATransition(source="q3", target="q3", read="b"),
        ],
    )


def _dfa_even_zeros() -> Automaton:
    """DFA over {0, 1} accepting strings with an even number of 0s."""
    return Automaton(
        type=AutomatonType.DFA,
        name="even-zeros",
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


def _dfa_partial() -> Automaton:
    """Partial DFA that gets stuck on 'b' from q0 (no b-transition defined)."""
    return Automaton(
        type=AutomatonType.DFA,
        name="a-plus",
        states=[State(id="q0"), State(id="q1")],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions=[
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q1", target="q1", read="a"),
            # no 'b' transitions at all
        ],
    )


class TestContainsABB:
    @pytest.mark.parametrize(
        "word",
        ["abb", "aabb", "babb", "abbb", "aabba", "abab" * 2 + "abb", "aaabbbabb"],
    )
    def test_accepts(self, word: str) -> None:
        sim = DFASimulator(_dfa_contains_abb())
        assert sim.accepts(word) is True

    @pytest.mark.parametrize("word", ["", "a", "b", "ab", "ba", "bab", "aaab", "baabab"])
    def test_rejects(self, word: str) -> None:
        sim = DFASimulator(_dfa_contains_abb())
        assert sim.accepts(word) is False

    def test_trace_structure(self) -> None:
        sim = DFASimulator(_dfa_contains_abb())
        trace = sim.run("abb")
        assert trace.accepted is True
        assert trace.verdict is Verdict.ACCEPTED
        assert trace.final_state == "q3"
        assert [s.symbol for s in trace.steps] == ["a", "b", "b"]
        assert [s.from_state for s in trace.steps] == ["q0", "q1", "q2"]
        assert [s.to_state for s in trace.steps] == ["q1", "q2", "q3"]


class TestEvenZeros:
    @pytest.mark.parametrize("word", ["", "1", "11", "00", "0011", "10101", "0110", "001", "010"])
    def test_accepts_even_count_of_zeros(self, word: str) -> None:
        assert DFASimulator(_dfa_even_zeros()).accepts(word) is True

    @pytest.mark.parametrize("word", ["0", "0010", "111000", "0001"])
    def test_rejects_odd_count_of_zeros(self, word: str) -> None:
        assert DFASimulator(_dfa_even_zeros()).accepts(word) is False


class TestRejectionVerdicts:
    def test_stuck_when_transition_missing(self) -> None:
        trace = DFASimulator(_dfa_partial()).run("ab")
        assert trace.verdict is Verdict.REJECTED_STUCK
        assert trace.final_state == "q1"  # stuck after reading 'a'

    def test_invalid_symbol_yields_dedicated_verdict(self) -> None:
        trace = DFASimulator(_dfa_even_zeros()).run("0x1")
        assert trace.verdict is Verdict.REJECTED_INVALID_SYMBOL

    def test_non_accepting_final_state(self) -> None:
        trace = DFASimulator(_dfa_even_zeros()).run("0")
        assert trace.verdict is Verdict.REJECTED_NON_ACCEPTING
        assert trace.final_state == "odd"


class TestStepByStep:
    def test_step_api_matches_run(self) -> None:
        sim = DFASimulator(_dfa_contains_abb())
        sim.reset("abb")
        assert sim.current_state == "q0"
        assert sim.position == 0

        steps = []
        while True:
            step = sim.step()
            if step is None:
                break
            steps.append(step)

        assert sim.is_halted
        assert sim.is_accepted
        assert len(steps) == 3
        assert sim.position == 3
        assert sim.current_state == "q3"

    def test_step_before_reset_raises(self) -> None:
        sim = DFASimulator(_dfa_contains_abb())
        with pytest.raises(SimulatorNotReadyError):
            sim.step()

    def test_step_after_halt_returns_none(self) -> None:
        sim = DFASimulator(_dfa_even_zeros())
        sim.reset("0")
        while sim.step() is not None:
            pass
        assert sim.step() is None  # idempotent after halt

    def test_reset_clears_history(self) -> None:
        sim = DFASimulator(_dfa_even_zeros())
        sim.run("00")
        history_before_reset = sim.history
        assert len(history_before_reset) == 2
        sim.reset("1")
        history_after_reset = sim.history
        assert len(history_after_reset) == 0
        assert not sim.is_halted
        assert sim.current_state == "even"


class TestTypeValidation:
    def test_non_dfa_rejected(self) -> None:
        nfa = Automaton(
            type=AutomatonType.NFA,
            states=[State(id="q0", is_initial=True)],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(WrongAutomatonTypeError):
            DFASimulator(nfa)
