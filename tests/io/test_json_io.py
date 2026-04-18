"""JSON round-trip tests — every automaton type must survive a round-trip."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from automata_simulator.core.io import automaton_from_json, automaton_to_json, load_json, save_json
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


def _dfa() -> Automaton:
    return Automaton(
        type=AutomatonType.DFA,
        name="ends-in-a",
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


def _mealy() -> Automaton:
    return Automaton(
        type=AutomatonType.MEALY,
        states=[State(id="S0")],
        alphabet=["a"],
        output_alphabet=["x"],
        initial_state="S0",
        transitions=[MealyTransition(source="S0", target="S0", read="a", write="x")],
    )


def _moore() -> Automaton:
    return Automaton(
        type=AutomatonType.MOORE,
        states=[State(id="r0", moore_output="0")],
        alphabet=["a"],
        output_alphabet=["0"],
        initial_state="r0",
        transitions=[MooreTransition(source="r0", target="r0", read="a")],
    )


def _pda() -> Automaton:
    return Automaton(
        type=AutomatonType.PDA,
        states=[State(id="q0"), State(id="qf")],
        alphabet=["a", "b"],
        stack_alphabet=["Z", "A"],
        stack_start="Z",
        initial_state="q0",
        accepting_states=["qf"],
        transitions=[
            PDATransition(source="q0", target="qf", read=EPSILON, pop="Z", push=("Z",)),
            PDATransition(source="q0", target="q0", read="a", pop="Z", push=("A", "Z")),
        ],
    )


def _tm() -> Automaton:
    return Automaton(
        type=AutomatonType.TM,
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


@pytest.mark.parametrize(
    "factory",
    [_dfa, _epsilon_nfa, _mealy, _moore, _pda, _tm],
    ids=["dfa", "epsilon-nfa", "mealy", "moore", "pda", "tm"],
)
def test_string_round_trip(factory: Callable[[], Automaton]) -> None:
    original = factory()
    round_tripped = automaton_from_json(automaton_to_json(original))
    assert round_tripped == original


def test_file_round_trip(tmp_path: Path) -> None:
    original = _dfa()
    path = tmp_path / "auto.json"
    save_json(original, path)
    assert load_json(path) == original


def test_indent_argument_controls_formatting() -> None:
    payload = automaton_to_json(_dfa(), indent=None)
    assert "\n" not in payload  # compact when indent is None
    payload_pretty = automaton_to_json(_dfa(), indent=4)
    assert "\n" in payload_pretty
