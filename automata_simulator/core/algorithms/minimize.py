"""DFA minimisation via Hopcroft's partition-refinement algorithm.

Summary (UA): Мінімізація DFA алгоритмом Хопкрофта (O(n log n)). Включає
видалення недосяжних станів і доповнення часткового DFA trap-станом перед
роздiленням на класи еквівалентності.
Summary (EN): Hopcroft's O(n log n) minimisation. Removes unreachable states,
completes the partial DFA with a trap state, partitions by equivalence, and
rebuilds the DFA from the partition.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    FATransition,
    State,
    Transition,
)


@dataclass(frozen=True)
class MinimizationResult:
    """Result of :func:`minimize_dfa`.

    Attributes:
        dfa: The minimised DFA.
        equivalence_classes: ``{new_state_id: set of original state ids}``.
    """

    dfa: Automaton
    equivalence_classes: dict[str, frozenset[str]]


# -------------------------------------------------------------------------- helpers
def remove_unreachable_states(dfa: Automaton) -> Automaton:
    """Drop any DFA state that is unreachable from the initial state."""
    if dfa.type is not AutomatonType.DFA:
        raise ValueError(f"remove_unreachable_states expects a DFA, got {dfa.type.value!r}")
    reachable: set[str] = {dfa.initial_state}
    queue: deque[str] = deque([dfa.initial_state])
    by_source: dict[str, list[FATransition]] = {}
    for tr in dfa.transitions:
        assert isinstance(tr, FATransition)
        by_source.setdefault(tr.source, []).append(tr)
    while queue:
        src = queue.popleft()
        for tr in by_source.get(src, ()):
            if tr.target not in reachable:
                reachable.add(tr.target)
                queue.append(tr.target)
    return Automaton(
        type=AutomatonType.DFA,
        name=dfa.name,
        states=[s for s in dfa.states if s.id in reachable],
        alphabet=list(dfa.alphabet),
        initial_state=dfa.initial_state,
        accepting_states=[a for a in dfa.accepting_states if a in reachable],
        transitions=[
            tr for tr in dfa.transitions if tr.source in reachable and tr.target in reachable
        ],
    )


def _totalize(dfa: Automaton) -> tuple[Automaton, str | None]:
    """Add a trap state so every ``(state, symbol)`` has a defined transition.

    Returns ``(totalized_dfa, trap_id)`` where ``trap_id`` is ``None`` if the
    input was already total (no trap added).
    """
    existing: dict[tuple[str, str], str] = {}
    for tr in dfa.transitions:
        assert isinstance(tr, FATransition)
        existing[(tr.source, tr.read)] = tr.target

    missing: list[tuple[str, str]] = []
    for state in dfa.states:
        for symbol in dfa.alphabet:
            if (state.id, symbol) not in existing:
                missing.append((state.id, symbol))
    if not missing:
        return dfa, None

    taken = {s.id for s in dfa.states}
    trap_id = "__trap__"
    while trap_id in taken:
        trap_id += "_"

    new_states = [*dfa.states, State(id=trap_id)]
    new_transitions: list[Transition] = list(dfa.transitions)
    for src, sym in missing:
        new_transitions.append(FATransition(source=src, target=trap_id, read=sym))
    for sym in dfa.alphabet:
        new_transitions.append(FATransition(source=trap_id, target=trap_id, read=sym))

    return (
        Automaton(
            type=AutomatonType.DFA,
            name=dfa.name,
            states=new_states,
            alphabet=list(dfa.alphabet),
            initial_state=dfa.initial_state,
            accepting_states=list(dfa.accepting_states),
            transitions=new_transitions,
        ),
        trap_id,
    )


# -------------------------------------------------------------------------- core
def _hopcroft_partition(dfa: Automaton) -> list[frozenset[str]]:
    """Return the list of equivalence classes for a *total* DFA."""
    trans: dict[tuple[str, str], str] = {}
    for tr in dfa.transitions:
        assert isinstance(tr, FATransition)
        trans[(tr.source, tr.read)] = tr.target
    all_states = frozenset(s.id for s in dfa.states)
    accepting = frozenset(dfa.accepting_states)
    non_accepting = all_states - accepting

    partitions: list[frozenset[str]] = [p for p in (accepting, non_accepting) if p]
    # Worklist: use the smaller of the two seeds for optimality.
    worklist: list[frozenset[str]] = [min(partitions, key=len)]

    while worklist:
        splitter = worklist.pop()
        for symbol in dfa.alphabet:
            preimage: frozenset[str] = frozenset(
                q for q in all_states if trans.get((q, symbol)) in splitter
            )
            if not preimage:
                continue
            new_partitions: list[frozenset[str]] = []
            for block in partitions:
                inter = block & preimage
                diff = block - preimage
                if inter and diff:
                    new_partitions.extend((inter, diff))
                    if block in worklist:
                        worklist.remove(block)
                        worklist.extend((inter, diff))
                    else:
                        worklist.append(min(inter, diff, key=len))
                else:
                    new_partitions.append(block)
            partitions = new_partitions
    return partitions


def _build_from_partition(
    totalized: Automaton,
    partition: list[frozenset[str]],
    trap_id: str | None,
    original_name: str,
) -> MinimizationResult:
    part_of: dict[str, int] = {}
    for i, block in enumerate(partition):
        for sid in block:
            part_of[sid] = i

    # Drop the block that contains the trap state (if any).
    trap_block = part_of.get(trap_id) if trap_id is not None else None

    def label(block: frozenset[str]) -> str:
        # Strip trap id from the label for clarity.
        cleaned = sorted(s for s in block if s != trap_id)
        return "[" + ",".join(cleaned) + "]" if cleaned else "[trap]"

    labels: dict[int, str] = {i: label(b) for i, b in enumerate(partition)}

    trans: dict[tuple[str, str], str] = {}
    for tr in totalized.transitions:
        assert isinstance(tr, FATransition)
        trans[(tr.source, tr.read)] = tr.target

    accepting_original = frozenset(totalized.accepting_states)

    new_states: list[State] = []
    new_transitions: list[Transition] = []
    new_accepting: list[str] = []
    initial_label: str | None = None
    equivalence: dict[str, frozenset[str]] = {}

    for i, block in enumerate(partition):
        if i == trap_block:
            continue
        name = labels[i]
        is_initial = totalized.initial_state in block
        is_accepting = bool(block & accepting_original)
        new_states.append(
            State(id=name, is_initial=is_initial, is_accepting=is_accepting),
        )
        equivalence[name] = frozenset(s for s in block if s != trap_id)
        if is_accepting:
            new_accepting.append(name)
        if is_initial:
            initial_label = name
        rep = next(iter(block))
        for symbol in totalized.alphabet:
            tgt = trans.get((rep, symbol))
            if tgt is None:
                continue
            tgt_block = part_of[tgt]
            if tgt_block == trap_block:
                continue  # drop transitions into the trap
            new_transitions.append(
                FATransition(source=name, target=labels[tgt_block], read=symbol),
            )

    assert initial_label is not None
    dfa = Automaton(
        type=AutomatonType.DFA,
        name=f"{original_name}-min",
        states=new_states,
        alphabet=list(totalized.alphabet),
        initial_state=initial_label,
        accepting_states=new_accepting,
        transitions=new_transitions,
    )
    return MinimizationResult(dfa=dfa, equivalence_classes=equivalence)


# -------------------------------------------------------------------------- public
def minimize_dfa(dfa: Automaton) -> MinimizationResult:
    """Minimise ``dfa`` using Hopcroft's algorithm.

    Steps: remove unreachable states → totalise with a trap state →
    Hopcroft partition refinement → rebuild DFA (dropping the trap block).

    Args:
        dfa: Automaton with ``type == DFA``.

    Returns:
        The minimised DFA together with the equivalence-class mapping.

    Raises:
        ValueError: If ``dfa`` is not a DFA or has no accepting states *and*
            also has no reachable non-accepting states (i.e. the language is
            empty — the minimised form is then a single unreachable trap).
    """
    if dfa.type is not AutomatonType.DFA:
        raise ValueError(f"minimize_dfa expects a DFA, got {dfa.type.value!r}")
    original_name = dfa.name
    trimmed = remove_unreachable_states(dfa)
    if not trimmed.accepting_states:
        # Empty language — canonical form is a 1-state DFA with no acceptance.
        dead = State(id="[dead]")
        dead_loops: list[Transition] = [
            FATransition(source="[dead]", target="[dead]", read=sym) for sym in trimmed.alphabet
        ]
        empty_dfa = Automaton(
            type=AutomatonType.DFA,
            name=f"{original_name}-min",
            states=[dead],
            alphabet=list(trimmed.alphabet),
            initial_state="[dead]",
            accepting_states=[],
            transitions=dead_loops,
        )
        return MinimizationResult(
            dfa=empty_dfa,
            equivalence_classes={
                "[dead]": frozenset(s.id for s in trimmed.states),
            },
        )
    totalized, trap_id = _totalize(trimmed)
    partition = _hopcroft_partition(totalized)
    return _build_from_partition(totalized, partition, trap_id, original_name)
