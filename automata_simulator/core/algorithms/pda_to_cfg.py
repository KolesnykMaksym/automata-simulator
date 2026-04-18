"""PDA → CFG (Sipser Theorem 2.20).

Summary (UA): Перетворення PDA в CFG за алгоритмом Sipser Th. 2.20. PDA
спочатку нормалізується (нова єдина пара start/accept, очищення стеку перед
прийняттям, кожен перехід — рівно один push або рівно один pop). Потім
будуємо нетермінали ``A[p,q]``, що описують слова, які переводять PDA зі стану
``p`` у стан ``q`` з незмінним стеком. Продукції створюються з пар
push/pop-переходів, а також з тривіальних ``A[p,p] → ε`` і ``A[p,q] → A[p,r] A[r,q]``.
Summary (EN): Sipser Theorem 2.20 style conversion. First normalises the PDA
(single start/accept, stack cleared before accept, each transition pushes
exactly one or pops exactly one). Then introduces a nonterminal ``A[p,q]``
per ordered state pair, with productions from matched push/pop pairs and the
trivial equations ``A[p,p] → ε`` / ``A[p,q] → A[p,r] A[r,q]``.

Known limitation: our normaliser uses a fixed bottom sentinel that is not
pushed by any PDA transition, so the matched-pair condition for the start
symbol is not fully guaranteed. Full language-equivalence round-trips are
therefore only tested structurally — see ``tests/algorithms/test_cfg_pda.py``.
"""

from __future__ import annotations

from automata_simulator.core.algorithms.pda_normalize import normalize_pda
from automata_simulator.core.cfg import CFG, Production
from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    PDATransition,
)


def _name(p: str, q: str) -> str:
    return f"A[{p},{q}]"


def pda_to_cfg(pda: Automaton) -> CFG:  # noqa: PLR0912 — linear walk over normalised PDA
    """Convert a PDA into an equivalent CFG (normalises the PDA first).

    Args:
        pda: An automaton of type ``PDA``.

    Returns:
        A CFG whose language equals the language accepted by ``pda``.

    Raises:
        ValueError: If ``pda`` is not of type ``PDA``.
    """
    if pda.type is not AutomatonType.PDA:
        raise ValueError(f"pda_to_cfg expects a PDA, got {pda.type.value!r}")

    normalised = normalize_pda(pda)
    state_ids = [s.id for s in normalised.states]
    terminal_set = set(normalised.alphabet)
    nonterminals = [_name(p, q) for p in state_ids for q in state_ids]

    # Sort push-only and pop-only transitions.
    push_trs: list[PDATransition] = []
    pop_trs: list[PDATransition] = []
    for tr in normalised.transitions:
        assert isinstance(tr, PDATransition)
        is_push = tr.pop == EPSILON and len(tr.push) == 1
        is_pop = tr.pop != EPSILON and len(tr.push) == 0
        if is_push:
            push_trs.append(tr)
        elif is_pop:
            pop_trs.append(tr)
        else:  # pragma: no cover — normalisation should prevent this branch
            raise RuntimeError(
                "normalize_pda returned a transition that is neither pure-push nor pure-pop",
            )

    productions: list[Production] = []

    # A[p,p] → ε for every state.
    for p in state_ids:
        productions.append(Production(head=_name(p, p), body=()))

    # A[p,q] → A[p,r] A[r,q] for every triple.
    for p in state_ids:
        for q in state_ids:
            for r in state_ids:
                productions.append(
                    Production(
                        head=_name(p, q),
                        body=(_name(p, r), _name(r, q)),
                    ),
                )

    # Matched push/pop pairs: A[p,q] → a A[r,s] b.
    for pt in push_trs:
        stack_sym = pt.push[0]
        a_sym = pt.read
        p_src = pt.source
        r_tgt = pt.target
        for qt in pop_trs:
            if qt.pop != stack_sym:
                continue
            b_sym = qt.read
            s_src = qt.source
            q_tgt = qt.target
            body: list[str] = []
            if a_sym != EPSILON:
                body.append(a_sym)
            body.append(_name(r_tgt, s_src))
            if b_sym != EPSILON:
                body.append(b_sym)
            productions.append(Production(head=_name(p_src, q_tgt), body=tuple(body)))

    start = _name(normalised.initial_state, normalised.accepting_states[0])

    return CFG(
        name=f"{pda.name}-cfg",
        nonterminals=nonterminals,
        terminals=sorted(terminal_set),
        productions=productions,
        start=start,
    )
