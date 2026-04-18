"""Deterministic finite automaton simulator.

Summary (UA): Покроковий симулятор DFA з повною історією, підтримкою reset/step/run
та явним вердиктом (``Verdict``).
Summary (EN): Step-by-step DFA simulator with full history; reset/step/run API
yielding an explicit ``Verdict``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from automata_simulator.core.models import Automaton, AutomatonType, FATransition
from automata_simulator.core.simulators.base import (
    SimulatorNotReadyError,
    Verdict,
    WrongAutomatonTypeError,
)


@dataclass(frozen=True, slots=True)
class DFAStep:
    """One transition fired by the DFA simulator."""

    index: int
    from_state: str
    symbol: str
    to_state: str


@dataclass(frozen=True, slots=True)
class DFATrace:
    """Complete record of a DFA run."""

    input: tuple[str, ...]
    steps: tuple[DFAStep, ...]
    final_state: str | None
    verdict: Verdict

    @property
    def accepted(self) -> bool:
        """Whether the input was accepted."""
        return self.verdict.is_accepted


class DFASimulator:
    """Reusable DFA simulator.

    The simulator keeps per-run mutable state (current position, current state,
    history, verdict) that is reset by :meth:`reset`. Construction is O(|δ|).
    """

    def __init__(self, automaton: Automaton) -> None:
        if automaton.type is not AutomatonType.DFA:
            raise WrongAutomatonTypeError(
                f"DFASimulator requires a DFA, got {automaton.type.value!r}",
            )
        self._automaton = automaton
        self._table: dict[tuple[str, str], str] = {}
        for tr in automaton.transitions:
            assert isinstance(tr, FATransition)
            self._table[(tr.source, tr.read)] = tr.target
        self._accepting: frozenset[str] = frozenset(automaton.accepting_states)
        self._alphabet: frozenset[str] = frozenset(automaton.alphabet)
        self._input: tuple[str, ...] = ()
        self._position: int = 0
        self._current: str | None = None
        self._history: list[DFAStep] = []
        self._verdict: Verdict | None = None

    # ---------------------------------------------------------------- introspection
    @property
    def automaton(self) -> Automaton:
        """The underlying automaton (read-only)."""
        return self._automaton

    @property
    def current_state(self) -> str | None:
        """Currently occupied state, or ``None`` before :meth:`reset`."""
        return self._current

    @property
    def position(self) -> int:
        """Number of symbols already consumed in the current run."""
        return self._position

    @property
    def input(self) -> tuple[str, ...]:
        """Input tape the simulator is currently working on."""
        return self._input

    @property
    def history(self) -> tuple[DFAStep, ...]:
        """All steps taken since the last :meth:`reset`."""
        return tuple(self._history)

    @property
    def verdict(self) -> Verdict | None:
        """The verdict once halted, else ``None``."""
        return self._verdict

    @property
    def is_halted(self) -> bool:
        """Whether the simulator has finished the current run."""
        return self._verdict is not None

    @property
    def is_accepted(self) -> bool:
        """Convenience shortcut for ``verdict is Verdict.ACCEPTED``."""
        return self._verdict is Verdict.ACCEPTED

    # ---------------------------------------------------------------- control
    def reset(self, input_string: Sequence[str]) -> None:
        """Place the simulator at the initial state with ``input_string`` on tape."""
        self._input = tuple(input_string)
        self._position = 0
        self._current = self._automaton.initial_state
        self._history = []
        self._verdict = None

    def step(self) -> DFAStep | None:
        """Advance the simulator by one symbol.

        Returns:
            The step that was just taken, or ``None`` if the run has halted
            (either before this call or because this call halted it).

        Raises:
            SimulatorNotReadyError: If :meth:`reset` has not been called yet.
        """
        if self._current is None:
            raise SimulatorNotReadyError("call reset(input) before step()")
        if self._verdict is not None:
            return None
        if self._position >= len(self._input):
            self._verdict = (
                Verdict.ACCEPTED
                if self._current in self._accepting
                else Verdict.REJECTED_NON_ACCEPTING
            )
            return None
        symbol = self._input[self._position]
        if symbol not in self._alphabet:
            self._verdict = Verdict.REJECTED_INVALID_SYMBOL
            return None
        key = (self._current, symbol)
        if key not in self._table:
            self._verdict = Verdict.REJECTED_STUCK
            return None
        next_state = self._table[key]
        step = DFAStep(
            index=len(self._history),
            from_state=self._current,
            symbol=symbol,
            to_state=next_state,
        )
        self._history.append(step)
        self._current = next_state
        self._position += 1
        return step

    def run(self, input_string: Sequence[str]) -> DFATrace:
        """Reset and execute the simulator to completion."""
        self.reset(input_string)
        while self.step() is not None:
            pass
        assert self._verdict is not None
        return DFATrace(
            input=self._input,
            steps=tuple(self._history),
            final_state=self._current,
            verdict=self._verdict,
        )

    def accepts(self, input_string: Sequence[str]) -> bool:
        """Return ``True`` iff the DFA accepts ``input_string``."""
        return self.run(input_string).accepted
