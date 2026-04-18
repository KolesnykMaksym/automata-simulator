"""MealySimulator tests — sequential 101-detector transducer."""

from __future__ import annotations

import pytest

from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    MealyTransition,
    State,
)
from automata_simulator.core.simulators import (
    MealySimulator,
    Verdict,
    WrongAutomatonTypeError,
)


def _mealy_detect_101() -> Automaton:
    """Classic Mealy machine that outputs 1 exactly when it has just seen "101"."""
    return Automaton(
        type=AutomatonType.MEALY,
        name="detect-101",
        states=[State(id="S0"), State(id="S1"), State(id="S2")],
        alphabet=["0", "1"],
        output_alphabet=["0", "1"],
        initial_state="S0",
        transitions=[
            MealyTransition(source="S0", target="S0", read="0", write="0"),
            MealyTransition(source="S0", target="S1", read="1", write="0"),
            MealyTransition(source="S1", target="S2", read="0", write="0"),
            MealyTransition(source="S1", target="S1", read="1", write="0"),
            MealyTransition(source="S2", target="S0", read="0", write="0"),
            MealyTransition(source="S2", target="S1", read="1", write="1"),
        ],
    )


class TestMealyDetect101:
    @pytest.mark.parametrize(
        ("input_word", "expected_output"),
        [
            ("", ""),
            ("0", "0"),
            ("1", "0"),
            ("101", "001"),  # detects itself on the final '1'
            ("11010", "00010"),  # "101" completes at position 3
            ("10101", "00101"),  # two "101" windows, both detected
            ("1011010", "0010010"),  # "101" at positions 2 and 5
        ],
    )
    def test_translate(self, input_word: str, expected_output: str) -> None:
        sim = MealySimulator(_mealy_detect_101())
        assert "".join(sim.translate(input_word)) == expected_output

    def test_accepts_when_no_accepting_set_defined(self) -> None:
        # With no accepting_states, full consumption means ACCEPTED.
        sim = MealySimulator(_mealy_detect_101())
        trace = sim.run("11010")
        assert trace.verdict is Verdict.ACCEPTED
        assert trace.accepted is True

    def test_stuck_when_transition_missing(self) -> None:
        # Build a partial Mealy with no 'b' transition from S0.
        auto = Automaton(
            type=AutomatonType.MEALY,
            states=[State(id="S0")],
            alphabet=["a", "b"],
            output_alphabet=["x"],
            initial_state="S0",
            transitions=[
                MealyTransition(source="S0", target="S0", read="a", write="x"),
            ],
        )
        assert MealySimulator(auto).run("ab").verdict is Verdict.REJECTED_STUCK

    def test_invalid_input_symbol(self) -> None:
        trace = MealySimulator(_mealy_detect_101()).run("12")
        assert trace.verdict is Verdict.REJECTED_INVALID_SYMBOL

    def test_step_api(self) -> None:
        sim = MealySimulator(_mealy_detect_101())
        sim.reset("101")
        assert sim.current_state == "S0"
        first = sim.step()
        assert first is not None
        assert first.output_symbol == "0"
        assert first.to_state == "S1"


class TestMealyTypeValidation:
    def test_rejects_non_mealy(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(WrongAutomatonTypeError):
            MealySimulator(dfa)
