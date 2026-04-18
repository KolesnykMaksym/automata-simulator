"""Deterministic multi-tape Turing-machine simulator.

Summary (UA): Детермінований симулятор ТМ з підтримкою k-стрічок. Стрічка
автоматично розширюється blank-символами ліворуч/праворуч; обмеження
``step_limit`` захищає від нескінченних циклів.
Summary (EN): Deterministic multi-tape Turing-machine simulator. Tapes are
auto-extended with the blank symbol in both directions. Halts on entering an
accepting state (accept), on a missing transition (reject), or after
``step_limit`` steps (timeout).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    TapeMove,
    TMTransition,
)
from automata_simulator.core.simulators.base import (
    SimulatorNotReadyError,
    Verdict,
    WrongAutomatonTypeError,
)

DEFAULT_TM_STEP_LIMIT: int = 100_000


@dataclass(frozen=True, slots=True)
class TMConfig:
    """A snapshot of the TM state."""

    state: str
    tapes: tuple[tuple[str, ...], ...]
    heads: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class TMStep:
    """One step of a TM simulation."""

    index: int
    from_config: TMConfig
    transition: TMTransition
    to_config: TMConfig


@dataclass(frozen=True, slots=True)
class TMTrace:
    """Complete record of a TM run."""

    input: tuple[str, ...]
    steps: tuple[TMStep, ...]
    final_config: TMConfig | None
    verdict: Verdict

    @property
    def accepted(self) -> bool:
        """Whether the input was accepted."""
        return self.verdict.is_accepted


class _MutableTape:
    """Growable 1-D tape with auto-extension on both ends."""

    __slots__ = ("_blank", "_cells", "_head")

    def __init__(self, initial: Sequence[str], blank: str) -> None:
        self._cells: list[str] = list(initial)
        self._blank: str = blank
        self._head: int = 0
        if not self._cells:
            self._cells.append(blank)

    @property
    def head(self) -> int:
        """Current head position (0-indexed into ``cells``)."""
        return self._head

    def read(self) -> str:
        """Read the symbol currently under the head."""
        return self._cells[self._head]

    def write(self, symbol: str) -> None:
        """Overwrite the cell under the head."""
        self._cells[self._head] = symbol

    def move(self, direction: TapeMove) -> None:
        """Move the head; auto-extend with blanks if we fall off either edge."""
        if direction is TapeMove.LEFT:
            self._head -= 1
            if self._head < 0:
                self._cells.insert(0, self._blank)
                self._head = 0
        elif direction is TapeMove.RIGHT:
            self._head += 1
            if self._head >= len(self._cells):
                self._cells.append(self._blank)
        # STAY: no action

    def snapshot(self) -> tuple[tuple[str, ...], int]:
        """Return an immutable snapshot ``(cells, head_pos)``."""
        return tuple(self._cells), self._head


class TMSimulator:
    """Deterministic multi-tape Turing-machine simulator."""

    def __init__(
        self,
        automaton: Automaton,
        *,
        step_limit: int = DEFAULT_TM_STEP_LIMIT,
    ) -> None:
        if automaton.type is not AutomatonType.TM:
            raise WrongAutomatonTypeError(
                f"TMSimulator requires a TM, got {automaton.type.value!r}",
            )
        if step_limit < 1:
            raise ValueError("step_limit must be ≥ 1")
        self._automaton = automaton
        assert automaton.tape_alphabet is not None  # guaranteed by validator
        self._blank: str = automaton.blank_symbol
        self._tape_count: int = automaton.tape_count
        self._accepting: frozenset[str] = frozenset(automaton.accepting_states)
        self._input_alphabet: frozenset[str] = frozenset(automaton.alphabet)
        self._tape_alphabet: frozenset[str] = frozenset(automaton.tape_alphabet)
        self._step_limit: int = step_limit
        self._table: dict[tuple[str, tuple[str, ...]], TMTransition] = {}
        for tr in automaton.transitions:
            assert isinstance(tr, TMTransition)
            key = (tr.source, tuple(tr.read))
            # Determinism is enforced by the model validator for DFA but not
            # strictly for TM; guard against accidental non-determinism here.
            if key in self._table:
                raise ValueError(
                    f"TM is non-deterministic: state {tr.source!r} has multiple "
                    f"transitions reading {tr.read!r}",
                )
            self._table[key] = tr

        self._tapes: list[_MutableTape] = []
        self._current: str | None = None
        self._input: tuple[str, ...] = ()
        self._history: list[TMStep] = []
        self._verdict: Verdict | None = None
        self._step_count: int = 0

    # ---------------------------------------------------------------- introspection
    @property
    def automaton(self) -> Automaton:
        """The underlying TM (read-only)."""
        return self._automaton

    @property
    def current_state(self) -> str | None:
        """Current TM state, or ``None`` before the first :meth:`reset`."""
        return self._current

    @property
    def history(self) -> tuple[TMStep, ...]:
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

    def snapshot(self) -> TMConfig:
        """Return an immutable snapshot of the current configuration."""
        if self._current is None:
            raise SimulatorNotReadyError("call reset(input) before snapshot()")
        tapes: list[tuple[str, ...]] = []
        heads: list[int] = []
        for tape in self._tapes:
            cells, head = tape.snapshot()
            tapes.append(cells)
            heads.append(head)
        return TMConfig(state=self._current, tapes=tuple(tapes), heads=tuple(heads))

    # ---------------------------------------------------------------- control
    def reset(self, input_string: Sequence[str]) -> None:
        """Load ``input_string`` onto tape 0 and position all heads at 0."""
        tape = tuple(input_string)
        for sym in tape:
            if sym not in self._input_alphabet:
                # Still allow reset; acceptance check will surface the issue.
                # (Strict input-alphabet enforcement happens in run() below.)
                pass
        self._input = tape
        self._tapes = [
            _MutableTape(tape if i == 0 else (), self._blank) for i in range(self._tape_count)
        ]
        self._current = self._automaton.initial_state
        self._history = []
        self._verdict = None
        self._step_count = 0
        # If the TM immediately lands in an accepting state, halt at once.
        if self._current in self._accepting:
            self._verdict = Verdict.ACCEPTED

    def step(self) -> TMStep | None:
        """Advance the TM by one transition.

        Returns:
            The step taken, or ``None`` if the run has halted.

        Raises:
            SimulatorNotReadyError: If :meth:`reset` has not been called yet.
        """
        if self._current is None:
            raise SimulatorNotReadyError("call reset(input) before step()")
        if self._verdict is not None:
            return None
        if self._step_count >= self._step_limit:
            self._verdict = Verdict.REJECTED_TIMEOUT
            return None

        read_tuple: tuple[str, ...] = tuple(t.read() for t in self._tapes)
        # Guard against writes outside the tape alphabet leaking into reads.
        for sym in read_tuple:
            if sym not in self._tape_alphabet:
                self._verdict = Verdict.REJECTED_INVALID_SYMBOL
                return None

        key = (self._current, read_tuple)
        tr = self._table.get(key)
        if tr is None:
            self._verdict = Verdict.REJECTED_STUCK
            return None

        from_config = self.snapshot()
        for i, tape in enumerate(self._tapes):
            tape.write(tr.write[i])
            tape.move(tr.move[i])
        self._current = tr.target
        self._step_count += 1
        to_config = self.snapshot()

        step = TMStep(
            index=len(self._history),
            from_config=from_config,
            transition=tr,
            to_config=to_config,
        )
        self._history.append(step)

        if self._current in self._accepting:
            self._verdict = Verdict.ACCEPTED
        return step

    def run(self, input_string: Sequence[str]) -> TMTrace:
        """Reset and execute the TM to completion."""
        self.reset(input_string)
        while self.step() is not None:
            pass
        assert self._verdict is not None
        final = self.snapshot() if self._current is not None else None
        return TMTrace(
            input=self._input,
            steps=tuple(self._history),
            final_config=final,
            verdict=self._verdict,
        )

    def accepts(self, input_string: Sequence[str]) -> bool:
        """Return ``True`` iff the TM accepts ``input_string``."""
        return self.run(input_string).accepted
