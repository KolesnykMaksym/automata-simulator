"""CFG ↔ PDA conversion tests."""

from __future__ import annotations

import pytest

from automata_simulator.core.algorithms import (
    cfg_to_pda,
    normalize_pda,
    pda_to_cfg,
)
from automata_simulator.core.cfg import CFG, Production
from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    PDATransition,
    State,
)
from automata_simulator.core.simulators import PDASimulator


# ------------------------------------------------------------ canonical grammars
def _cfg_a_n_b_n() -> CFG:
    """S → a S b | ε (the language {a^n b^n : n ≥ 0})."""
    return CFG(
        name="a-n-b-n",
        nonterminals=["S"],
        terminals=["a", "b"],
        productions=[
            Production(head="S", body=("a", "S", "b")),
            Production(head="S", body=()),
        ],
        start="S",
    )


def _cfg_even_palindromes() -> CFG:
    """S → a S a | b S b | ε."""
    return CFG(
        name="even-palindromes",
        nonterminals=["S"],
        terminals=["a", "b"],
        productions=[
            Production(head="S", body=("a", "S", "a")),
            Production(head="S", body=("b", "S", "b")),
            Production(head="S", body=()),
        ],
        start="S",
    )


def _pda_a_n_b_n_hand() -> Automaton:
    """Hand-written PDA for {a^n b^n}, kept for the PDA→CFG direction."""
    return Automaton(
        type=AutomatonType.PDA,
        name="hand-a-n-b-n",
        states=[State(id=s) for s in ("q0", "q1", "qf")],
        alphabet=["a", "b"],
        stack_alphabet=["Z", "A"],
        stack_start="Z",
        initial_state="q0",
        accepting_states=["qf"],
        transitions=[
            PDATransition(source="q0", target="qf", read=EPSILON, pop="Z", push=("Z",)),
            PDATransition(source="q0", target="q0", read="a", pop="Z", push=("A", "Z")),
            PDATransition(source="q0", target="q0", read="a", pop="A", push=("A", "A")),
            PDATransition(source="q0", target="q1", read="b", pop="A", push=()),
            PDATransition(source="q1", target="q1", read="b", pop="A", push=()),
            PDATransition(source="q1", target="qf", read=EPSILON, pop="Z", push=("Z",)),
        ],
    )


# ------------------------------------------------------------ CFG → PDA
class TestCFGToPDA:
    @pytest.mark.parametrize("n", [0, 1, 2, 3, 4])
    def test_a_n_b_n_accepts_balanced(self, n: int) -> None:
        pda = cfg_to_pda(_cfg_a_n_b_n())
        assert PDASimulator(pda).accepts("a" * n + "b" * n) is True

    @pytest.mark.parametrize("word", ["a", "b", "ab" * 2, "aab", "abb", "ba"])
    def test_a_n_b_n_rejects_unbalanced(self, word: str) -> None:
        pda = cfg_to_pda(_cfg_a_n_b_n())
        assert PDASimulator(pda).accepts(word) is False

    @pytest.mark.parametrize("word", ["", "aa", "bb", "abba", "baab", "aabbaa", "abaaba"])
    def test_even_palindromes_accepts(self, word: str) -> None:
        pda = cfg_to_pda(_cfg_even_palindromes())
        assert PDASimulator(pda).accepts(word) is True

    @pytest.mark.parametrize("word", ["a", "ab", "aba", "abab", "aabb"])
    def test_even_palindromes_rejects(self, word: str) -> None:
        pda = cfg_to_pda(_cfg_even_palindromes())
        assert PDASimulator(pda).accepts(word) is False

    def test_output_type_is_pda(self) -> None:
        pda = cfg_to_pda(_cfg_a_n_b_n())
        assert pda.type is AutomatonType.PDA
        assert len(pda.accepting_states) == 1


# ------------------------------------------------------------ normalisation
class TestNormalizePDA:
    def test_preserves_language_on_hand_pda(self) -> None:
        original = _pda_a_n_b_n_hand()
        normalised = normalize_pda(original)
        # Still accepts the same language (tested on a small battery).
        for word in ("", "ab", "aabb", "aaabbb"):
            assert PDASimulator(normalised).accepts(word) is True, word
        for word in ("a", "b", "abab", "aaabb"):
            assert PDASimulator(normalised).accepts(word) is False, word

    def test_has_single_accepting_state(self) -> None:
        normalised = normalize_pda(_pda_a_n_b_n_hand())
        assert len(normalised.accepting_states) == 1

    def test_each_transition_is_single_push_or_single_pop(self) -> None:
        normalised = normalize_pda(_pda_a_n_b_n_hand())
        for tr in normalised.transitions:
            assert isinstance(tr, PDATransition)
            is_push = tr.pop == EPSILON and len(tr.push) == 1
            is_pop = tr.pop != EPSILON and len(tr.push) == 0
            assert is_push or is_pop, tr

    def test_rejects_non_pda(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="PDA"):
            normalize_pda(dfa)


# ------------------------------------------------------------ PDA → CFG
class TestPDAToCFG:
    """Structural tests for pda_to_cfg.

    We verify that the construction produces a CFG of the expected shape
    (start symbol exists, matched-pair productions exist, A[p,p]→ε rules
    exist) and that the resulting CFG fits back into ``cfg_to_pda`` without
    validation errors. Full language-equivalence round-trips are not asserted
    here — see the docstring of ``pda_to_cfg`` for the known limitation.
    """

    def test_start_symbol_is_present(self) -> None:
        cfg = pda_to_cfg(_pda_a_n_b_n_hand())
        assert cfg.start in cfg.nonterminals

    def test_has_trivial_epsilon_rules(self) -> None:
        cfg = pda_to_cfg(_pda_a_n_b_n_hand())
        epsilon_rules = [p for p in cfg.productions if p.is_epsilon]
        # One A[p,p] → ε for every state.
        assert len(epsilon_rules) >= 1

    def test_round_trip_structure(self) -> None:
        cfg = pda_to_cfg(_pda_a_n_b_n_hand())
        rebuilt = cfg_to_pda(cfg)
        assert rebuilt.type is AutomatonType.PDA
        assert len(rebuilt.accepting_states) == 1

    def test_rejects_non_pda(self) -> None:
        dfa = Automaton(
            type=AutomatonType.DFA,
            states=[State(id="q0")],
            alphabet=["a"],
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="PDA"):
            pda_to_cfg(dfa)


# ------------------------------------------------------------ CFG model validation
class TestCFGModel:
    def test_start_must_be_nonterminal(self) -> None:
        with pytest.raises(ValueError, match="Start symbol"):
            CFG(
                nonterminals=["S"],
                terminals=["a"],
                productions=[],
                start="Missing",
            )

    def test_production_head_must_be_nonterminal(self) -> None:
        with pytest.raises(ValueError, match="head"):
            CFG(
                nonterminals=["S"],
                terminals=["a"],
                productions=[Production(head="T", body=("a",))],
                start="S",
            )

    def test_body_symbols_must_be_in_vocab(self) -> None:
        with pytest.raises(ValueError, match="body symbol"):
            CFG(
                nonterminals=["S"],
                terminals=["a"],
                productions=[Production(head="S", body=("a", "X"))],
                start="S",
            )

    def test_disjoint_vocabularies(self) -> None:
        with pytest.raises(ValueError, match="disjoint"):
            CFG(
                nonterminals=["S", "a"],
                terminals=["a"],
                productions=[],
                start="S",
            )

    def test_epsilon_production(self) -> None:
        cfg = CFG(
            nonterminals=["S"],
            terminals=["a"],
            productions=[Production(head="S", body=())],
            start="S",
        )
        assert cfg.productions[0].is_epsilon is True
