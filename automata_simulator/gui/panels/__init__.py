"""Specialised side panels: TapeView (TM), StackView (PDA), StepHistoryView."""

from __future__ import annotations

from automata_simulator.gui.panels.library_panel import LibraryPanel
from automata_simulator.gui.panels.simulation_panel import SimulationPanel
from automata_simulator.gui.panels.stack_view import StackView
from automata_simulator.gui.panels.step_history import StepHistoryView
from automata_simulator.gui.panels.tape_view import TapeView

__all__ = [
    "LibraryPanel",
    "SimulationPanel",
    "StackView",
    "StepHistoryView",
    "TapeView",
]
