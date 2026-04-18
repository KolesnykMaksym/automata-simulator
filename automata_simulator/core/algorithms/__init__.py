"""Transformations: NFA→DFA, ε-closure, Hopcroft minimization, Thompson, etc."""

from __future__ import annotations

from automata_simulator.core.algorithms.cfg_to_pda import cfg_to_pda
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
from automata_simulator.core.algorithms.pda_normalize import normalize_pda
from automata_simulator.core.algorithms.pda_to_cfg import pda_to_cfg
from automata_simulator.core.algorithms.state_elimination import fa_to_regex
from automata_simulator.core.algorithms.subset_construction import (
    SubsetConstructionResult,
    nfa_to_dfa,
)
from automata_simulator.core.algorithms.thompson import regex_to_nfa

__all__ = [
    "EpsilonRemovalResult",
    "MinimizationResult",
    "SubsetConstructionResult",
    "cfg_to_pda",
    "epsilon_closure",
    "fa_to_regex",
    "minimize_dfa",
    "nfa_to_dfa",
    "normalize_pda",
    "pda_to_cfg",
    "regex_to_nfa",
    "remove_epsilon_transitions",
    "remove_unreachable_states",
]
