"""PDASimulator tests — a^n b^n (deterministic) and ww^R (non-deterministic)."""

from __future__ import annotations

import pytest

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    PDATransition,
    State,
)
from automata_simulator.core.simulators import (
    PDASimulator,
    Verdict,
    WrongAutomatonTypeError,
)


def _pda_a_n_b_n() -> Automaton:
    """PDA accepting {a^n b^n : n ≥ 0} by final state."""
    return Automaton(
        type=AutomatonType.PDA,
        name="a-n-b-n",
        states=[State(id=s) for s in ("q0", "q1", "qf")],
        alphabet=["a", "b"],
        stack_alphabet=["Z", "A"],
        stack_start="Z",
        initial_state="q0",
        accepting_states=["qf"],
        transitions=[
            # n = 0 fast path
            PDATransition(source="q0", target="qf", read=EPSILON, pop="Z", push=("Z",)),
            # push A for every a
            PDATransition(source="q0", target="q0", read="a", pop="Z", push=("A", "Z")),
            PDATransition(source="q0", target="q0", read="a", pop="A", push=("A", "A")),
            # switch to matching mode on first b
            PDATransition(source="q0", target="q1", read="b", pop="A", push=()),
            # pop one A per b
            PDATransition(source="q1", target="q1", read="b", pop="A", push=()),
            # accept when stack bottom is reached
            PDATransition(source="q1", target="qf", read=EPSILON, pop="Z", push=("Z",)),
        ],
    )


def _pda_even_palindromes() -> Automaton:
    """Non-deterministic PDA accepting even-length palindromes over {a,b}.

    Language L = {ww^R : w ∈ {a,b}*}. Classic Sipser example where the PDA
    must "guess" the midpoint non-deterministically.
    """
    return Automaton(
        type=AutomatonType.PDA,
        name="even-palindromes",
        states=[State(id=s) for s in ("q0", "q1", "qf")],
        alphabet=["a", "b"],
        stack_alphabet=["Z", "A", "B"],
        stack_start="Z",
        initial_state="q0",
        accepting_states=["qf"],
        transitions=[
            # Empty-string acceptance
            PDATransition(source="q0", target="qf", read=EPSILON, pop="Z", push=("Z",)),
            # Push mode — stack new symbols
            PDATransition(source="q0", target="q0", read="a", pop=EPSILON, push=("A",)),
            PDATransition(source="q0", target="q0", read="b", pop=EPSILON, push=("B",)),
            # Guess midpoint (non-deterministic ε jump)
            PDATransition(source="q0", target="q1", read=EPSILON, pop=EPSILON, push=()),
            # Match mode — pop symbols
            PDATransition(source="q1", target="q1", read="a", pop="A", push=()),
            PDATransition(source="q1", target="q1", read="b", pop="B", push=()),
            # Accept when bottom reached
            PDATransition(source="q1", target="qf", read=EPSILON, pop="Z", push=("Z",)),
        ],
    )


class TestPDAaNbN:
    @pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 8])
    def test_accepts_balanced(self, n: int) -> None:
        sim = PDASimulator(_pda_a_n_b_n())
        assert sim.accepts("a" * n + "b" * n) is True

    @pytest.mark.parametrize("word", ["a", "b", "ab" * 2, "aab", "abb", "ba"])
    def test_rejects_unbalanced(self, word: str) -> None:
        assert PDASimulator(_pda_a_n_b_n()).accepts(word) is False

    def test_trace_length_matches_consumption(self) -> None:
        trace = PDASimulator(_pda_a_n_b_n()).run("aabb")
        assert trace.verdict is Verdict.ACCEPTED
        # 2 pushes + 2 pops + ε-accept. At least len(input) steps.
        assert len(trace.steps) >= 4
        # Final config should be at input end with q state accepting.
        assert trace.final_config is not None
        assert trace.final_config.input_pos == 4
        assert trace.final_config.state == "qf"

    def test_invalid_symbol(self) -> None:
        trace = PDASimulator(_pda_a_n_b_n()).run("aXb")
        assert trace.verdict is Verdict.REJECTED_INVALID_SYMBOL


class TestPDAEvenPalindromes:
    @pytest.mark.parametrize("word", ["", "aa", "bb", "abba", "baab", "aabbaa"])
    def test_accepts(self, word: str) -> None:
        assert PDASimulator(_pda_even_palindromes()).accepts(word) is True

    @pytest.mark.parametrize("word", ["a", "ab", "aba", "abab", "aabb"])
    def test_rejects(self, word: str) -> None:
        assert PDASimulator(_pda_even_palindromes()).accepts(word) is False


class TestPDAStepLimit:
    def test_timeout_verdict_on_runaway_epsilon_loop(self) -> None:
        # Machine with a useless ε-loop that never accepts.
        loopy = Automaton(
            type=AutomatonType.PDA,
            states=[State(id="q0")],
            alphabet=["a"],
            stack_alphabet=["Z"],
            stack_start="Z",
            initial_state="q0",
            accepting_states=[],  # no way to accept — must exhaust
            transitions=[
                PDATransition(source="q0", target="q0", read=EPSILON, pop="Z", push=("Z", "Z")),
            ],
        )
        sim = PDASimulator(loopy, step_limit=50)
        assert sim.run("").verdict is Verdict.REJECTED_TIMEOUT

    def test_step_limit_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="step_limit"):
            PDASimulator(_pda_a_n_b_n(), step_limit=0)


class TestPDATypeValidation:
    def test_rejects_non_pda(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(WrongAutomatonTypeError):
            PDASimulator(dfa)
