"""Graphviz DOT export tests (text only, no binary rendering)."""

from __future__ import annotations

from pathlib import Path

from automata_simulator.core.io import save_dot, to_dot
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


def test_dot_contains_digraph_header() -> None:
    auto = Automaton(
        type=AutomatonType.DFA,
        states=[State(id="q0"), State(id="q1")],
        alphabet=["a"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions=[FATransition(source="q0", target="q1", read="a")],
    )
    out = to_dot(auto)
    assert "digraph" in out
    assert "q0" in out
    assert "q1" in out
    assert "doublecircle" in out  # accepting state


def test_dot_uses_epsilon_for_empty_pop_and_push() -> None:
    auto = Automaton(
        type=AutomatonType.PDA,
        states=[State(id="q0")],
        alphabet=["a"],
        stack_alphabet=["Z"],
        stack_start="Z",
        initial_state="q0",
        transitions=[
            PDATransition(source="q0", target="q0", read=EPSILON, pop="Z", push=()),
        ],
    )
    out = to_dot(auto)
    assert "Z/ε" in out  # push=() shown as ε


def test_dot_tm_label_includes_move() -> None:
    auto = Automaton(
        type=AutomatonType.TM,
        tape_count=1,
        states=[State(id="q0"), State(id="halt")],
        alphabet=["0"],
        tape_alphabet=["0", DEFAULT_BLANK],
        initial_state="q0",
        accepting_states=["halt"],
        transitions=[
            TMTransition(
                source="q0",
                target="halt",
                read=("0",),
                write=("0",),
                move=(TapeMove.RIGHT,),
            ),
        ],
    )
    out = to_dot(auto)
    assert "R" in out  # move=R in the label


def test_dot_mealy_label_is_read_slash_write() -> None:
    auto = Automaton(
        type=AutomatonType.MEALY,
        states=[State(id="S0")],
        alphabet=["a"],
        output_alphabet=["x"],
        initial_state="S0",
        transitions=[MealyTransition(source="S0", target="S0", read="a", write="x")],
    )
    out = to_dot(auto)
    assert "a/x" in out


def test_dot_moore_label_includes_state_output() -> None:
    auto = Automaton(
        type=AutomatonType.MOORE,
        states=[State(id="r0", moore_output="0")],
        alphabet=["a"],
        output_alphabet=["0"],
        initial_state="r0",
        transitions=[MooreTransition(source="r0", target="r0", read="a")],
    )
    out = to_dot(auto)
    assert "/0" in out  # Moore output on state label


def test_save_dot_writes_file(tmp_path: Path) -> None:
    auto = Automaton(
        type=AutomatonType.DFA,
        states=[State(id="q0")],
        alphabet=["a"],
        initial_state="q0",
        transitions=[FATransition(source="q0", target="q0", read="a")],
    )
    path = tmp_path / "g.dot"
    save_dot(auto, path)
    content = path.read_text()
    assert "digraph" in content
