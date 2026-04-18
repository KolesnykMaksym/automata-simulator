"""Pushdown-automaton simulator (non-deterministic, final-state acceptance).

Summary (UA): Симулятор PDA з обходом у ширину по конфігураціях. Можуть
застосовуватись ε-переходи (read=ε, pop=ε). Trace — один прийнятний шлях.
Summary (EN): Breadth-first PDA simulator over ``(state, input_pos, stack)``
configurations, supporting ε on either ``read`` or ``pop``. Returns a single
accepting path in the trace (if one exists). Final-state acceptance.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    PDATransition,
)
from automata_simulator.core.simulators.base import (
    Verdict,
    WrongAutomatonTypeError,
)

DEFAULT_PDA_STEP_LIMIT: int = 10_000


@dataclass(frozen=True, slots=True)
class PDAConfig:
    """One configuration of the PDA: state, remaining-input offset, and stack.

    Stack is bottom-first: ``stack[-1]`` is the top symbol.
    """

    state: str
    input_pos: int
    stack: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PDAStep:
    """One transition between two PDA configurations."""

    index: int
    from_config: PDAConfig
    transition: PDATransition
    to_config: PDAConfig


@dataclass(frozen=True, slots=True)
class PDATrace:
    """Outcome of a PDA run. ``steps`` is populated only on acceptance."""

    input: tuple[str, ...]
    steps: tuple[PDAStep, ...]
    final_config: PDAConfig | None
    verdict: Verdict

    @property
    def accepted(self) -> bool:
        """Whether the input was accepted."""
        return self.verdict.is_accepted


class PDASimulator:
    """Non-deterministic PDA simulator with final-state acceptance.

    Uses BFS over a visited set of configurations to decide acceptance and to
    reconstruct one accepting path. The total number of configurations explored
    is capped at ``step_limit`` (default: 10 000) to guard against runaway
    ε-loops over unbounded stacks.
    """

    def __init__(
        self,
        automaton: Automaton,
        *,
        step_limit: int = DEFAULT_PDA_STEP_LIMIT,
    ) -> None:
        if automaton.type is not AutomatonType.PDA:
            raise WrongAutomatonTypeError(
                f"PDASimulator requires a PDA, got {automaton.type.value!r}",
            )
        if step_limit < 1:
            raise ValueError("step_limit must be ≥ 1")
        self._automaton = automaton
        assert automaton.stack_start is not None  # guaranteed by validator
        self._stack_start: str = automaton.stack_start
        self._accepting: frozenset[str] = frozenset(automaton.accepting_states)
        self._alphabet: frozenset[str] = frozenset(automaton.alphabet)
        # Index transitions by source state for fast lookup.
        self._by_source: dict[str, list[PDATransition]] = {}
        for tr in automaton.transitions:
            assert isinstance(tr, PDATransition)
            self._by_source.setdefault(tr.source, []).append(tr)
        self._step_limit: int = step_limit

    # ---------------------------------------------------------------- run / accepts
    @property
    def automaton(self) -> Automaton:
        """The underlying PDA (read-only)."""
        return self._automaton

    def run(self, input_string: Sequence[str]) -> PDATrace:
        """Execute the PDA on ``input_string`` and return its trace."""
        tape = tuple(input_string)
        for sym in tape:
            if sym not in self._alphabet:
                return PDATrace(
                    input=tape,
                    steps=(),
                    final_config=None,
                    verdict=Verdict.REJECTED_INVALID_SYMBOL,
                )

        initial = PDAConfig(
            state=self._automaton.initial_state,
            input_pos=0,
            stack=(self._stack_start,),
        )
        parents: dict[PDAConfig, tuple[PDAConfig, PDATransition] | None] = {initial: None}
        queue: deque[PDAConfig] = deque([initial])
        expansions = 0
        accepted: PDAConfig | None = None

        while queue and accepted is None:
            if expansions >= self._step_limit:
                return PDATrace(
                    input=tape,
                    steps=(),
                    final_config=None,
                    verdict=Verdict.REJECTED_TIMEOUT,
                )
            cfg = queue.popleft()
            expansions += 1
            if cfg.input_pos == len(tape) and cfg.state in self._accepting:
                accepted = cfg
                break
            for next_cfg, tr in self._successors(cfg, tape):
                if next_cfg not in parents:
                    parents[next_cfg] = (cfg, tr)
                    queue.append(next_cfg)

        if accepted is not None:
            path = self._reconstruct(accepted, parents)
            return PDATrace(
                input=tape,
                steps=path,
                final_config=accepted,
                verdict=Verdict.ACCEPTED,
            )
        return PDATrace(
            input=tape,
            steps=(),
            final_config=None,
            verdict=Verdict.REJECTED_NON_ACCEPTING,
        )

    def accepts(self, input_string: Sequence[str]) -> bool:
        """Return ``True`` iff the PDA accepts ``input_string``."""
        return self.run(input_string).accepted

    # ---------------------------------------------------------------- internals
    def _successors(
        self,
        cfg: PDAConfig,
        tape: tuple[str, ...],
    ) -> list[tuple[PDAConfig, PDATransition]]:
        out: list[tuple[PDAConfig, PDATransition]] = []
        stack = cfg.stack
        top = stack[-1] if stack else None
        for tr in self._by_source.get(cfg.state, ()):
            # read clause
            if tr.read == EPSILON:
                consume = 0
            elif cfg.input_pos < len(tape) and tape[cfg.input_pos] == tr.read:
                consume = 1
            else:
                continue
            # pop clause
            if tr.pop == EPSILON:
                remaining = stack
            elif top == tr.pop:
                remaining = stack[:-1]
            else:
                continue
            # push: push[0] lands on top, so append reversed.
            new_stack = remaining + tuple(reversed(tr.push))
            out.append(
                (
                    PDAConfig(
                        state=tr.target,
                        input_pos=cfg.input_pos + consume,
                        stack=new_stack,
                    ),
                    tr,
                ),
            )
        return out

    @staticmethod
    def _reconstruct(
        accepted: PDAConfig,
        parents: dict[PDAConfig, tuple[PDAConfig, PDATransition] | None],
    ) -> tuple[PDAStep, ...]:
        chain: list[tuple[PDAConfig, PDATransition, PDAConfig]] = []
        current = accepted
        while True:
            link = parents[current]
            if link is None:
                break
            prev, tr = link
            chain.append((prev, tr, current))
            current = prev
        chain.reverse()
        return tuple(
            PDAStep(index=i, from_config=a, transition=tr, to_config=b)
            for i, (a, tr, b) in enumerate(chain)
        )
