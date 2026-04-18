"""Deterministic Mealy-machine simulator.

Summary (UA): Симулятор детермінованого автомата Мілі — вихідний символ
генерується під час переходу.
Summary (EN): Deterministic Mealy simulator — the output symbol is emitted
on every consumed transition.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    MealyTransition,
)
from automata_simulator.core.simulators.base import (
    SimulatorNotReadyError,
    Verdict,
    WrongAutomatonTypeError,
)


@dataclass(frozen=True, slots=True)
class MealyStep:
    """A single transition of the Mealy simulator."""

    index: int
    from_state: str
    input_symbol: str
    to_state: str
    output_symbol: str


@dataclass(frozen=True, slots=True)
class MealyTrace:
    """Complete record of a Mealy run."""

    input: tuple[str, ...]
    output: tuple[str, ...]
    steps: tuple[MealyStep, ...]
    final_state: str | None
    verdict: Verdict

    @property
    def accepted(self) -> bool:
        """Whether the input was accepted."""
        return self.verdict.is_accepted


class MealySimulator:
    """Step-by-step deterministic Mealy simulator.

    A Mealy machine accepts ``input_string`` when all its symbols have been
    consumed and the current state is in ``accepting_states``. When
    ``accepting_states`` is empty, successful consumption of the entire input
    is considered acceptance (the usual convention for transducers).
    """

    def __init__(self, automaton: Automaton) -> None:
        if automaton.type is not AutomatonType.MEALY:
            raise WrongAutomatonTypeError(
                f"MealySimulator requires a Mealy machine, got {automaton.type.value!r}",
            )
        self._automaton = automaton
        self._table: dict[tuple[str, str], tuple[str, str]] = {}
        for tr in automaton.transitions:
            assert isinstance(tr, MealyTransition)
            self._table[(tr.source, tr.read)] = (tr.target, tr.write)
        self._accepting: frozenset[str] = frozenset(automaton.accepting_states)
        self._alphabet: frozenset[str] = frozenset(automaton.alphabet)

        self._input: tuple[str, ...] = ()
        self._position: int = 0
        self._current: str | None = None
        self._output: list[str] = []
        self._history: list[MealyStep] = []
        self._verdict: Verdict | None = None

    # ---------------------------------------------------------------- introspection
    @property
    def automaton(self) -> Automaton:
        """The underlying Mealy automaton (read-only)."""
        return self._automaton

    @property
    def current_state(self) -> str | None:
        """Current state, or ``None`` before the first :meth:`reset`."""
        return self._current

    @property
    def position(self) -> int:
        """Number of symbols already consumed."""
        return self._position

    @property
    def output(self) -> tuple[str, ...]:
        """Output symbols emitted so far."""
        return tuple(self._output)

    @property
    def history(self) -> tuple[MealyStep, ...]:
        """All steps taken since the last :meth:`reset`."""
        return tuple(self._history)

    @property
    def verdict(self) -> Verdict | None:
        """Verdict once halted, else ``None``."""
        return self._verdict

    @property
    def is_halted(self) -> bool:
        """Whether the simulator has finished the current run."""
        return self._verdict is not None

    @property
    def is_accepted(self) -> bool:
        """Shortcut for ``verdict is Verdict.ACCEPTED``."""
        return self._verdict is Verdict.ACCEPTED

    # ---------------------------------------------------------------- control
    def reset(self, input_string: Sequence[str]) -> None:
        """Place the simulator at the initial state with an empty output."""
        self._input = tuple(input_string)
        self._position = 0
        self._current = self._automaton.initial_state
        self._output = []
        self._history = []
        self._verdict = None

    def step(self) -> MealyStep | None:
        """Consume one symbol, emit one output symbol.

        Returns:
            The step taken, or ``None`` if the run has halted.

        Raises:
            SimulatorNotReadyError: If :meth:`reset` has not been called yet.
        """
        if self._current is None:
            raise SimulatorNotReadyError("call reset(input) before step()")
        if self._verdict is not None:
            return None
        if self._position >= len(self._input):
            self._verdict = self._accept_verdict()
            return None
        symbol = self._input[self._position]
        if symbol not in self._alphabet:
            self._verdict = Verdict.REJECTED_INVALID_SYMBOL
            return None
        key = (self._current, symbol)
        if key not in self._table:
            self._verdict = Verdict.REJECTED_STUCK
            return None
        next_state, out_symbol = self._table[key]
        step = MealyStep(
            index=len(self._history),
            from_state=self._current,
            input_symbol=symbol,
            to_state=next_state,
            output_symbol=out_symbol,
        )
        self._history.append(step)
        self._output.append(out_symbol)
        self._current = next_state
        self._position += 1
        return step

    def run(self, input_string: Sequence[str]) -> MealyTrace:
        """Reset and execute the simulator to completion."""
        self.reset(input_string)
        while self.step() is not None:
            pass
        assert self._verdict is not None
        return MealyTrace(
            input=self._input,
            output=tuple(self._output),
            steps=tuple(self._history),
            final_state=self._current,
            verdict=self._verdict,
        )

    def accepts(self, input_string: Sequence[str]) -> bool:
        """Return ``True`` iff the Mealy machine accepts ``input_string``."""
        return self.run(input_string).accepted

    def translate(self, input_string: Sequence[str]) -> tuple[str, ...]:
        """Return the output string produced for ``input_string`` (may be partial)."""
        return self.run(input_string).output

    # ---------------------------------------------------------------- internals
    def _accept_verdict(self) -> Verdict:
        if not self._accepting:
            return Verdict.ACCEPTED
        assert self._current is not None
        return (
            Verdict.ACCEPTED if self._current in self._accepting else Verdict.REJECTED_NON_ACCEPTING
        )
