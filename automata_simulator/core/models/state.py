"""The ``State`` node of an automaton.

Summary (UA): Стан автомата з прапорами початкового/прикінцевого та вихідним
символом для машини Мура.
Summary (EN): Automaton state node with initial/accepting flags and a Moore
output symbol slot.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from automata_simulator.core.models.position import Position


class State(BaseModel):
    """A vertex of the automaton graph.

    Attributes:
        id: Unique identifier (stable across edits and (de)serialisation).
        label: Optional human-friendly label shown on the canvas.
        is_initial: Whether this state is the starting state.
        is_accepting: Whether this state is a final / accepting state.
        moore_output: Output symbol for Moore machines (must be ``None`` for
            every other automaton type).
        position: Optional canvas coordinates for the GUI editor.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str | None = None
    is_initial: bool = False
    is_accepting: bool = False
    moore_output: str | None = None
    position: Position | None = None

    @field_validator("id")
    @classmethod
    def _id_nonempty(cls, value: str) -> str:
        if not value:
            raise ValueError("State id must be a non-empty string")
        return value

    @property
    def display_name(self) -> str:
        """Label if set, otherwise the raw id — convenience for the UI."""
        return self.label if self.label else self.id
