"""Thompson's construction: regex AST → ε-NFA.

Summary (UA): Побудова ε-NFA за регулярним виразом (алгоритм Томпсона). Кожна
рекурсивна гілка повертає sub-NFA з рівно одним початковим та прикінцевим
станом; вони з'єднуються через ε-переходи.
Summary (EN): Builds an ε-NFA from a regex AST via Thompson's construction.
Every recursive call returns a sub-NFA with exactly one start and one accept
state, stitched together via ε-transitions.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from dataclasses import dataclass

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
    Transition,
)
from automata_simulator.core.regex import (
    Concat,
    EmptySet,
    Epsilon,
    Literal,
    RegexNode,
    Star,
    Union,
    literals_in,
)


@dataclass
class _Fragment:
    """An intermediate ε-NFA fragment with distinguished start/accept states."""

    start: str
    accept: str
    states: list[State]
    transitions: list[Transition]


def regex_to_nfa(
    node: RegexNode,
    alphabet: Iterable[str] | None = None,
    *,
    name: str = "regex-nfa",
) -> Automaton:
    """Build an ε-NFA whose language equals ``L(node)``.

    Args:
        node: The regex AST to compile.
        alphabet: Input alphabet. If ``None``, uses the set of literal
            characters that appear in ``node``. Passing an explicit alphabet is
            useful when a regex uses only a proper subset of the machine's Σ.
        name: Human-friendly name for the resulting automaton.

    Returns:
        An ``EPSILON_NFA`` with a single accepting state and a distinguished
        initial state.
    """
    counter = itertools.count()

    def fresh() -> str:
        return f"t{next(counter)}"

    def build(n: RegexNode) -> _Fragment:
        match n:
            case Epsilon():
                a, b = fresh(), fresh()
                return _Fragment(
                    start=a,
                    accept=b,
                    states=[State(id=a), State(id=b)],
                    transitions=[FATransition(source=a, target=b, read=EPSILON)],
                )
            case EmptySet():
                a, b = fresh(), fresh()
                # No transition between them → language is ∅.
                return _Fragment(
                    start=a,
                    accept=b,
                    states=[State(id=a), State(id=b)],
                    transitions=[],
                )
            case Literal(char):
                a, b = fresh(), fresh()
                return _Fragment(
                    start=a,
                    accept=b,
                    states=[State(id=a), State(id=b)],
                    transitions=[FATransition(source=a, target=b, read=char)],
                )
            case Concat(lhs, rhs):
                left = build(lhs)
                right = build(rhs)
                bridge: Transition = FATransition(
                    source=left.accept,
                    target=right.start,
                    read=EPSILON,
                )
                return _Fragment(
                    start=left.start,
                    accept=right.accept,
                    states=left.states + right.states,
                    transitions=[*left.transitions, *right.transitions, bridge],
                )
            case Union(lhs, rhs):
                new_start, new_end = fresh(), fresh()
                left = build(lhs)
                right = build(rhs)
                bridges: list[Transition] = [
                    FATransition(source=new_start, target=left.start, read=EPSILON),
                    FATransition(source=new_start, target=right.start, read=EPSILON),
                    FATransition(source=left.accept, target=new_end, read=EPSILON),
                    FATransition(source=right.accept, target=new_end, read=EPSILON),
                ]
                return _Fragment(
                    start=new_start,
                    accept=new_end,
                    states=[
                        State(id=new_start),
                        State(id=new_end),
                        *left.states,
                        *right.states,
                    ],
                    transitions=[*left.transitions, *right.transitions, *bridges],
                )
            case Star(inner):
                new_start, new_end = fresh(), fresh()
                sub = build(inner)
                bridges = [
                    FATransition(source=new_start, target=sub.start, read=EPSILON),
                    FATransition(source=new_start, target=new_end, read=EPSILON),
                    FATransition(source=sub.accept, target=sub.start, read=EPSILON),
                    FATransition(source=sub.accept, target=new_end, read=EPSILON),
                ]
                return _Fragment(
                    start=new_start,
                    accept=new_end,
                    states=[State(id=new_start), State(id=new_end), *sub.states],
                    transitions=[*sub.transitions, *bridges],
                )

    fragment = build(node)
    alphabet_list: list[str] = (
        sorted(alphabet) if alphabet is not None else sorted(literals_in(node))
    )

    # Re-build states with initial/accepting flags set.
    tagged_states: list[State] = []
    for s in fragment.states:
        tagged_states.append(
            State(
                id=s.id,
                is_initial=s.id == fragment.start,
                is_accepting=s.id == fragment.accept,
            ),
        )

    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        name=name,
        states=tagged_states,
        alphabet=alphabet_list,
        initial_state=fragment.start,
        accepting_states=[fragment.accept],
        transitions=fragment.transitions,
    )
