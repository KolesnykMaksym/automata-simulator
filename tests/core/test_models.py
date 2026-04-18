"""Unit tests for the pydantic domain models (Stage 1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

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


# ---------------------------------------------------------------- State / Position
class TestState:
    def test_minimal_state(self) -> None:
        s = State(id="q0")
        assert s.id == "q0"
        assert s.is_initial is False
        assert s.is_accepting is False
        assert s.moore_output is None
        assert s.display_name == "q0"

    def test_label_used_as_display_name(self) -> None:
        s = State(id="q0", label="start")
        assert s.display_name == "start"

    def test_empty_id_rejected(self) -> None:
        with pytest.raises(ValidationError, match="non-empty"):
            State(id="")

    def test_position_defaults(self) -> None:
        p = Position()
        assert p.x == 0.0
        assert p.y == 0.0

    def test_position_is_frozen(self) -> None:
        p = Position(x=1.0, y=2.0)
        with pytest.raises(ValidationError):
            p.x = 5.0


# ---------------------------------------------------------------- TM transition
class TestTMTransition:
    def test_ok_single_tape(self) -> None:
        tr = TMTransition(
            source="q0",
            target="q1",
            read=("a",),
            write=("b",),
            move=(TapeMove.RIGHT,),
        )
        assert tr.kind == "tm"

    def test_mismatched_arity_rejected(self) -> None:
        with pytest.raises(ValidationError, match="arities must match"):
            TMTransition(
                source="q0",
                target="q1",
                read=("a", "b"),
                write=("c",),
                move=(TapeMove.STAY, TapeMove.STAY),
            )

    def test_zero_tapes_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least one tape"):
            TMTransition(source="q0", target="q1", read=(), write=(), move=())


# ---------------------------------------------------------------- DFA
def _two_state_dfa(**overrides: object) -> Automaton:
    defaults: dict[str, object] = {
        "type": AutomatonType.DFA,
        "states": [
            State(id="q0", is_initial=True),
            State(id="q1", is_accepting=True),
        ],
        "alphabet": ["a", "b"],
        "initial_state": "q0",
        "accepting_states": ["q1"],
        "transitions": [
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q0", target="q0", read="b"),
            FATransition(source="q1", target="q1", read="a"),
            FATransition(source="q1", target="q1", read="b"),
        ],
    }
    defaults.update(overrides)
    return Automaton(**defaults)  # type: ignore[arg-type]


class TestDFA:
    def test_happy_path(self) -> None:
        dfa = _two_state_dfa()
        assert dfa.is_deterministic() is True
        assert dfa.initial().id == "q0"
        assert {s.id for s in dfa.states} == {"q0", "q1"}
        assert len(dfa.transitions_from("q0")) == 2

    def test_nondeterminism_rejected(self) -> None:
        with pytest.raises(ValidationError, match="non-deterministic"):
            _two_state_dfa(
                transitions=[
                    FATransition(source="q0", target="q1", read="a"),
                    FATransition(source="q0", target="q0", read="a"),  # duplicate
                ],
            )

    def test_epsilon_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must not use ε"):
            _two_state_dfa(
                transitions=[FATransition(source="q0", target="q1", read=EPSILON)],
            )

    def test_symbol_not_in_alphabet_rejected(self) -> None:
        with pytest.raises(ValidationError, match="not in alphabet"):
            _two_state_dfa(
                transitions=[FATransition(source="q0", target="q1", read="c")],
            )


# ---------------------------------------------------------------- NFA / ε-NFA
class TestNFA:
    def test_nfa_allows_multiple_on_same_symbol(self) -> None:
        nfa = Automaton(
            type=AutomatonType.NFA,
            states=[State(id="q0", is_initial=True), State(id="q1", is_accepting=True)],
            alphabet=["a"],
            initial_state="q0",
            accepting_states=["q1"],
            transitions=[
                FATransition(source="q0", target="q0", read="a"),
                FATransition(source="q0", target="q1", read="a"),
            ],
        )
        assert nfa.is_deterministic() is False

    def test_nfa_rejects_epsilon(self) -> None:
        with pytest.raises(ValidationError, match="must not use ε"):
            Automaton(
                type=AutomatonType.NFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                initial_state="q0",
                transitions=[FATransition(source="q0", target="q0", read=EPSILON)],
            )

    def test_epsilon_nfa_allows_epsilon(self) -> None:
        enfa = Automaton(
            type=AutomatonType.EPSILON_NFA,
            states=[State(id="q0", is_initial=True), State(id="q1", is_accepting=True)],
            alphabet=["a"],
            initial_state="q0",
            accepting_states=["q1"],
            transitions=[
                FATransition(source="q0", target="q1", read=EPSILON),
                FATransition(source="q1", target="q1", read="a"),
            ],
        )
        assert enfa.is_deterministic() is False


# ---------------------------------------------------------------- Mealy / Moore
class TestMealy:
    def test_happy_path(self) -> None:
        mealy = Automaton(
            type=AutomatonType.MEALY,
            states=[State(id="q0", is_initial=True)],
            alphabet=["a", "b"],
            output_alphabet=["0", "1"],
            initial_state="q0",
            transitions=[
                MealyTransition(source="q0", target="q0", read="a", write="0"),
                MealyTransition(source="q0", target="q0", read="b", write="1"),
            ],
        )
        assert mealy.type is AutomatonType.MEALY
        assert mealy.is_deterministic() is False  # Mealy determinism is simulator-level

    def test_requires_output_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="output_alphabet"):
            Automaton(
                type=AutomatonType.MEALY,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                initial_state="q0",
                transitions=[MealyTransition(source="q0", target="q0", read="a", write="0")],
            )

    def test_write_must_be_in_output_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="not in output_alphabet"):
            Automaton(
                type=AutomatonType.MEALY,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                output_alphabet=["0"],
                initial_state="q0",
                transitions=[MealyTransition(source="q0", target="q0", read="a", write="1")],
            )


class TestMoore:
    def test_happy_path(self) -> None:
        moore = Automaton(
            type=AutomatonType.MOORE,
            states=[
                State(id="q0", is_initial=True, moore_output="0"),
                State(id="q1", moore_output="1"),
            ],
            alphabet=["a"],
            output_alphabet=["0", "1"],
            initial_state="q0",
            transitions=[
                MooreTransition(source="q0", target="q1", read="a"),
                MooreTransition(source="q1", target="q0", read="a"),
            ],
        )
        assert moore.get_state("q0").moore_output == "0"

    def test_requires_output_on_each_state(self) -> None:
        with pytest.raises(ValidationError, match="missing moore_output"):
            Automaton(
                type=AutomatonType.MOORE,
                states=[State(id="q0", is_initial=True)],  # no moore_output
                alphabet=["a"],
                output_alphabet=["0"],
                initial_state="q0",
                transitions=[],
            )

    def test_output_symbol_must_be_in_output_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="not in output_alphabet"):
            Automaton(
                type=AutomatonType.MOORE,
                states=[State(id="q0", is_initial=True, moore_output="Z")],
                alphabet=["a"],
                output_alphabet=["0"],
                initial_state="q0",
                transitions=[],
            )


# ---------------------------------------------------------------- PDA
class TestPDA:
    def test_happy_path(self) -> None:
        pda = Automaton(
            type=AutomatonType.PDA,
            states=[State(id="q0", is_initial=True), State(id="q1", is_accepting=True)],
            alphabet=["a", "b"],
            stack_alphabet=["Z", "A"],
            stack_start="Z",
            initial_state="q0",
            accepting_states=["q1"],
            transitions=[
                PDATransition(source="q0", target="q0", read="a", pop="Z", push=("A", "Z")),
                PDATransition(source="q0", target="q0", read="a", pop="A", push=("A", "A")),
                PDATransition(source="q0", target="q1", read="b", pop="A", push=()),
                PDATransition(source="q1", target="q1", read="b", pop="A", push=()),
            ],
        )
        assert pda.stack_start == "Z"

    def test_requires_stack_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="stack_alphabet"):
            Automaton(
                type=AutomatonType.PDA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                stack_start="Z",
                initial_state="q0",
                transitions=[],
            )

    def test_requires_stack_start(self) -> None:
        with pytest.raises(ValidationError, match="stack_start"):
            Automaton(
                type=AutomatonType.PDA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                stack_alphabet=["Z"],
                initial_state="q0",
                transitions=[],
            )

    def test_push_symbol_must_be_in_stack_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="push symbol"):
            Automaton(
                type=AutomatonType.PDA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                stack_alphabet=["Z"],
                stack_start="Z",
                initial_state="q0",
                transitions=[
                    PDATransition(source="q0", target="q0", read="a", pop="Z", push=("X",)),
                ],
            )


# ---------------------------------------------------------------- TM
class TestTM:
    def test_single_tape(self) -> None:
        tm = Automaton(
            type=AutomatonType.TM,
            states=[State(id="q0", is_initial=True), State(id="qacc", is_accepting=True)],
            alphabet=["0", "1"],
            tape_alphabet=["0", "1", DEFAULT_BLANK],
            initial_state="q0",
            accepting_states=["qacc"],
            transitions=[
                TMTransition(
                    source="q0",
                    target="qacc",
                    read=("0",),
                    write=("1",),
                    move=(TapeMove.RIGHT,),
                ),
            ],
        )
        assert tm.tape_count == 1
        assert tm.blank_symbol == DEFAULT_BLANK

    def test_multi_tape(self) -> None:
        tm = Automaton(
            type=AutomatonType.TM,
            tape_count=2,
            states=[State(id="q0", is_initial=True)],
            alphabet=["a"],
            tape_alphabet=["a", DEFAULT_BLANK],
            initial_state="q0",
            transitions=[
                TMTransition(
                    source="q0",
                    target="q0",
                    read=("a", DEFAULT_BLANK),
                    write=("a", "a"),
                    move=(TapeMove.RIGHT, TapeMove.RIGHT),
                ),
            ],
        )
        assert tm.tape_count == 2

    def test_requires_tape_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="tape_alphabet"):
            Automaton(
                type=AutomatonType.TM,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                initial_state="q0",
                transitions=[],
            )

    def test_blank_must_be_in_tape_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="blank_symbol"):
            Automaton(
                type=AutomatonType.TM,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                tape_alphabet=["a"],
                blank_symbol=DEFAULT_BLANK,
                initial_state="q0",
                transitions=[],
            )

    def test_input_alphabet_must_be_subset_of_tape_alphabet(self) -> None:
        with pytest.raises(ValidationError, match="must also appear in tape_alphabet"):
            Automaton(
                type=AutomatonType.TM,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a", "b"],
                tape_alphabet=["a", DEFAULT_BLANK],
                initial_state="q0",
                transitions=[],
            )

    def test_transition_arity_must_match_tape_count(self) -> None:
        with pytest.raises(ValidationError, match="does not match tape_count"):
            Automaton(
                type=AutomatonType.TM,
                tape_count=2,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                tape_alphabet=["a", DEFAULT_BLANK],
                initial_state="q0",
                transitions=[
                    TMTransition(
                        source="q0",
                        target="q0",
                        read=("a",),
                        write=("a",),
                        move=(TapeMove.STAY,),
                    ),
                ],
            )


# ---------------------------------------------------------------- Structural
class TestStructuralValidation:
    def test_duplicate_state_ids_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate state ids"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True), State(id="q0")],
                alphabet=["a"],
                initial_state="q0",
                transitions=[],
            )

    def test_empty_states_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least one state"):
            Automaton(
                type=AutomatonType.DFA,
                states=[],
                alphabet=["a"],
                initial_state="q0",
                transitions=[],
            )

    def test_initial_state_must_exist(self) -> None:
        with pytest.raises(ValidationError, match="Initial state"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0")],
                alphabet=["a"],
                initial_state="q_missing",
                transitions=[],
            )

    def test_accepting_state_must_exist(self) -> None:
        with pytest.raises(ValidationError, match="Accepting state"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                initial_state="q0",
                accepting_states=["q_missing"],
                transitions=[],
            )

    def test_transition_source_must_exist(self) -> None:
        with pytest.raises(ValidationError, match="Transition source"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                initial_state="q0",
                transitions=[FATransition(source="missing", target="q0", read="a")],
            )

    def test_transition_target_must_exist(self) -> None:
        with pytest.raises(ValidationError, match="Transition target"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                initial_state="q0",
                transitions=[FATransition(source="q0", target="missing", read="a")],
            )

    def test_transition_kind_must_match_type(self) -> None:
        with pytest.raises(ValidationError, match="requires transitions of kind"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a"],
                initial_state="q0",
                transitions=[
                    MealyTransition(source="q0", target="q0", read="a", write="x"),
                ],
            )

    def test_alphabet_rejects_empty_symbol(self) -> None:
        with pytest.raises(ValidationError, match="non-empty"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a", ""],
                initial_state="q0",
                transitions=[],
            )

    def test_alphabet_rejects_epsilon(self) -> None:
        with pytest.raises(ValidationError, match="epsilon"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a", EPSILON],
                initial_state="q0",
                transitions=[],
            )

    def test_alphabet_rejects_duplicate_symbol(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate alphabet symbol"):
            Automaton(
                type=AutomatonType.DFA,
                states=[State(id="q0", is_initial=True)],
                alphabet=["a", "a"],
                initial_state="q0",
                transitions=[],
            )


# ---------------------------------------------------------------- Accessors / round-trip
class TestAccessors:
    def test_get_state_raises_on_unknown(self) -> None:
        dfa = _two_state_dfa()
        with pytest.raises(KeyError):
            dfa.get_state("q_unknown")

    def test_transitions_from_returns_only_outgoing(self) -> None:
        dfa = _two_state_dfa()
        out_of_q1 = dfa.transitions_from("q1")
        assert all(t.source == "q1" for t in out_of_q1)
        assert len(out_of_q1) == 2


class TestRoundTrip:
    def test_dfa_json_round_trip(self) -> None:
        dfa = _two_state_dfa()
        payload = dfa.model_dump_json()
        restored = Automaton.model_validate_json(payload)
        assert restored == dfa

    def test_pda_json_round_trip(self) -> None:
        pda = Automaton(
            type=AutomatonType.PDA,
            states=[State(id="q0", is_initial=True), State(id="q1", is_accepting=True)],
            alphabet=["a", "b"],
            stack_alphabet=["Z", "A"],
            stack_start="Z",
            initial_state="q0",
            accepting_states=["q1"],
            transitions=[
                PDATransition(source="q0", target="q0", read="a", pop="Z", push=("A", "Z")),
                PDATransition(source="q0", target="q1", read=EPSILON, pop="Z", push=("Z",)),
            ],
        )
        restored = Automaton.model_validate_json(pda.model_dump_json())
        assert restored == pda
        assert isinstance(restored.transitions[0], PDATransition)

    def test_tm_json_round_trip(self) -> None:
        tm = Automaton(
            type=AutomatonType.TM,
            states=[State(id="q0", is_initial=True), State(id="qacc", is_accepting=True)],
            alphabet=["0", "1"],
            tape_alphabet=["0", "1", DEFAULT_BLANK],
            initial_state="q0",
            accepting_states=["qacc"],
            transitions=[
                TMTransition(
                    source="q0",
                    target="qacc",
                    read=("0",),
                    write=("1",),
                    move=(TapeMove.RIGHT,),
                ),
            ],
        )
        restored = Automaton.model_validate_json(tm.model_dump_json())
        assert restored == tm
        assert isinstance(restored.transitions[0], TMTransition)
