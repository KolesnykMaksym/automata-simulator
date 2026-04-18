"""Deterministic Moore-machine simulator.

Summary (UA): Симулятор детермінованого автомата Мура — вихідний символ
пов'язаний зі станом; послідовність виходу має довжину |input| + 1.
Summary (EN): Deterministic Moore simulator — the output symbol lives on the
state, so the emitted sequence has length |input| + 1 (initial output plus
one symbol after each consumed input symbol).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    MooreTransition,
)
from automata_simulator.core.simulators.base import (
    SimulatorNotReadyError,
    Verdict,
    WrongAutomatonTypeError,
)


@dataclass(frozen=True, slots=True)
class MooreStep:
    """A single transition of the Moore simulator."""

    index: int
    from_state: str
    input_symbol: str
    to_state: str
    output_symbol: str  # output of to_state


@dataclass(frozen=True, slots=True)
class MooreTrace:
    """Complete record of a Moore run."""

    input: tuple[str, ...]
    output: tuple[str, ...]  # length == len(input) + 1 if fully consumed
    steps: tuple[MooreStep, ...]
    final_state: str | None
    verdict: Verdict

    @property
    def accepted(self) -> bool:
        """Whether the input was accepted."""
        return self.verdict.is_accepted


class MooreSimulator:
    """Step-by-step deterministic Moore simulator.

    Acceptance semantics mirror :class:`MealySimulator`: all input consumed
    and current state in ``accepting_states`` (or ``accepting_states`` empty).
    """

    def __init__(self, automaton: Automaton) -> None:
        if automaton.type is not AutomatonType.MOORE:
            raise WrongAutomatonTypeError(
                f"MooreSimulator requires a Moore machine, got {automaton.type.value!r}",
            )
        self._automaton = automaton
        self._table: dict[tuple[str, str], str] = {}
        for tr in automaton.transitions:
            assert isinstance(tr, MooreTransition)
            self._table[(tr.source, tr.read)] = tr.target
        self._state_output: dict[str, str] = {}
        for state in automaton.states:
            assert state.moore_output is not None  # guaranteed by validator
            self._state_output[state.id] = state.moore_output
        self._accepting: frozenset[str] = frozenset(automaton.accepting_states)
        self._alphabet: frozenset[str] = frozenset(automaton.alphabet)

        self._input: tuple[str, ...] = ()
        self._position: int = 0
        self._current: str | None = None
        self._output: list[str] = []
        self._history: list[MooreStep] = []
        self._verdict: Verdict | None = None

    # ---------------------------------------------------------------- introspection
    @property
    def automaton(self) -> Automaton:
        """The underlying Moore automaton (read-only)."""
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
        """Output emitted so far (initial state output + one per consumed symbol)."""
        return tuple(self._output)

    @property
    def history(self) -> tuple[MooreStep, ...]:
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
        """Place the simulator at the initial state; emit the initial state's output."""
        self._input = tuple(input_string)
        self._position = 0
        self._current = self._automaton.initial_state
        self._output = [self._state_output[self._current]]
        self._history = []
        self._verdict = None

    def step(self) -> MooreStep | None:
        """Consume one symbol; emit the new state's output.

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
        next_state = self._table[key]
        out_symbol = self._state_output[next_state]
        step = MooreStep(
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

    def run(self, input_string: Sequence[str]) -> MooreTrace:
        """Reset and execute the simulator to completion."""
        self.reset(input_string)
        while self.step() is not None:
            pass
        assert self._verdict is not None
        return MooreTrace(
            input=self._input,
            output=tuple(self._output),
            steps=tuple(self._history),
            final_state=self._current,
            verdict=self._verdict,
        )

    def accepts(self, input_string: Sequence[str]) -> bool:
        """Return ``True`` iff the Moore machine accepts ``input_string``."""
        return self.run(input_string).accepted

    def translate(self, input_string: Sequence[str]) -> tuple[str, ...]:
        """Return the full output sequence for ``input_string``."""
        return self.run(input_string).output

    # ---------------------------------------------------------------- internals
    def _accept_verdict(self) -> Verdict:
        if not self._accepting:
            return Verdict.ACCEPTED
        assert self._current is not None
        return (
            Verdict.ACCEPTED if self._current in self._accepting else Verdict.REJECTED_NON_ACCEPTING
        )
