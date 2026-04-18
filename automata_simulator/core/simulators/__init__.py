"""Per-automaton-type simulators (DFA / NFA / ε-NFA / Mealy / Moore / PDA / TM)."""

from __future__ import annotations

from automata_simulator.core.simulators.base import (
    SimulatorNotReadyError,
    Verdict,
    WrongAutomatonTypeError,
)
from automata_simulator.core.simulators.dfa import DFASimulator, DFAStep, DFATrace
from automata_simulator.core.simulators.mealy import (
    MealySimulator,
    MealyStep,
    MealyTrace,
)
from automata_simulator.core.simulators.moore import (
    MooreSimulator,
    MooreStep,
    MooreTrace,
)
from automata_simulator.core.simulators.nfa import NFASimulator, NFAStep, NFATrace
from automata_simulator.core.simulators.pda import (
    PDAConfig,
    PDASimulator,
    PDAStep,
    PDATrace,
)
from automata_simulator.core.simulators.tm import (
    TMConfig,
    TMSimulator,
    TMStep,
    TMTrace,
)

__all__ = [
    "DFASimulator",
    "DFAStep",
    "DFATrace",
    "MealySimulator",
    "MealyStep",
    "MealyTrace",
    "MooreSimulator",
    "MooreStep",
    "MooreTrace",
    "NFASimulator",
    "NFAStep",
    "NFATrace",
    "PDAConfig",
    "PDASimulator",
    "PDAStep",
    "PDATrace",
    "SimulatorNotReadyError",
    "TMConfig",
    "TMSimulator",
    "TMStep",
    "TMTrace",
    "Verdict",
    "WrongAutomatonTypeError",
]
