"""QGraphicsScene-based canvas for the automaton editor."""

from __future__ import annotations

from automata_simulator.gui.canvas.scene import AutomatonScene
from automata_simulator.gui.canvas.scene_conversion import (
    SceneConversionError,
    automaton_to_scene,
    scene_to_automaton,
)
from automata_simulator.gui.canvas.state_item import STATE_RADIUS, StateItem
from automata_simulator.gui.canvas.transition_item import TransitionItem
from automata_simulator.gui.canvas.undo_commands import (
    AddStateCommand,
    AddTransitionCommand,
    RemoveStateCommand,
)
from automata_simulator.gui.canvas.view import AutomatonView

__all__ = [
    "STATE_RADIUS",
    "AddStateCommand",
    "AddTransitionCommand",
    "AutomatonScene",
    "AutomatonView",
    "RemoveStateCommand",
    "SceneConversionError",
    "StateItem",
    "TransitionItem",
    "automaton_to_scene",
    "scene_to_automaton",
]
