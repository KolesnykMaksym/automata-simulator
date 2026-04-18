"""The top-level ``Automaton`` aggregate.

Summary (UA): Єдина модель автомата з типом (DFA/NFA/ε-NFA/Mealy/Moore/PDA/TM),
станами, переходами та кросс-валідацією структурної коректності.
Summary (EN): One model to rule them all — carries the automaton type, states,
transitions, and all per-type aux alphabets. Cross-field validators enforce
structural consistency for each automaton flavour.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from automata_simulator.core.models.state import State
from automata_simulator.core.models.transition import (
    FATransition,
    MealyTransition,
    MooreTransition,
    PDATransition,
    TMTransition,
    Transition,
)
from automata_simulator.core.models.types import (
    DEFAULT_BLANK,
    EPSILON,
    AutomatonType,
)

_REQUIRED_KIND: dict[AutomatonType, str] = {
    AutomatonType.DFA: "fa",
    AutomatonType.NFA: "fa",
    AutomatonType.EPSILON_NFA: "fa",
    AutomatonType.MEALY: "mealy",
    AutomatonType.MOORE: "moore",
    AutomatonType.PDA: "pda",
    AutomatonType.TM: "tm",
}


class Automaton(BaseModel):
    """An automaton of any supported type, validated on construction.

    Only the fields relevant to the chosen ``type`` need to be populated; the
    ``model_validator`` checks that the rest are absent or trivially defaulted.
    """

    model_config = ConfigDict(extra="forbid")

    type: AutomatonType
    name: str = "automaton"
    states: list[State]
    alphabet: list[str] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)
    initial_state: str
    accepting_states: list[str] = Field(default_factory=list)

    # Mealy / Moore
    output_alphabet: list[str] | None = None

    # PDA
    stack_alphabet: list[str] | None = None
    stack_start: str | None = None

    # TM
    tape_alphabet: list[str] | None = None
    blank_symbol: str = DEFAULT_BLANK
    tape_count: int = 1

    # ---------------------------------------------------------------- field-level
    @field_validator("alphabet", "stack_alphabet", "tape_alphabet", "output_alphabet")
    @classmethod
    def _alphabet_clean(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        seen: set[str] = set()
        for symbol in value:
            if symbol == "":
                raise ValueError("Alphabet symbols must be non-empty strings")
            if symbol == EPSILON:
                raise ValueError(f"Alphabet must not contain the epsilon marker {EPSILON!r}")
            if symbol in seen:
                raise ValueError(f"Duplicate alphabet symbol: {symbol!r}")
            seen.add(symbol)
        return value

    # ---------------------------------------------------------------- cross-field
    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        if not self.states:
            raise ValueError("Automaton must have at least one state")

        ids = [s.id for s in self.states]
        if len(ids) != len(set(ids)):
            duplicates = sorted({sid for sid in ids if ids.count(sid) > 1})
            raise ValueError(f"Duplicate state ids: {duplicates}")
        id_set = set(ids)

        if self.initial_state not in id_set:
            raise ValueError(f"Initial state {self.initial_state!r} is not among states")

        for acc in self.accepting_states:
            if acc not in id_set:
                raise ValueError(f"Accepting state {acc!r} is not among states")

        required_kind = _REQUIRED_KIND[self.type]
        for tr in self.transitions:
            if tr.kind != required_kind:
                raise ValueError(
                    f"Automaton type {self.type.value!r} requires transitions of kind "
                    f"{required_kind!r}; got {tr.kind!r}",
                )
            if tr.source not in id_set:
                raise ValueError(f"Transition source {tr.source!r} is not among states")
            if tr.target not in id_set:
                raise ValueError(f"Transition target {tr.target!r} is not among states")

        dispatch = {
            AutomatonType.DFA: self._check_dfa,
            AutomatonType.NFA: lambda: self._check_fa_symbols(allow_epsilon=False),
            AutomatonType.EPSILON_NFA: lambda: self._check_fa_symbols(allow_epsilon=True),
            AutomatonType.MEALY: self._check_mealy,
            AutomatonType.MOORE: self._check_moore,
            AutomatonType.PDA: self._check_pda,
            AutomatonType.TM: self._check_tm,
        }
        dispatch[self.type]()
        return self

    # ---------------------------------------------------------------- per-type
    def _check_dfa(self) -> None:
        seen_keys: set[tuple[str, str]] = set()
        for tr in self.transitions:
            assert isinstance(tr, FATransition)
            if tr.read == EPSILON:
                raise ValueError("DFA transitions must not use ε")
            if tr.read not in self.alphabet:
                raise ValueError(f"DFA transition reads symbol {tr.read!r} not in alphabet")
            key = (tr.source, tr.read)
            if key in seen_keys:
                raise ValueError(
                    f"DFA is non-deterministic: state {tr.source!r} has multiple "
                    f"transitions on symbol {tr.read!r}",
                )
            seen_keys.add(key)

    def _check_fa_symbols(self, *, allow_epsilon: bool) -> None:
        for tr in self.transitions:
            assert isinstance(tr, FATransition)
            if tr.read == EPSILON:
                if not allow_epsilon:
                    raise ValueError(
                        "NFA (non-ε) transitions must not use ε — use EPSILON_NFA instead",
                    )
            elif tr.read not in self.alphabet:
                raise ValueError(f"FA transition reads symbol {tr.read!r} not in alphabet")

    def _check_mealy(self) -> None:
        if not self.output_alphabet:
            raise ValueError("Mealy machine requires a non-empty output_alphabet")
        for tr in self.transitions:
            assert isinstance(tr, MealyTransition)
            if tr.read not in self.alphabet:
                raise ValueError(f"Mealy transition reads symbol {tr.read!r} not in alphabet")
            if tr.write not in self.output_alphabet:
                raise ValueError(
                    f"Mealy transition writes symbol {tr.write!r} not in output_alphabet",
                )

    def _check_moore(self) -> None:
        if not self.output_alphabet:
            raise ValueError("Moore machine requires a non-empty output_alphabet")
        for st in self.states:
            if st.moore_output is None:
                raise ValueError(f"Moore state {st.id!r} is missing moore_output")
            if st.moore_output not in self.output_alphabet:
                raise ValueError(
                    f"State {st.id!r}: moore_output {st.moore_output!r} not in output_alphabet",
                )
        for tr in self.transitions:
            assert isinstance(tr, MooreTransition)
            if tr.read not in self.alphabet:
                raise ValueError(f"Moore transition reads symbol {tr.read!r} not in alphabet")

    def _check_pda(self) -> None:
        if not self.stack_alphabet:
            raise ValueError("PDA requires a non-empty stack_alphabet")
        if self.stack_start is None:
            raise ValueError("PDA requires a stack_start symbol (Z₀)")
        if self.stack_start not in self.stack_alphabet:
            raise ValueError(
                f"PDA stack_start {self.stack_start!r} is not in stack_alphabet",
            )
        for tr in self.transitions:
            assert isinstance(tr, PDATransition)
            if tr.read != EPSILON and tr.read not in self.alphabet:
                raise ValueError(
                    f"PDA transition reads {tr.read!r} not in alphabet ∪ {{ε}}",
                )
            if tr.pop != EPSILON and tr.pop not in self.stack_alphabet:
                raise ValueError(
                    f"PDA transition pop {tr.pop!r} not in stack_alphabet ∪ {{ε}}",
                )
            for sym in tr.push:
                if sym not in self.stack_alphabet:
                    raise ValueError(
                        f"PDA transition push symbol {sym!r} not in stack_alphabet",
                    )

    def _check_tm(self) -> None:
        if not self.tape_alphabet:
            raise ValueError("TM requires a non-empty tape_alphabet")
        if self.blank_symbol not in self.tape_alphabet:
            raise ValueError(f"TM blank_symbol {self.blank_symbol!r} not in tape_alphabet")
        if self.tape_count < 1:
            raise ValueError("TM tape_count must be ≥ 1")
        for sym in self.alphabet:
            if sym not in self.tape_alphabet:
                raise ValueError(
                    f"TM input alphabet symbol {sym!r} must also appear in tape_alphabet",
                )
        for tr in self.transitions:
            assert isinstance(tr, TMTransition)
            if len(tr.read) != self.tape_count:
                raise ValueError(
                    f"TM transition arity {len(tr.read)} does not match tape_count "
                    f"{self.tape_count}",
                )
            for sym in (*tr.read, *tr.write):
                if sym not in self.tape_alphabet:
                    raise ValueError(
                        f"TM transition uses symbol {sym!r} not in tape_alphabet",
                    )

    # ---------------------------------------------------------------- accessors
    def states_by_id(self) -> dict[str, State]:
        """Return ``{state.id: state}`` for O(1) lookup."""
        return {s.id: s for s in self.states}

    def get_state(self, state_id: str) -> State:
        """Return the state with the given id or raise ``KeyError``."""
        by_id = self.states_by_id()
        if state_id not in by_id:
            raise KeyError(f"No such state: {state_id!r}")
        return by_id[state_id]

    def initial(self) -> State:
        """Return the initial state object."""
        return self.get_state(self.initial_state)

    def transitions_from(self, state_id: str) -> list[Transition]:
        """Return all transitions whose source is ``state_id``."""
        return [tr for tr in self.transitions if tr.source == state_id]

    def is_deterministic(self) -> bool:
        """Return ``True`` iff the automaton is obviously deterministic.

        For DFA this is always ``True`` (enforced by the validator). For
        NFA / ε-NFA this returns ``True`` when there is no ε-transition and
        at most one transition per ``(state, symbol)`` pair. For any other
        automaton type this returns ``False`` — determinism for PDA/TM is a
        semantic property of the simulator, not the structural model.
        """
        if self.type == AutomatonType.DFA:
            return True
        if self.type not in (AutomatonType.NFA, AutomatonType.EPSILON_NFA):
            return False
        seen: set[tuple[str, str]] = set()
        for tr in self.transitions:
            assert isinstance(tr, FATransition)
            if tr.read == EPSILON:
                return False
            key = (tr.source, tr.read)
            if key in seen:
                return False
            seen.add(key)
        return True
