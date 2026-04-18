"""Modal dialogs (new automaton, import/export, batch test, transformations)."""

from __future__ import annotations

from automata_simulator.gui.dialogs.algorithm_dialogs import (
    ConvertToDFADialog,
    FAToRegexDialog,
    MinimizeDFADialog,
    RegexToNFADialog,
    RemoveEpsilonDialog,
)
from automata_simulator.gui.dialogs.batch_test_dialog import (
    BatchResult,
    BatchTestDialog,
)

__all__ = [
    "BatchResult",
    "BatchTestDialog",
    "ConvertToDFADialog",
    "FAToRegexDialog",
    "MinimizeDFADialog",
    "RegexToNFADialog",
    "RemoveEpsilonDialog",
]
