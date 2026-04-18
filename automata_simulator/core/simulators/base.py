"""Shared simulator primitives (verdicts, common exceptions).

Summary (UA): Спільні типи для всіх симуляторів — вердикти приймання/відхилення
та базові винятки.
Summary (EN): Common vocabulary used by every simulator — acceptance verdicts
and shared exceptions.
"""

from __future__ import annotations

from enum import StrEnum


class Verdict(StrEnum):
    """Outcome of a finished simulation run."""

    ACCEPTED = "accepted"
    REJECTED_NON_ACCEPTING = "rejected:non-accepting-final-state"
    REJECTED_STUCK = "rejected:stuck"
    REJECTED_INVALID_SYMBOL = "rejected:invalid-input-symbol"
    REJECTED_EMPTY_CONFIG = "rejected:empty-configuration"

    @property
    def is_accepted(self) -> bool:
        """Return ``True`` iff this verdict is an acceptance outcome."""
        return self is Verdict.ACCEPTED


class SimulatorNotReadyError(RuntimeError):
    """Raised when ``step()`` is invoked before ``reset()``."""


class WrongAutomatonTypeError(ValueError):
    """Raised when a simulator is given an automaton of the wrong kind."""
