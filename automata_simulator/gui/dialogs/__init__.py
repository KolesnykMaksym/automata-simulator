"""Modal dialogs (new automaton, import/export, batch test, transformations)."""

from __future__ import annotations

from automata_simulator.gui.dialogs.algorithm_dialogs import (
    ConvertToDFADialog,
    FAToRegexDialog,
    MinimizeDFADialog,
    RegexToNFADialog,
    RemoveEpsilonDialog,
)

__all__ = [
    "ConvertToDFADialog",
    "FAToRegexDialog",
    "MinimizeDFADialog",
    "RegexToNFADialog",
    "RemoveEpsilonDialog",
]
