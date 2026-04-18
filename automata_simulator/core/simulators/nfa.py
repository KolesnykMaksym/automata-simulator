"""Non-deterministic finite automaton simulator (supports ε-NFA).

Summary (UA): Симулятор NFA та ε-NFA — тримає множину активних станів,
виконує ε-замикання перед кожною перевіркою приймання.
Summary (EN): NFA / ε-NFA simulator that tracks a frontier of active states
and takes ε-closure after every consumption (and of the initial frontier).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
)
from automata_simulator.core.simulators.base import (
    SimulatorNotReadyError,
    Verdict,
    WrongAutomatonTypeError,
)

_SUPPORTED_TYPES: frozenset[AutomatonType] = frozenset(
    {AutomatonType.NFA, AutomatonType.EPSILON_NFA},
)


@dataclass(frozen=True, slots=True)
class NFAStep:
    """One symbol-consumption step of an NFA simulation.

    ``from_states`` is the ε-closed frontier before reading ``symbol``;
    ``to_states`` is the ε-closed frontier after reading ``symbol``.
    """

    index: int
    from_states: frozenset[str]
    symbol: str
    to_states: frozenset[str]


@dataclass(frozen=True, slots=True)
class NFATrace:
    """Complete record of an NFA run."""

    input: tuple[str, ...]
    steps: tuple[NFAStep, ...]
    final_states: frozenset[str]
    verdict: Verdict

    @property
    def accepted(self) -> bool:
        """Whether the input was accepted."""
        return self.verdict.is_accepted


class NFASimulator:
    """Simulator for NFA and ε-NFA.

    When the underlying automaton is an :attr:`AutomatonType.EPSILON_NFA`,
    ε-closure is applied to the initial frontier and after every consumption.
    For a plain NFA, ε-closure is the identity.
    """

    def __init__(self, automaton: Automaton) -> None:
        if automaton.type not in _SUPPORTED_TYPES:
            raise WrongAutomatonTypeError(
                f"NFASimulator requires NFA or EPSILON_NFA, got {automaton.type.value!r}",
            )
        self._automaton = automaton
        self._allow_epsilon = automaton.type is AutomatonType.EPSILON_NFA
        self._table: dict[tuple[str, str], set[str]] = {}
        for tr in automaton.transitions:
            assert isinstance(tr, FATransition)
            self._table.setdefault((tr.source, tr.read), set()).add(tr.target)
        self._accepting: frozenset[str] = frozenset(automaton.accepting_states)
        self._alphabet: frozenset[str] = frozenset(automaton.alphabet)

        self._input: tuple[str, ...] = ()
        self._position: int = 0
        self._current: frozenset[str] = frozenset()
        self._history: list[NFAStep] = []
        self._verdict: Verdict | None = None
        self._ready: bool = False

    # ---------------------------------------------------------------- introspection
    @property
    def automaton(self) -> Automaton:
        """The underlying automaton (read-only)."""
        return self._automaton

    @property
    def current_states(self) -> frozenset[str]:
        """ε-closed frontier of active states."""
        return self._current

    @property
    def position(self) -> int:
        """Number of symbols already consumed."""
        return self._position

    @property
    def input(self) -> tuple[str, ...]:
        """Input tape for the current run."""
        return self._input

    @property
    def history(self) -> tuple[NFAStep, ...]:
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

    # ---------------------------------------------------------------- internals
    def _epsilon_closure(self, seeds: Iterable[str]) -> frozenset[str]:
        if not self._allow_epsilon:
            return frozenset(seeds)
        result: set[str] = set(seeds)
        stack: list[str] = list(result)
        while stack:
            src = stack.pop()
            for dst in self._table.get((src, EPSILON), ()):
                if dst not in result:
                    result.add(dst)
                    stack.append(dst)
        return frozenset(result)

    # ---------------------------------------------------------------- control
    def reset(self, input_string: Sequence[str]) -> None:
        """Place the simulator at the ε-closure of the initial state."""
        self._input = tuple(input_string)
        self._position = 0
        self._current = self._epsilon_closure({self._automaton.initial_state})
        self._history = []
        self._verdict = None
        self._ready = True

    def step(self) -> NFAStep | None:
        """Consume one symbol and update the active set.

        Returns:
            The step taken, or ``None`` if the run has halted.

        Raises:
            SimulatorNotReadyError: If :meth:`reset` has not been called yet.
        """
        if not self._ready:
            raise SimulatorNotReadyError("call reset(input) before step()")
        if self._verdict is not None:
            return None
        if self._position >= len(self._input):
            self._verdict = (
                Verdict.ACCEPTED
                if self._current & self._accepting
                else Verdict.REJECTED_NON_ACCEPTING
            )
            return None
        symbol = self._input[self._position]
        if symbol not in self._alphabet:
            self._verdict = Verdict.REJECTED_INVALID_SYMBOL
            return None
        raw_next: set[str] = set()
        for src in self._current:
            raw_next.update(self._table.get((src, symbol), ()))
        next_frontier = self._epsilon_closure(raw_next)
        step = NFAStep(
            index=len(self._history),
            from_states=self._current,
            symbol=symbol,
            to_states=next_frontier,
        )
        self._history.append(step)
        self._current = next_frontier
        self._position += 1
        if not next_frontier:
            self._verdict = Verdict.REJECTED_EMPTY_CONFIG
        return step

    def run(self, input_string: Sequence[str]) -> NFATrace:
        """Reset and execute the simulator to completion."""
        self.reset(input_string)
        while self.step() is not None:
            pass
        assert self._verdict is not None
        return NFATrace(
            input=self._input,
            steps=tuple(self._history),
            final_states=self._current,
            verdict=self._verdict,
        )

    def accepts(self, input_string: Sequence[str]) -> bool:
        """Return ``True`` iff the NFA accepts ``input_string``."""
        return self.run(input_string).accepted
