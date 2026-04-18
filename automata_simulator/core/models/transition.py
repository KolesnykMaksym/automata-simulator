"""Transition models for every automaton flavour.

Summary (UA): Моделі переходів для DFA/NFA/ε-NFA (FATransition), Мілі, Мура,
PDA та машини Тьюрінга. Об'єднані в дискримінаторний юніон ``Transition``.
Summary (EN): Transition models split by automaton kind, unified by a
pydantic-discriminated ``Transition`` type alias keyed on ``kind``.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from automata_simulator.core.models.types import TapeMove


class BaseTransition(BaseModel):
    """Common structural fields for every transition kind."""

    model_config = ConfigDict(extra="forbid")

    source: str
    target: str


class FATransition(BaseTransition):
    """Finite-automaton transition used by DFA / NFA / ε-NFA.

    ``read`` is a symbol of the input alphabet Σ, or the ε constant for
    ε-transitions (which only ε-NFA is allowed to carry).
    """

    kind: Literal["fa"] = "fa"
    read: str


class MealyTransition(BaseTransition):
    """Mealy transducer transition: reads from Σ, emits a symbol of Γ."""

    kind: Literal["mealy"] = "mealy"
    read: str
    write: str


class MooreTransition(BaseTransition):
    """Moore transducer transition: reads from Σ (output lives on the state)."""

    kind: Literal["moore"] = "moore"
    read: str


class PDATransition(BaseTransition):
    """Pushdown-automaton transition.

    Attributes:
        read: Input symbol from Σ, or ε.
        pop: Stack symbol expected on top (from Γ), or ε for "don't touch".
        push: Stack symbols to push **top-first** after popping. The empty
            tuple means "pop only, push nothing".
    """

    kind: Literal["pda"] = "pda"
    read: str
    pop: str
    push: tuple[str, ...] = ()


class TMTransition(BaseTransition):
    """Turing-machine transition (multi-tape capable).

    The ``read``/``write``/``move`` tuples are indexed by tape number; their
    length must equal the owning automaton's ``tape_count``.
    """

    kind: Literal["tm"] = "tm"
    read: tuple[str, ...]
    write: tuple[str, ...]
    move: tuple[TapeMove, ...]

    @model_validator(mode="after")
    def _arity_consistent(self) -> Self:
        n = len(self.read)
        if n == 0:
            raise ValueError("TM transition requires at least one tape")
        if len(self.write) != n or len(self.move) != n:
            raise ValueError(
                "TM transition arities must match across tapes "
                f"(read={len(self.read)}, write={len(self.write)}, move={len(self.move)})",
            )
        return self


Transition: TypeAlias = Annotated[
    FATransition | MealyTransition | MooreTransition | PDATransition | TMTransition,
    Field(discriminator="kind"),
]
"""Discriminated union across every transition kind, keyed on ``kind``."""
