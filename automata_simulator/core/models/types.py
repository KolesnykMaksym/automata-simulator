"""Shared enums and constants for the automaton domain model.

Summary (UA): Перелічення типів автоматів, напрямків руху стрічки ТМ
та константи ε / blank.
Summary (EN): Enumerations for automaton kinds and Turing-machine tape-move
directions, plus the ε (epsilon) and default blank-symbol constants.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

EPSILON: Final[str] = "ε"
"""The canonical ε symbol used for epsilon transitions."""

DEFAULT_BLANK: Final[str] = "□"
"""Default blank symbol for Turing-machine tapes (U+25A1 WHITE SQUARE)."""


class AutomatonType(StrEnum):
    """Enumeration of every automaton class supported by the simulator."""

    DFA = "dfa"
    NFA = "nfa"
    EPSILON_NFA = "epsilon-nfa"
    MEALY = "mealy"
    MOORE = "moore"
    PDA = "pda"
    TM = "tm"


class TapeMove(StrEnum):
    """Direction of a Turing-machine tape head after a transition."""

    LEFT = "L"
    RIGHT = "R"
    STAY = "S"
