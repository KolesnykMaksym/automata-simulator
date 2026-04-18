"""Transformations: NFA→DFA, ε-closure, Hopcroft minimization, Thompson, etc."""

from __future__ import annotations

from automata_simulator.core.algorithms.epsilon import (
    EpsilonRemovalResult,
    epsilon_closure,
    remove_epsilon_transitions,
)
from automata_simulator.core.algorithms.minimize import (
    MinimizationResult,
    minimize_dfa,
    remove_unreachable_states,
)
from automata_simulator.core.algorithms.subset_construction import (
    SubsetConstructionResult,
    nfa_to_dfa,
)

__all__ = [
    "EpsilonRemovalResult",
    "MinimizationResult",
    "SubsetConstructionResult",
    "epsilon_closure",
    "minimize_dfa",
    "nfa_to_dfa",
    "remove_epsilon_transitions",
    "remove_unreachable_states",
]
