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


class SceneConversionError(ValueError):
    """Raised when the scene can't be lowered to a valid automaton."""


def scene_to_automaton(  # noqa: PLR0912 — single-pass scene walker is clearest
    scene: AutomatonScene, *, name: str = "scene",
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
