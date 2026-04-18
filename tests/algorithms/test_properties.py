"""Property-based tests: algorithms preserve the language they operate on."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from automata_simulator.core.algorithms import (
    minimize_dfa,
    nfa_to_dfa,
    remove_epsilon_transitions,
)
from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
    Transition,
)
from automata_simulator.core.simulators import DFASimulator, NFASimulator

_ALPHABET: list[str] = ["a", "b"]


# ----------------------------------------------------------------------- strategies
@st.composite
def dfa_strategy(draw: st.DrawFn) -> Automaton:
    """Generate a small, possibly partial DFA over ``{a, b}``."""
    n_states = draw(st.integers(min_value=1, max_value=4))
    state_ids = [f"q{i}" for i in range(n_states)]
    accepting = sorted(draw(st.sets(st.sampled_from(state_ids), max_size=n_states)))
    transitions: list[Transition] = []
    defined: set[tuple[str, str]] = set()
    for src in state_ids:
        for sym in _ALPHABET:
            if draw(st.booleans()):
                tgt = draw(st.sampled_from(state_ids))
                transitions.append(FATransition(source=src, target=tgt, read=sym))
                defined.add((src, sym))
    return Automaton(
        type=AutomatonType.DFA,
        states=[State(id=s) for s in state_ids],
        alphabet=list(_ALPHABET),
        initial_state="q0",
        accepting_states=accepting,
        transitions=transitions,
    )


@st.composite
def nfa_strategy(draw: st.DrawFn) -> Automaton:
    """Generate a small NFA over ``{a, b}`` (no ε)."""
    n_states = draw(st.integers(min_value=1, max_value=4))
    state_ids = [f"q{i}" for i in range(n_states)]
    accepting = sorted(draw(st.sets(st.sampled_from(state_ids), max_size=n_states)))
    n_transitions = draw(st.integers(min_value=0, max_value=8))
    transitions: list[Transition] = []
    for _ in range(n_transitions):
        src = draw(st.sampled_from(state_ids))
        tgt = draw(st.sampled_from(state_ids))
        sym = draw(st.sampled_from(_ALPHABET))
        transitions.append(FATransition(source=src, target=tgt, read=sym))
    return Automaton(
        type=AutomatonType.NFA,
        states=[State(id=s) for s in state_ids],
        alphabet=list(_ALPHABET),
        initial_state="q0",
        accepting_states=accepting,
        transitions=transitions,
    )


@st.composite
def epsilon_nfa_strategy(draw: st.DrawFn) -> Automaton:
    """Generate a small ε-NFA over ``{a, b}``."""
    n_states = draw(st.integers(min_value=1, max_value=4))
    state_ids = [f"q{i}" for i in range(n_states)]
    accepting = sorted(draw(st.sets(st.sampled_from(state_ids), max_size=n_states)))
    # Some epsilon edges, some regular edges.
    n_eps = draw(st.integers(min_value=0, max_value=4))
    n_reg = draw(st.integers(min_value=0, max_value=6))
    transitions: list[Transition] = []
    for _ in range(n_eps):
        src = draw(st.sampled_from(state_ids))
        tgt = draw(st.sampled_from(state_ids))
        transitions.append(FATransition(source=src, target=tgt, read=EPSILON))
    for _ in range(n_reg):
        src = draw(st.sampled_from(state_ids))
        tgt = draw(st.sampled_from(state_ids))
        sym = draw(st.sampled_from(_ALPHABET))
        transitions.append(FATransition(source=src, target=tgt, read=sym))
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        states=[State(id=s) for s in state_ids],
        alphabet=list(_ALPHABET),
        initial_state="q0",
        accepting_states=accepting,
        transitions=transitions,
    )


_WORD_STRATEGY = st.text(alphabet=_ALPHABET, min_size=0, max_size=8)


# ----------------------------------------------------------------------- properties
@given(dfa=dfa_strategy(), word=_WORD_STRATEGY)
@settings(max_examples=100, deadline=None)
def test_minimize_preserves_language(dfa: Automaton, word: str) -> None:
    minimized = minimize_dfa(dfa).dfa
    assert DFASimulator(dfa).accepts(word) == DFASimulator(minimized).accepts(word)


@given(nfa=nfa_strategy(), word=_WORD_STRATEGY)
@settings(max_examples=100, deadline=None)
def test_subset_construction_preserves_language_for_nfa(nfa: Automaton, word: str) -> None:
    dfa = nfa_to_dfa(nfa).dfa
    assert NFASimulator(nfa).accepts(word) == DFASimulator(dfa).accepts(word)


@given(enfa=epsilon_nfa_strategy(), word=_WORD_STRATEGY)
@settings(max_examples=100, deadline=None)
def test_subset_construction_preserves_language_for_epsilon_nfa(
    enfa: Automaton,
    word: str,
) -> None:
    dfa = nfa_to_dfa(enfa).dfa
    assert NFASimulator(enfa).accepts(word) == DFASimulator(dfa).accepts(word)


@given(enfa=epsilon_nfa_strategy(), word=_WORD_STRATEGY)
@settings(max_examples=100, deadline=None)
def test_epsilon_removal_preserves_language(enfa: Automaton, word: str) -> None:
    nfa = remove_epsilon_transitions(enfa).nfa
    assert NFASimulator(enfa).accepts(word) == NFASimulator(nfa).accepts(word)


@given(nfa=nfa_strategy(), word=_WORD_STRATEGY)
@settings(max_examples=100, deadline=None)
def test_minimize_after_subset_construction_matches_nfa(nfa: Automaton, word: str) -> None:
    """End-to-end: NFA → DFA → minimise preserves language."""
    dfa = nfa_to_dfa(nfa).dfa
    minimized = minimize_dfa(dfa).dfa
    assert NFASimulator(nfa).accepts(word) == DFASimulator(minimized).accepts(word)
