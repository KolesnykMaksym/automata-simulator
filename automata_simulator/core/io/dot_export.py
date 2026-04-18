"""Graphviz DOT text export (no binary rendering).

Summary (UA): Генератор текстового представлення автомата у форматі DOT
(Graphviz). Labels для кожного типу автомата окремі; прийнятні стани —
подвійне коло; початковий — стрілка з невидимого вузла.
Summary (EN): Pure-text DOT builder. Rendering to SVG/PNG lives in
``render.py`` behind an optional Graphviz-binary check.
"""

from __future__ import annotations

from pathlib import Path

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    MealyTransition,
    MooreTransition,
    PDATransition,
    TMTransition,
    Transition,
)


def to_dot(automaton: Automaton) -> str:
    """Return a Graphviz DOT description of ``automaton``."""
    lines: list[str] = [
        f"digraph {_dot_id(automaton.name)} {{",
        "  rankdir=LR;",
        '  node [shape=circle, fontname="Helvetica"];',
    ]
    # Accepting states → double circle.
    for state in automaton.states:
        if state.is_accepting or state.id in automaton.accepting_states:
            lines.append(f'  "{_escape(state.id)}" [shape=doublecircle];')
    # Moore labels state with its output.
    if automaton.type is AutomatonType.MOORE:
        for state in automaton.states:
            if state.moore_output is not None:
                shape = "doublecircle" if state.id in automaton.accepting_states else "circle"
                lines.append(
                    f'  "{_escape(state.id)}" '
                    f'[label="{_escape(state.id)}\\n/{_escape(state.moore_output)}", '
                    f"shape={shape}];",
                )
    # Invisible entry node + initial arrow.
    lines.append('  __entry__ [shape=none, label=""];')
    lines.append(f'  __entry__ -> "{_escape(automaton.initial_state)}";')
    # Transitions.
    for tr in automaton.transitions:
        label = _transition_label(tr)
        lines.append(
            f'  "{_escape(tr.source)}" -> "{_escape(tr.target)}" [label="{_escape(label)}"];',
        )
    lines.append("}")
    return "\n".join(lines)


def save_dot(automaton: Automaton, path: Path) -> None:
    """Write the DOT text to ``path``."""
    path.write_text(to_dot(automaton), encoding="utf-8")


def _transition_label(tr: Transition) -> str:
    if isinstance(tr, FATransition):
        return tr.read
    if isinstance(tr, MealyTransition):
        return f"{tr.read}/{tr.write}"
    if isinstance(tr, MooreTransition):
        return tr.read
    if isinstance(tr, PDATransition):
        pop = tr.pop if tr.pop != EPSILON else "ε"
        push = "".join(tr.push) if tr.push else "ε"
        return f"{tr.read},{pop}/{push}"
    if isinstance(tr, TMTransition):
        pairs = [f"{r}/{w},{m.value}" for r, w, m in zip(tr.read, tr.write, tr.move, strict=True)]
        return " | ".join(pairs)
    raise TypeError(f"Unknown transition kind: {type(tr).__name__}")


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _dot_id(name: str) -> str:
    # Conservative identifier sanitization for the top-level digraph name.
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    return safe or "automaton"
