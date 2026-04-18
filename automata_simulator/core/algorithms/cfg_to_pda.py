"""CFG → PDA conversion.

Summary (UA): Побудова PDA за CFG. Використовується канонічна 3-станова схема:
стек-bottom marker $, завантаження стартового символа, основний стан з
ε-переходами для продукцій та символ-матч переходами для терміналів, окремий
прикінцевий стан.
Summary (EN): Canonical 3-state CFG→PDA construction: a bottom-of-stack
marker $, a load state that pushes the start symbol, a main state whose
ε-transitions expand productions (``A → body`` becomes a pop-A push-body
step) and whose consuming transitions match each terminal, plus a dedicated
final state reached by popping the marker.
"""

from __future__ import annotations

from automata_simulator.core.cfg import CFG
from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    PDATransition,
    State,
    Transition,
)


def _fresh_marker(cfg: CFG) -> str:
    candidate = "$"
    symbols = set(cfg.nonterminals) | set(cfg.terminals)
    while candidate in symbols:
        candidate += "$"
    return candidate


def _fresh_state(taken: set[str], base: str) -> str:
    if base not in taken:
        taken.add(base)
        return base
    idx = 0
    while True:
        candidate = f"{base}_{idx}"
        if candidate not in taken:
            taken.add(candidate)
            return candidate
        idx += 1


def cfg_to_pda(cfg: CFG) -> Automaton:
    """Convert a CFG into an equivalent PDA (final-state acceptance).

    The resulting PDA accepts exactly ``L(cfg)`` — a string is accepted iff
    the PDA can fully consume it and reach the accept state with only the
    bottom marker on the stack.

    Args:
        cfg: The context-free grammar to compile.

    Returns:
        An automaton of type ``PDA``.
    """
    marker = _fresh_marker(cfg)
    taken: set[str] = set()
    q_load = _fresh_state(taken, "q_load")
    q_main = _fresh_state(taken, "q")
    q_accept = _fresh_state(taken, "q_accept")

    states: list[State] = [
        State(id=q_load, is_initial=True),
        State(id=q_main),
        State(id=q_accept, is_accepting=True),
    ]

    # Stack alphabet: marker, every nonterminal (for expansion), every terminal
    # (so consumed symbols can be popped).
    stack_alphabet: list[str] = [marker, *cfg.nonterminals, *cfg.terminals]

    transitions: list[Transition] = []

    # Load start symbol onto the bottom marker.
    transitions.append(
        PDATransition(
            source=q_load,
            target=q_main,
            read=EPSILON,
            pop=marker,
            push=(cfg.start, marker),
        ),
    )

    # Terminal matches: pop terminal when consumed.
    for term in cfg.terminals:
        transitions.append(
            PDATransition(
                source=q_main,
                target=q_main,
                read=term,
                pop=term,
                push=(),
            ),
        )

    # Production expansions: pop head, push body (top-first == body order).
    for prod in cfg.productions:
        transitions.append(
            PDATransition(
                source=q_main,
                target=q_main,
                read=EPSILON,
                pop=prod.head,
                push=tuple(prod.body),
            ),
        )

    # Accept: pop bottom marker, re-push it, move to accept state.
    transitions.append(
        PDATransition(
            source=q_main,
            target=q_accept,
            read=EPSILON,
            pop=marker,
            push=(marker,),
        ),
    )

    return Automaton(
        type=AutomatonType.PDA,
        name=f"{cfg.name}-pda",
        states=states,
        alphabet=list(cfg.terminals),
        stack_alphabet=stack_alphabet,
        stack_start=marker,
        initial_state=q_load,
        accepting_states=[q_accept],
        transitions=transitions,
    )
