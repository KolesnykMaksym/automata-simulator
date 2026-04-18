"""PDA normalisation to Sipser's normal form.

Summary (UA): Приводить PDA до форми, де: (a) один початковий і один прикінцевий
стан, (b) перед прийняттям стек порожній (залишається лише маркер), (c) кожен
перехід або виштовхує рівно один символ на стек, або знімає рівно один символ —
ніколи обидва, ніколи жодного. Це форма, що потрібна для класичної побудови
CFG (Sipser Th. 2.20).
Summary (EN): Normalises a PDA so that: (a) it has a unique start/accept
state, (b) the stack is cleared before accepting, and (c) every transition
either pushes exactly one symbol or pops exactly one symbol — never both,
never neither. This is the form the Sipser Theorem 2.20 CFG construction
expects.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    PDATransition,
    State,
    Transition,
)


def _fresh(base: str, taken: set[str]) -> str:
    candidate = base
    idx = 0
    while candidate in taken:
        candidate = f"{base}__{idx}"
        idx += 1
    taken.add(candidate)
    return candidate


def normalize_pda(pda: Automaton) -> Automaton:
    """Return a PDA with the same language that satisfies Sipser's normal form.

    The resulting PDA has:
        * Exactly one initial state and exactly one accepting state.
        * A dedicated stack bottom marker ``$``; the stack is emptied (down
          to ``$``) before reaching the accepting state.
        * Every transition is either "push-one" (``pop=ε``, ``|push|=1``) or
          "pop-one" (``pop=X``, ``push=()``). No transition both pushes and
          pops, and no transition leaves the stack unchanged.

    Args:
        pda: The input PDA.

    Returns:
        A normalised PDA accepting exactly ``L(pda)``.

    Raises:
        ValueError: If ``pda`` is not of type ``PDA``.
    """
    if pda.type is not AutomatonType.PDA:
        raise ValueError(f"normalize_pda expects a PDA, got {pda.type.value!r}")
    assert pda.stack_alphabet is not None
    assert pda.stack_start is not None

    taken_states: set[str] = {s.id for s in pda.states}
    taken_stack: set[str] = set(pda.stack_alphabet)

    marker = _fresh("$", taken_stack)
    null_op = _fresh("·", taken_stack)  # for replacing no-op transitions

    start_id = _fresh("q_start", taken_states)
    accept_id = _fresh("q_accept", taken_states)
    clear_id = _fresh("q_clear", taken_states)

    inter_counter = itertools.count()

    def inter_state() -> str:
        while True:
            candidate = f"q_inter_{next(inter_counter)}"
            if candidate not in taken_states:
                taken_states.add(candidate)
                return candidate

    transitions: list[Transition] = []
    extra_states: list[State] = []

    # 1. New start: push original Z onto $.
    #    We emit two push-only steps: push $ via pop-$ push-$ is impossible,
    #    so stack_start of the new PDA *is* $, then we push Z0 on top.
    transitions.append(
        PDATransition(
            source=start_id,
            target=pda.initial_state,
            read=EPSILON,
            pop=EPSILON,
            push=(pda.stack_start,),
        ),
    )

    # 2. Rewrite every original transition into normal-form pieces.
    for tr in pda.transitions:
        assert isinstance(tr, PDATransition)
        _normalize_transition(tr, transitions, inter_state, extra_states, null_op)

    # 3. Add clearing machinery: every original accepting state connects (via
    #    ε) to q_clear; q_clear pops everything above $; when $ is popped
    #    we move to the accept state (pushing $ right back so the stack
    #    remains valid under our model).
    for acc in pda.accepting_states:
        transitions.append(
            PDATransition(
                source=acc,
                target=clear_id,
                read=EPSILON,
                pop=EPSILON,
                push=(null_op,),
            ),
        )
        # Immediately cancel the push we just did so the stack is unchanged.
        # (That extra push ensures even this ε-move is push-only, not a no-op.)
        transitions.append(
            PDATransition(
                source=clear_id,
                target=clear_id,
                read=EPSILON,
                pop=null_op,
                push=(),
            ),
        )
    # Pop every pre-existing stack symbol from q_clear.
    stack_alphabet = [*pda.stack_alphabet, marker, null_op]
    for sym in pda.stack_alphabet:
        transitions.append(
            PDATransition(
                source=clear_id,
                target=clear_id,
                read=EPSILON,
                pop=sym,
                push=(),
            ),
        )
    # Finally pop $ to accept — the stack then conceptually becomes empty.
    # Our PDASimulator's acceptance criterion only checks state + input
    # consumption, so an empty stack is fine.
    transitions.append(
        PDATransition(
            source=clear_id,
            target=accept_id,
            read=EPSILON,
            pop=marker,
            push=(),
        ),
    )

    # 4. Assemble state list (preserving originals + new helpers).
    original_states: list[State] = [
        State(id=s.id, label=s.label, position=s.position) for s in pda.states
    ]
    new_states: list[State] = [
        State(id=start_id, is_initial=True),
        *original_states,
        *extra_states,
        State(id=clear_id),
        State(id=accept_id, is_accepting=True),
    ]

    return Automaton(
        type=AutomatonType.PDA,
        name=f"{pda.name}-normalized",
        states=new_states,
        alphabet=list(pda.alphabet),
        stack_alphabet=sorted(set(stack_alphabet)),
        stack_start=marker,
        initial_state=start_id,
        accepting_states=[accept_id],
        transitions=transitions,
    )


def _normalize_transition(
    tr: PDATransition,
    out: list[Transition],
    fresh_state: Callable[[], str],
    extra_states: list[State],
    null_op: str,
) -> None:
    """Split one original transition into Sipser-normal-form pieces."""
    read = tr.read
    pop = tr.pop
    push = tr.push
    src = tr.source
    tgt = tr.target

    # Handle stack-unchanged transitions via marker trick.
    if pop == EPSILON and not push:
        mid = fresh_state()
        extra_states.append(State(id=mid))
        # push null_op, then pop it — still two transitions, both legal.
        out.append(
            PDATransition(source=src, target=mid, read=read, pop=EPSILON, push=(null_op,)),
        )
        out.append(
            PDATransition(
                source=mid,
                target=tgt,
                read=EPSILON,
                pop=null_op,
                push=(),
            ),
        )
        return

    # Combined pop-and-push → pop first, then push the sequence.
    if pop != EPSILON and push:
        # Emit pop step first.
        after_pop = fresh_state()
        extra_states.append(State(id=after_pop))
        out.append(
            PDATransition(
                source=src,
                target=after_pop,
                read=read,
                pop=pop,
                push=(),
            ),
        )
        # Emit push chain from bottom of new sequence up to the top.
        _emit_push_chain(after_pop, tgt, push, out, fresh_state, extra_states)
        return

    # Pure push: possibly multi-symbol; unroll into a chain of single-push steps.
    if pop == EPSILON and push:
        if len(push) == 1:
            out.append(tr)  # already in normal form
            return
        _emit_push_chain(src, tgt, push, out, fresh_state, extra_states, first_read=read)
        return

    # Pure pop of exactly one symbol and no push → already in normal form.
    if pop != EPSILON and not push:
        out.append(tr)
        return


def _emit_push_chain(
    src: str,
    tgt: str,
    push: tuple[str, ...],
    out: list[Transition],
    fresh_state: Callable[[], str],
    extra_states: list[State],
    *,
    first_read: str = EPSILON,
) -> None:
    """Push symbols one at a time; first push lands furthest from the top.

    ``push`` stores the symbols top-first (our model's convention); to leave
    ``push[0]`` on top after all steps, push in reverse order.
    """
    stages = list(reversed(push))  # push stages[0] first, stages[-1] last (top)
    prev = src
    for i, sym in enumerate(stages):
        is_last = i == len(stages) - 1
        after = tgt if is_last else fresh_state()
        if not is_last:
            extra_states.append(State(id=after))
        out.append(
            PDATransition(
                source=prev,
                target=after,
                read=first_read if i == 0 else EPSILON,
                pop=EPSILON,
                push=(sym,),
            ),
        )
        prev = after
