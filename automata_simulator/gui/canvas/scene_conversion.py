"""Convert an :class:`AutomatonScene` into a core :class:`Automaton` model.

Summary (UA): Побудова ``Automaton`` (DFA / NFA / ε-NFA) за станом сцени.
Тип автомата визначається автоматично: ``ε`` у міток → ε-NFA, недетермінізм
→ NFA, інакше DFA.
Summary (EN): Builds an ``Automaton`` (DFA / NFA / ε-NFA) from the editor
scene. The type is auto-classified from the transition labels: any ε label
implies ε-NFA; otherwise the presence of two transitions with the same
``(state, symbol)`` pair implies NFA; else DFA.
"""

from __future__ import annotations

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    Position,
    State,
    Transition,
)
from automata_simulator.gui.canvas.scene import AutomatonScene

_GRID_SPACING: float = 140.0


class SceneConversionError(ValueError):
    """Raised when the scene can't be lowered to a valid automaton."""


def scene_to_automaton(  # noqa: PLR0912 — single-pass scene walker is clearest
    scene: AutomatonScene,
    *,
    name: str = "scene",
) -> Automaton:
    """Lower ``scene`` into a core :class:`Automaton` model.

    Args:
        scene: The editor scene.
        name: Name to attach to the produced automaton.

    Returns:
        A DFA / NFA / ε-NFA (only FA kinds are supported at Stage 11).

    Raises:
        SceneConversionError: If the scene has no states, no initial state,
            or contains empty transition labels.
    """
    state_items = scene.state_items()
    if not state_items:
        raise SceneConversionError("Scene has no states")

    initial_items = [s for s in state_items if s.is_initial]
    if not initial_items:
        raise SceneConversionError("Scene has no initial state (mark one)")
    if len(initial_items) > 1:
        raise SceneConversionError(
            f"Scene has {len(initial_items)} initial states; exactly one is required",
        )

    states: list[State] = []
    for item in state_items:
        pos = item.scenePos()
        states.append(
            State(
                id=item.state_id,
                label=None if item.label == item.state_id else item.label,
                is_initial=item.is_initial,
                is_accepting=item.is_accepting,
                position=Position(x=pos.x(), y=pos.y()),
            ),
        )

    alphabet_set: set[str] = set()
    transitions: list[Transition] = []
    has_epsilon = False
    seen_pairs: set[tuple[str, str]] = set()
    is_nondeterministic = False

    for tr_item in scene.transition_items():
        label = tr_item.label.strip()
        if label == "":
            raise SceneConversionError(
                f"Transition {tr_item.source.state_id} → {tr_item.target.state_id} "
                "has an empty label",
            )
        if label in (EPSILON, "eps", "epsilon"):
            read = EPSILON
            has_epsilon = True
        else:
            read = label
            alphabet_set.add(read)
        pair = (tr_item.source.state_id, read)
        if pair in seen_pairs:
            is_nondeterministic = True
        else:
            seen_pairs.add(pair)
        transitions.append(
            FATransition(
                source=tr_item.source.state_id,
                target=tr_item.target.state_id,
                read=read,
            ),
        )

    if has_epsilon:
        automaton_type = AutomatonType.EPSILON_NFA
    elif is_nondeterministic:
        automaton_type = AutomatonType.NFA
    else:
        automaton_type = AutomatonType.DFA

    return Automaton(
        type=automaton_type,
        name=name,
        states=states,
        alphabet=sorted(alphabet_set),
        initial_state=initial_items[0].state_id,
        accepting_states=[s.state_id for s in state_items if s.is_accepting],
        transitions=transitions,
    )


def automaton_to_scene(automaton: Automaton, scene: AutomatonScene) -> None:
    """Replace ``scene``'s contents with the graphical view of ``automaton``.

    Uses stored State.position when available; otherwise arranges states on
    a simple grid.

    Only FA-kind automata (DFA/NFA/ε-NFA) contribute labelled transitions;
    for richer kinds the caller should use a specialised editor.
    """
    scene.clear_automaton()
    positions = _compute_positions(automaton)
    state_items = {}
    for state in automaton.states:
        x, y = positions[state.id]
        item = scene.add_state(x, y, state_id=state.id)
        item.set_initial(state.id == automaton.initial_state)
        item.set_accepting(state.id in automaton.accepting_states)
        if state.label is not None:
            item.set_label(state.label)
        state_items[state.id] = item
    for tr in automaton.transitions:
        label = tr.read if isinstance(tr, FATransition) else getattr(tr, "read", "")
        src_id = getattr(tr, "source", "")
        tgt_id = getattr(tr, "target", "")
        src = state_items.get(src_id)
        tgt = state_items.get(tgt_id)
        if src is not None and tgt is not None:
            scene.add_transition(src, tgt, label)


def _compute_positions(automaton: Automaton) -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {}
    col = 0
    row = 0
    columns_per_row = 4
    for state in automaton.states:
        if state.position is not None:
            positions[state.id] = (state.position.x, state.position.y)
            continue
        positions[state.id] = (col * _GRID_SPACING, row * _GRID_SPACING)
        col += 1
        if col >= columns_per_row:
            col = 0
            row += 1
    return positions
