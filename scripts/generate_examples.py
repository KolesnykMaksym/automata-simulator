"""Regenerate files under ``examples/`` from canonical Python factories."""

from __future__ import annotations

from pathlib import Path

from automata_simulator.core.io import save_json
from automata_simulator.core.models import (
    DEFAULT_BLANK,
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    MealyTransition,
    MooreTransition,
    PDATransition,
    Position,
    State,
    TapeMove,
    TMTransition,
)


def dfa_contains_abb() -> Automaton:
    return Automaton(
        type=AutomatonType.DFA,
        name="contains-abb",
        states=[
            State(id="q0", is_initial=True, position=Position(x=0, y=0)),
            State(id="q1", position=Position(x=140, y=0)),
            State(id="q2", position=Position(x=280, y=0)),
            State(id="q3", is_accepting=True, position=Position(x=420, y=0)),
        ],
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


def nfa_ends_in_abb() -> Automaton:
    return Automaton(
        type=AutomatonType.NFA,
        name="ends-in-abb",
        states=[
            State(id="q0", is_initial=True, position=Position(x=0, y=0)),
            State(id="q1", position=Position(x=140, y=0)),
            State(id="q2", position=Position(x=280, y=0)),
            State(id="q3", is_accepting=True, position=Position(x=420, y=0)),
        ],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q3"],
        transitions=[
            FATransition(source="q0", target="q0", read="a"),
            FATransition(source="q0", target="q0", read="b"),
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q1", target="q2", read="b"),
            FATransition(source="q2", target="q3", read="b"),
        ],
    )


def enfa_a_star_b_star() -> Automaton:
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        name="a-star-b-star",
        states=[
            State(id="q0", is_initial=True, is_accepting=True, position=Position(x=0, y=0)),
            State(id="q1", is_accepting=True, position=Position(x=180, y=0)),
        ],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q0", "q1"],
        transitions=[
            FATransition(source="q0", target="q0", read="a"),
            FATransition(source="q0", target="q1", read=EPSILON),
            FATransition(source="q1", target="q1", read="b"),
        ],
    )


def pda_a_n_b_n() -> Automaton:
    return Automaton(
        type=AutomatonType.PDA,
        name="a-n-b-n",
        states=[
            State(id="q0", is_initial=True, position=Position(x=0, y=0)),
            State(id="q1", position=Position(x=180, y=0)),
            State(id="qf", is_accepting=True, position=Position(x=360, y=0)),
        ],
        alphabet=["a", "b"],
        stack_alphabet=["Z", "A"],
        stack_start="Z",
        initial_state="q0",
        accepting_states=["qf"],
        transitions=[
            PDATransition(source="q0", target="qf", read=EPSILON, pop="Z", push=("Z",)),
            PDATransition(source="q0", target="q0", read="a", pop="Z", push=("A", "Z")),
            PDATransition(source="q0", target="q0", read="a", pop="A", push=("A", "A")),
            PDATransition(source="q0", target="q1", read="b", pop="A", push=()),
            PDATransition(source="q1", target="q1", read="b", pop="A", push=()),
            PDATransition(source="q1", target="qf", read=EPSILON, pop="Z", push=("Z",)),
        ],
    )


def tm_bit_inverter() -> Automaton:
    return Automaton(
        type=AutomatonType.TM,
        name="bit-inverter",
        tape_count=1,
        states=[
            State(id="q0", is_initial=True, position=Position(x=0, y=0)),
            State(id="halt", is_accepting=True, position=Position(x=200, y=0)),
        ],
        alphabet=["0", "1"],
        tape_alphabet=["0", "1", DEFAULT_BLANK],
        initial_state="q0",
        accepting_states=["halt"],
        transitions=[
            TMTransition(
                source="q0", target="q0",
                read=("0",), write=("1",), move=(TapeMove.RIGHT,),
            ),
            TMTransition(
                source="q0", target="q0",
                read=("1",), write=("0",), move=(TapeMove.RIGHT,),
            ),
            TMTransition(
                source="q0", target="halt",
                read=(DEFAULT_BLANK,), write=(DEFAULT_BLANK,), move=(TapeMove.STAY,),
            ),
        ],
    )


def mealy_detect_101() -> Automaton:
    return Automaton(
        type=AutomatonType.MEALY,
        name="detect-101",
        states=[
            State(id="S0", is_initial=True, position=Position(x=0, y=0)),
            State(id="S1", position=Position(x=180, y=0)),
            State(id="S2", position=Position(x=360, y=0)),
        ],
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


def moore_mod3() -> Automaton:
    return Automaton(
        type=AutomatonType.MOORE,
        name="mod3",
        states=[
            State(
                id="r0",
                is_initial=True,
                moore_output="0",
                position=Position(x=0, y=0),
            ),
            State(id="r1", moore_output="1", position=Position(x=180, y=0)),
            State(id="r2", moore_output="2", position=Position(x=360, y=0)),
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


def main() -> None:
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    examples_dir.mkdir(exist_ok=True)
    factories = [
        ("dfa_contains_abb.json", dfa_contains_abb),
        ("nfa_ends_in_abb.json", nfa_ends_in_abb),
        ("enfa_a_star_b_star.json", enfa_a_star_b_star),
        ("pda_a_n_b_n.json", pda_a_n_b_n),
        ("tm_bit_inverter.json", tm_bit_inverter),
        ("mealy_detect_101.json", mealy_detect_101),
        ("moore_mod3.json", moore_mod3),
    ]
    for filename, factory in factories:
        path = examples_dir / filename
        save_json(factory(), path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
