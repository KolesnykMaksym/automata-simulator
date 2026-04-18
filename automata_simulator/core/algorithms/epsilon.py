"""ε-closure and ε-transition removal.

Summary (UA): ε-замикання множини станів та перетворення ε-NFA на еквівалентний
NFA без ε-переходів.
Summary (EN): ε-closure of a set of states and the classical conversion of an
ε-NFA to an equivalent NFA (no ε-transitions).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
)


def epsilon_closure(automaton: Automaton, seeds: Iterable[str]) -> frozenset[str]:
    """Return the ε-closure of ``seeds`` in ``automaton``.

    Args:
        automaton: An NFA or ε-NFA (any FA-like automaton).
        seeds: Iterable of state ids to seed the closure with.

    Returns:
        The smallest set containing ``seeds`` and closed under ε-transitions.
    """
    result: set[str] = set(seeds)
    # Build ε-adjacency lazily on first use.
    eps_adj: dict[str, list[str]] = {}
    for tr in automaton.transitions:
        if isinstance(tr, FATransition) and tr.read == EPSILON:
            eps_adj.setdefault(tr.source, []).append(tr.target)
    stack: list[str] = list(result)
    while stack:
        src = stack.pop()
        for dst in eps_adj.get(src, ()):
            if dst not in result:
                result.add(dst)
                stack.append(dst)
    return frozenset(result)


@dataclass(frozen=True)
class EpsilonRemovalResult:
    """Result of :func:`remove_epsilon_transitions`.

    Attributes:
        nfa: The ε-free equivalent NFA.
        closure_by_state: ``{original_state_id: ε-closure}`` for visualisation.
    """

    nfa: Automaton
    closure_by_state: dict[str, frozenset[str]]


def remove_epsilon_transitions(enfa: Automaton) -> EpsilonRemovalResult:
    """Convert an ε-NFA to an equivalent NFA without ε-transitions.

    Args:
        enfa: Automaton with ``type == EPSILON_NFA`` (an NFA is also accepted
            and returned unchanged).

    Returns:
        The ε-free NFA plus a per-state ε-closure mapping.

    Raises:
        ValueError: If ``enfa.type`` is neither ``NFA`` nor ``EPSILON_NFA``.
    """
    if enfa.type not in (AutomatonType.NFA, AutomatonType.EPSILON_NFA):
        raise ValueError(
            f"remove_epsilon_transitions expects an NFA or ε-NFA, got {enfa.type.value!r}",
        )

    closures: dict[str, frozenset[str]] = {s.id: epsilon_closure(enfa, {s.id}) for s in enfa.states}

    accepting = frozenset(enfa.accepting_states)
    new_accepting: list[str] = [
        sid for sid in (s.id for s in enfa.states) if closures[sid] & accepting
    ]

    # For each (p, a) with a ∈ Σ: new targets = ε-closure(∪{δ(q, a) : q ∈ E(p)}).
    by_source_and_symbol: dict[tuple[str, str], set[str]] = {}
    for tr in enfa.transitions:
        assert isinstance(tr, FATransition)
        if tr.read == EPSILON:
            continue
        by_source_and_symbol.setdefault((tr.source, tr.read), set()).add(tr.target)

    new_transitions: list[FATransition] = []
    seen_pairs: set[tuple[str, str, str]] = set()
    for state in enfa.states:
        p = state.id
        for symbol in enfa.alphabet:
            raw: set[str] = set()
            for q in closures[p]:
                raw.update(by_source_and_symbol.get((q, symbol), ()))
            if not raw:
                continue
            closed = epsilon_closure(enfa, raw)
            for t in sorted(closed):
                key = (p, symbol, t)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                new_transitions.append(FATransition(source=p, target=t, read=symbol))

    # Preserve state flags except is_initial / is_accepting (we recompute the latter).
    new_states: list[State] = []
    for s in enfa.states:
        new_states.append(
            State(
                id=s.id,
                label=s.label,
                is_initial=s.id == enfa.initial_state,
                is_accepting=s.id in new_accepting,
                moore_output=s.moore_output,
                position=s.position,
            ),
        )

    new_nfa = Automaton(
        type=AutomatonType.NFA,
        name=f"{enfa.name}-eps-removed",
        states=new_states,
        alphabet=list(enfa.alphabet),
        initial_state=enfa.initial_state,
        accepting_states=new_accepting,
        transitions=list(new_transitions),
    )
    return EpsilonRemovalResult(nfa=new_nfa, closure_by_state=closures)
