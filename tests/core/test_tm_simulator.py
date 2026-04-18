"""TMSimulator tests — bit-inverter and 0^n 1^n recogniser."""

from __future__ import annotations

import pytest

from automata_simulator.core.models import (
    DEFAULT_BLANK,
    Automaton,
    AutomatonType,
    State,
    TapeMove,
    TMTransition,
)
from automata_simulator.core.simulators import (
    TMSimulator,
    Verdict,
    WrongAutomatonTypeError,
)


def _tm_bit_inverter() -> Automaton:
    """Deterministic TM that flips every bit on the tape and halts."""
    return Automaton(
        type=AutomatonType.TM,
        name="bit-inverter",
        tape_count=1,
        states=[
            State(id="q0", is_initial=True),
            State(id="halt", is_accepting=True),
        ],
        alphabet=["0", "1"],
        tape_alphabet=["0", "1", DEFAULT_BLANK],
        initial_state="q0",
        accepting_states=["halt"],
        transitions=[
            TMTransition(
                source="q0",
                target="q0",
                read=("0",),
                write=("1",),
                move=(TapeMove.RIGHT,),
            ),
            TMTransition(
                source="q0",
                target="q0",
                read=("1",),
                write=("0",),
                move=(TapeMove.RIGHT,),
            ),
            TMTransition(
                source="q0",
                target="halt",
                read=(DEFAULT_BLANK,),
                write=(DEFAULT_BLANK,),
                move=(TapeMove.STAY,),
            ),
        ],
    )


def _tm_zero_n_one_n() -> Automaton:
    """Sipser Example 3.7-style TM for L = {0^n 1^n : n ≥ 0}."""
    return Automaton(
        type=AutomatonType.TM,
        name="0n-1n",
        tape_count=1,
        states=[
            State(id="q0", is_initial=True),  # looking for next 0 at left
            State(id="q1"),  # scanning right, found an X, looking for 1
            State(id="q2"),  # walking back to leftmost unmarked 0
            State(id="q3"),  # saw X at q0 start → check remaining are Y's
            State(id="qacc", is_accepting=True),
        ],
        alphabet=["0", "1"],
        tape_alphabet=["0", "1", "X", "Y", DEFAULT_BLANK],
        initial_state="q0",
        accepting_states=["qacc"],
        transitions=[
            # Empty tape — accept immediately.
            TMTransition(
                source="q0",
                target="qacc",
                read=(DEFAULT_BLANK,),
                write=(DEFAULT_BLANK,),
                move=(TapeMove.STAY,),
            ),
            # Mark the next '0' as 'X' and go hunt a '1'.
            TMTransition(
                source="q0",
                target="q1",
                read=("0",),
                write=("X",),
                move=(TapeMove.RIGHT,),
            ),
            # If we see a Y at q0 start, then all 0s are consumed — make sure no 1s remain.
            TMTransition(
                source="q0",
                target="q3",
                read=("Y",),
                write=("Y",),
                move=(TapeMove.RIGHT,),
            ),
            # q1: walk right over 0s and Ys, find a 1.
            TMTransition(
                source="q1",
                target="q1",
                read=("0",),
                write=("0",),
                move=(TapeMove.RIGHT,),
            ),
            TMTransition(
                source="q1",
                target="q1",
                read=("Y",),
                write=("Y",),
                move=(TapeMove.RIGHT,),
            ),
            TMTransition(
                source="q1",
                target="q2",
                read=("1",),
                write=("Y",),
                move=(TapeMove.LEFT,),
            ),
            # q2: walk left back to the X we wrote.
            TMTransition(
                source="q2",
                target="q2",
                read=("0",),
                write=("0",),
                move=(TapeMove.LEFT,),
            ),
            TMTransition(
                source="q2",
                target="q2",
                read=("Y",),
                write=("Y",),
                move=(TapeMove.LEFT,),
            ),
            TMTransition(
                source="q2",
                target="q0",
                read=("X",),
                write=("X",),
                move=(TapeMove.RIGHT,),
            ),
            # q3: verify only Ys remain then blank → accept.
            TMTransition(
                source="q3",
                target="q3",
                read=("Y",),
                write=("Y",),
                move=(TapeMove.RIGHT,),
            ),
            TMTransition(
                source="q3",
                target="qacc",
                read=(DEFAULT_BLANK,),
                write=(DEFAULT_BLANK,),
                move=(TapeMove.STAY,),
            ),
        ],
    )


class TestTMBitInverter:
    def test_flips_all_bits(self) -> None:
        sim = TMSimulator(_tm_bit_inverter())
        trace = sim.run("01101")
        assert trace.verdict is Verdict.ACCEPTED
        assert trace.final_config is not None
        # Tape 0 should contain the inverted bits (plus trailing blank).
        cells = trace.final_config.tapes[0]
        inverted = "".join(c for c in cells if c != DEFAULT_BLANK)
        assert inverted == "10010"

    def test_empty_input_accepts(self) -> None:
        # Empty input → head reads blank → q0 transitions to halt.
        sim = TMSimulator(_tm_bit_inverter())
        trace = sim.run("")
        assert trace.verdict is Verdict.ACCEPTED

    def test_step_api(self) -> None:
        sim = TMSimulator(_tm_bit_inverter())
        sim.reset("10")
        first = sim.step()
        assert first is not None
        assert first.from_config.state == "q0"
        assert first.to_config.heads[0] == 1


class TestTM0n1n:
    @pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 7])
    def test_accepts_balanced(self, n: int) -> None:
        assert TMSimulator(_tm_zero_n_one_n()).accepts("0" * n + "1" * n) is True

    @pytest.mark.parametrize(
        "word",
        ["0", "1", "00", "11", "01" * 2, "001", "011", "00011", "00111"],
    )
    def test_rejects_unbalanced(self, word: str) -> None:
        assert TMSimulator(_tm_zero_n_one_n()).accepts(word) is False

    @pytest.mark.parametrize("word", ["10", "1001"])
    def test_rejects_wrong_order(self, word: str) -> None:
        # Leading 1s mean q0 has no transition — REJECTED_STUCK.
        trace = TMSimulator(_tm_zero_n_one_n()).run(word)
        assert trace.verdict is Verdict.REJECTED_STUCK


class TestTMStepLimit:
    def test_step_limit_triggers_timeout(self) -> None:
        # TM that loops forever on an empty tape.
        looper = Automaton(
            type=AutomatonType.TM,
            tape_count=1,
            states=[State(id="q0", is_initial=True)],
            alphabet=[],
            tape_alphabet=[DEFAULT_BLANK],
            initial_state="q0",
            accepting_states=[],
            transitions=[
                TMTransition(
                    source="q0",
                    target="q0",
                    read=(DEFAULT_BLANK,),
                    write=(DEFAULT_BLANK,),
                    move=(TapeMove.RIGHT,),
                ),
            ],
        )
        assert TMSimulator(looper, step_limit=10).run("").verdict is Verdict.REJECTED_TIMEOUT

    def test_step_limit_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="step_limit"):
            TMSimulator(_tm_bit_inverter(), step_limit=0)


class TestTMNonDeterminismRejected:
    def test_rejects_non_deterministic_tm(self) -> None:
        # Two transitions from the same (state, read) tuple.
        auto = Automaton(
            type=AutomatonType.TM,
            tape_count=1,
            states=[State(id="q0", is_initial=True), State(id="q1"), State(id="q2")],
            alphabet=["a"],
            tape_alphabet=["a", DEFAULT_BLANK],
            initial_state="q0",
            accepting_states=[],
            transitions=[
                TMTransition(
                    source="q0",
                    target="q1",
                    read=("a",),
                    write=("a",),
                    move=(TapeMove.RIGHT,),
                ),
                TMTransition(
                    source="q0",
                    target="q2",
                    read=("a",),
                    write=("a",),
                    move=(TapeMove.LEFT,),
                ),
            ],
        )
        with pytest.raises(ValueError, match="non-deterministic"):
            TMSimulator(auto)


class TestTMTypeValidation:
    def test_rejects_non_tm(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(WrongAutomatonTypeError):
            TMSimulator(dfa)
