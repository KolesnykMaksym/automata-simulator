"""NFA → DFA subset construction (Rabin-Scott).

Summary (UA): Класична конверсія NFA/ε-NFA у DFA через підмножини станів.
Summary (EN): Rabin-Scott powerset construction converting an NFA (or ε-NFA)
into an equivalent DFA, with a side-mapping ``DFA state → NFA subset`` for
visualisation.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from automata_simulator.core.algorithms.epsilon import epsilon_closure
from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    FATransition,
    State,
    Transition,
)


@dataclass(frozen=True)
class SubsetConstructionResult:
    """Result of :func:`nfa_to_dfa`.

    Attributes:
        dfa: The constructed DFA.
        subset_by_state: ``{dfa_state_id: subset of NFA state ids}``.
    """

    dfa: Automaton
    subset_by_state: dict[str, frozenset[str]]


def _subset_name(subset: frozenset[str]) -> str:
    if not subset:
        return "{}"
    return "{" + ",".join(sorted(subset)) + "}"


def nfa_to_dfa(nfa: Automaton) -> SubsetConstructionResult:
    """Convert an NFA or ε-NFA to an equivalent DFA.

    The resulting DFA is partial — subsets with no outgoing transition on a
    given symbol simply have no corresponding DFA transition (instead of a
    trap state). This preserves the DFA-model's partial-function convention.

    Args:
        nfa: Automaton of type NFA or EPSILON_NFA.

    Returns:
        The constructed DFA and a mapping from DFA state ids to the
        NFA subsets they represent.

    Raises:
        ValueError: If ``nfa.type`` is not NFA or EPSILON_NFA.
    """
    if nfa.type not in (AutomatonType.NFA, AutomatonType.EPSILON_NFA):
        raise ValueError(
            f"nfa_to_dfa expects an NFA or ε-NFA, got {nfa.type.value!r}",
        )

    nfa_accepting = frozenset(nfa.accepting_states)
    alphabet = list(nfa.alphabet)

    by_source_and_symbol: dict[tuple[str, str], set[str]] = {}
    for tr in nfa.transitions:
        assert isinstance(tr, FATransition)
        by_source_and_symbol.setdefault((tr.source, tr.read), set()).add(tr.target)

    initial_subset = epsilon_closure(nfa, {nfa.initial_state})
    subset_by_state: dict[str, frozenset[str]] = {}
    state_by_subset: dict[frozenset[str], str] = {}

    def name_of(subset: frozenset[str]) -> str:
        if subset not in state_by_subset:
            name = _subset_name(subset)
            state_by_subset[subset] = name
            subset_by_state[name] = subset
        return state_by_subset[subset]

    initial_name = name_of(initial_subset)

    states: list[State] = []
    transitions: list[Transition] = []
    accepting_state_ids: list[str] = []

    queue: deque[frozenset[str]] = deque([initial_subset])
    processed: set[frozenset[str]] = set()

    while queue:
        subset = queue.popleft()
        if subset in processed:
            continue
        processed.add(subset)
        name = name_of(subset)
        is_initial = subset == initial_subset
        is_accepting = bool(subset & nfa_accepting)
        states.append(
            State(id=name, is_initial=is_initial, is_accepting=is_accepting),
        )
        if is_accepting:
            accepting_state_ids.append(name)
        for symbol in alphabet:
            raw: set[str] = set()
            for src in subset:
                raw.update(by_source_and_symbol.get((src, symbol), ()))
            if not raw:
                continue  # partial DFA — no transition
            closed = epsilon_closure(nfa, raw)
            target_name = name_of(closed)
            transitions.append(
                FATransition(source=name, target=target_name, read=symbol),
            )
            if closed not in processed:
                queue.append(closed)

    dfa = Automaton(
        type=AutomatonType.DFA,
        name=f"{nfa.name}-dfa",
        states=states,
        alphabet=alphabet,
        initial_state=initial_name,
        accepting_states=accepting_state_ids,
        transitions=transitions,
    )
    return SubsetConstructionResult(dfa=dfa, subset_by_state=subset_by_state)
