"""QGraphicsScene-based canvas for the automaton editor."""

from __future__ import annotations

from automata_simulator.gui.canvas.scene import AutomatonScene
from automata_simulator.gui.canvas.scene_conversion import (
    SceneConversionError,
    scene_to_automaton,
)
from automata_simulator.gui.canvas.state_item import STATE_RADIUS, StateItem
from automata_simulator.gui.canvas.transition_item import TransitionItem
from automata_simulator.gui.canvas.view import AutomatonView

__all__ = [
    "STATE_RADIUS",
    "AutomatonScene",
    "AutomatonView",
    "SceneConversionError",
    "StateItem",
    "TransitionItem",
    "scene_to_automaton",
]
