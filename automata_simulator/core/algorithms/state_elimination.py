"""State-elimination: convert any FA (DFA/NFA/ε-NFA) into a regex.

Summary (UA): Перетворення FA на регулярний вираз методом поступового
усунення станів. Алгоритм стандартний (Hopcroft-Ullman §3.2): додаємо
віртуальні start/final стани, тримаємо ребра з мітками-регексами, в циклі
усуваємо по одному стану, замінюючи шляхи через нього на еквівалентний
regex зі зіркою для self-loop.
Summary (EN): Textbook state-elimination conversion from a finite automaton
(DFA, NFA, or ε-NFA) into an equivalent regex. Adds virtual start/final
states, keeps regex-labelled edges, iteratively eliminates inner states by
substituting paths through them with ``in · loop* · out``.
"""

from __future__ import annotations

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
)
from automata_simulator.core.regex import (
    EmptySet,
    Epsilon,
    Literal,
    RegexNode,
    concat,
    star,
    union,
)

_VIRTUAL_START: str = "__start__"
_VIRTUAL_END: str = "__end__"


def fa_to_regex(automaton: Automaton) -> RegexNode:
    """Return a regex equivalent to the language recognised by ``automaton``.

    Args:
        automaton: A DFA, NFA, or ε-NFA.

    Returns:
        A :data:`RegexNode` whose language matches ``automaton``'s.

    Raises:
        ValueError: If ``automaton`` is not a finite-automaton kind.
    """
    if automaton.type not in (
        AutomatonType.DFA,
        AutomatonType.NFA,
        AutomatonType.EPSILON_NFA,
    ):
        raise ValueError(
            f"fa_to_regex expects a DFA/NFA/ε-NFA, got {automaton.type.value!r}",
        )

    edges: dict[tuple[str, str], RegexNode] = {}

    def add_edge(src: str, tgt: str, label: RegexNode) -> None:
        key = (src, tgt)
        existing = edges.get(key)
        edges[key] = union(existing, label) if existing is not None else label

    # Copy existing transitions as labelled edges.
    for tr in automaton.transitions:
        assert isinstance(tr, FATransition)
        label: RegexNode = Epsilon() if tr.read == EPSILON else Literal(tr.read)
        add_edge(tr.source, tr.target, label)

    # Virtual start/end states.
    add_edge(_VIRTUAL_START, automaton.initial_state, Epsilon())
    for acc in automaton.accepting_states:
        add_edge(acc, _VIRTUAL_END, Epsilon())

    # Eliminate every real state, in id order for determinism.
    to_eliminate = sorted(s.id for s in automaton.states)
    for state_id in to_eliminate:
        loop = edges.get((state_id, state_id))
        loop_star = star(loop) if loop is not None else Epsilon()

        incoming: list[tuple[str, RegexNode]] = [
            (src, lbl) for (src, tgt), lbl in edges.items() if tgt == state_id and src != state_id
        ]
        outgoing: list[tuple[str, RegexNode]] = [
            (tgt, lbl) for (src, tgt), lbl in edges.items() if src == state_id and tgt != state_id
        ]
        for p, in_label in incoming:
            for q, out_label in outgoing:
                new_label = concat(concat(in_label, loop_star), out_label)
                add_edge(p, q, new_label)

        # Drop every edge touching this state.
        edges = {(src, tgt): lbl for (src, tgt), lbl in edges.items() if state_id not in (src, tgt)}

    return edges.get((_VIRTUAL_START, _VIRTUAL_END), EmptySet())
