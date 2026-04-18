"""MooreSimulator tests — binary mod-3 counter."""

from __future__ import annotations

import pytest

from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    MooreTransition,
    State,
)
from automata_simulator.core.simulators import (
    MooreSimulator,
    Verdict,
    WrongAutomatonTypeError,
)


def _moore_mod3() -> Automaton:
    """Moore machine whose state output is (binary value of prefix) mod 3."""
    return Automaton(
        type=AutomatonType.MOORE,
        name="mod3",
        states=[
            State(id="r0", moore_output="0"),
            State(id="r1", moore_output="1"),
            State(id="r2", moore_output="2"),
        ],
        alphabet=["0", "1"],
        output_alphabet=["0", "1", "2"],
        initial_state="r0",
        transitions=[
            MooreTransition(source="r0", target="r0", read="0"),
            MooreTransition(source="r0", target="r1", read="1"),
            MooreTransition(source="r1", target="r2", read="0"),
            MooreTransition(source="r1", target="r0", read="1"),
            MooreTransition(source="r2", target="r1", read="0"),
            MooreTransition(source="r2", target="r2", read="1"),
        ],
    )


class TestMooreMod3:
    @pytest.mark.parametrize(
        ("input_word", "expected_last_output"),
        [
            ("", "0"),  # 0 mod 3 = 0
            ("1", "1"),  # 1 mod 3 = 1
            ("10", "2"),  # 2 mod 3 = 2
            ("11", "0"),  # 3 mod 3 = 0
            ("110", "0"),  # 6 mod 3 = 0
            ("1101", "1"),  # 13 mod 3 = 1
            ("11011", "0"),  # 27 mod 3 = 0
        ],
    )
    def test_last_output_equals_value_mod_three(
        self,
        input_word: str,
        expected_last_output: str,
    ) -> None:
        out = MooreSimulator(_moore_mod3()).translate(input_word)
        assert out[-1] == expected_last_output

    def test_output_length_is_input_length_plus_one(self) -> None:
        out = MooreSimulator(_moore_mod3()).translate("1101")
        assert len(out) == 5  # 4 input chars + initial state output

    def test_first_output_is_initial_state_output(self) -> None:
        out = MooreSimulator(_moore_mod3()).translate("111")
        assert out[0] == "0"  # initial state r0 -> "0"

    def test_trace_after_reset_contains_initial_output(self) -> None:
        sim = MooreSimulator(_moore_mod3())
        sim.reset("1")
        # Initial output is already in the buffer even before any step.
        output_before_step = sim.output
        assert output_before_step == ("0",)
        sim.step()
        output_after_step = sim.output
        assert output_after_step == ("0", "1")

    def test_verdict_is_accepted_without_accepting_states(self) -> None:
        trace = MooreSimulator(_moore_mod3()).run("110")
        assert trace.verdict is Verdict.ACCEPTED


class TestMooreTypeValidation:
    def test_rejects_non_moore(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(WrongAutomatonTypeError):
            MooreSimulator(dfa)
