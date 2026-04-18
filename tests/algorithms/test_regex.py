"""Regex parser / formatter / Thompson / state-elimination tests."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from automata_simulator.core.algorithms import (
    fa_to_regex,
    minimize_dfa,
    nfa_to_dfa,
    regex_to_nfa,
)
from automata_simulator.core.models import (
    Automaton,
    AutomatonType,
    FATransition,
    State,
    Transition,
)
from automata_simulator.core.regex import (
    Concat,
    EmptySet,
    Epsilon,
    Literal,
    RegexNode,
    Star,
    Union,
    format_regex,
    parse_regex,
)
from automata_simulator.core.simulators import DFASimulator, NFASimulator


# ------------------------------------------------------------ parser + formatter
class TestParser:
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("a", Literal("a")),
            ("ε", Epsilon()),
            ("∅", EmptySet()),
            ("ab", Concat(Literal("a"), Literal("b"))),
            ("a|b", Union(Literal("a"), Literal("b"))),
            ("a*", Star(Literal("a"))),
        ],
    )
    def test_basic_shapes(self, source: str, expected: RegexNode) -> None:
        assert parse_regex(source) == expected

    def test_precedence_concat_over_union(self) -> None:
        # a|bc must parse as a | (bc), not (a|b)c.
        parsed = parse_regex("a|bc")
        assert parsed == Union(Literal("a"), Concat(Literal("b"), Literal("c")))

    def test_star_binds_tighter_than_concat(self) -> None:
        # ab* parses as a(b*), not (ab)*.
        parsed = parse_regex("ab*")
        assert parsed == Concat(Literal("a"), Star(Literal("b")))

    def test_plus_desugars_to_concat_star(self) -> None:
        assert parse_regex("a+") == Concat(Literal("a"), Star(Literal("a")))

    def test_question_desugars_to_union_epsilon(self) -> None:
        assert parse_regex("a?") == Union(Literal("a"), Epsilon())

    def test_double_star_is_idempotent(self) -> None:
        # Smart constructor collapses (r*)* → r*.
        assert parse_regex("a**") == Star(Literal("a"))

    def test_parens(self) -> None:
        parsed = parse_regex("(a|b)*abb")
        expected = Concat(
            Concat(
                Concat(
                    Star(Union(Literal("a"), Literal("b"))),
                    Literal("a"),
                ),
                Literal("b"),
            ),
            Literal("b"),
        )
        assert parsed == expected

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid regex"):
            parse_regex("(a|b")


class TestFormatter:
    @pytest.mark.parametrize(
        ("node", "expected"),
        [
            (Literal("a"), "a"),
            (Epsilon(), "ε"),
            (EmptySet(), "∅"),
            (Star(Literal("a")), "a*"),
            (Concat(Literal("a"), Literal("b")), "ab"),
            (Union(Literal("a"), Literal("b")), "a|b"),
            (Star(Union(Literal("a"), Literal("b"))), "(a|b)*"),
            (Concat(Literal("a"), Union(Literal("b"), Literal("c"))), "a(b|c)"),
        ],
    )
    def test_round_trip_shapes(self, node: RegexNode, expected: str) -> None:
        assert format_regex(node) == expected


# ------------------------------------------------------------ Thompson construction
class TestThompson:
    @pytest.mark.parametrize(
        ("regex", "accepts", "rejects"),
        [
            ("a", ["a"], ["", "b", "aa"]),
            ("a|b", ["a", "b"], ["", "ab", "c"]),
            ("a*", ["", "a", "aaaa"], ["b", "ab"]),
            ("a+", ["a", "aaa"], ["", "b"]),
            ("a?", ["", "a"], ["aa", "b"]),
            ("(a|b)*", ["", "a", "b", "abab", "bbba"], []),
            ("(a|b)*abb", ["abb", "aabb", "babb", "ababb"], ["", "abba", "ab", "abbb"]),
            ("a*b*", ["", "a", "b", "ab", "aaabbb"], ["ba", "abab"]),
        ],
    )
    def test_language_matches(
        self,
        regex: str,
        accepts: list[str],
        rejects: list[str],
    ) -> None:
        nfa = regex_to_nfa(parse_regex(regex))
        sim = NFASimulator(nfa)
        for w in accepts:
            assert sim.accepts(w) is True, (regex, w)
        for w in rejects:
            assert sim.accepts(w) is False, (regex, w)

    def test_output_type_is_epsilon_nfa(self) -> None:
        nfa = regex_to_nfa(parse_regex("(a|b)*"))
        assert nfa.type is AutomatonType.EPSILON_NFA
        assert nfa.initial_state in {s.id for s in nfa.states}
        assert len(nfa.accepting_states) == 1

    def test_empty_set_accepts_nothing(self) -> None:
        sim = NFASimulator(regex_to_nfa(EmptySet(), alphabet=["a"]))
        for w in ("", "a", "aa"):
            assert sim.accepts(w) is False


# ------------------------------------------------------------ state elimination
def _dfa_contains_abb() -> Automaton:
    return Automaton(
        type=AutomatonType.DFA,
        states=[State(id=s) for s in ("q0", "q1", "q2", "q3")],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q3"],
        transitions=[
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q0", target="q0", read="b"),
            FATransition(source="q1", target="q1", read="a"),
            FATransition(source="q1", target="q2", read="b"),
            FATransition(source="q2", target="q1", read="a"),
            FATransition(source="q2", target="q3", read="b"),
            FATransition(source="q3", target="q3", read="a"),
            FATransition(source="q3", target="q3", read="b"),
        ],
    )


class TestStateElimination:
    def test_language_preserved_on_contains_abb(self) -> None:
        dfa = _dfa_contains_abb()
        regex = fa_to_regex(dfa)
        rebuilt = nfa_to_dfa(regex_to_nfa(regex, alphabet=["a", "b"])).dfa
        for word in ("", "a", "abb", "babb", "abab", "aabbabb", "bab"):
            assert DFASimulator(dfa).accepts(word) == DFASimulator(rebuilt).accepts(word), word

    def test_result_is_regex_node(self) -> None:
        result = fa_to_regex(_dfa_contains_abb())
        # RegexNode is a type alias for a Union; isinstance works in Python 3.10+.
        assert isinstance(result, (Literal, Epsilon, EmptySet, Concat, Union, Star))

    def test_rejects_pda(self) -> None:
        pda = Automaton(
            type=AutomatonType.PDA,
            states=[State(id="q0")],
            alphabet=["a"],
            stack_alphabet=["Z"],
            stack_start="Z",
            initial_state="q0",
            transitions=[],
        )
        with pytest.raises(ValueError, match="DFA/NFA"):
            fa_to_regex(pda)


# ------------------------------------------------------------ property-based
_ALPHABET: list[str] = ["a", "b"]


@st.composite
def dfa_strategy(draw: st.DrawFn) -> Automaton:
    n_states = draw(st.integers(min_value=1, max_value=3))
    state_ids = [f"q{i}" for i in range(n_states)]
    accepting = sorted(draw(st.sets(st.sampled_from(state_ids), max_size=n_states)))
    transitions: list[Transition] = []
    for src in state_ids:
        for sym in _ALPHABET:
            if draw(st.booleans()):
                tgt = draw(st.sampled_from(state_ids))
                transitions.append(FATransition(source=src, target=tgt, read=sym))
    return Automaton(
        type=AutomatonType.DFA,
        states=[State(id=s) for s in state_ids],
        alphabet=list(_ALPHABET),
        initial_state="q0",
        accepting_states=accepting,
        transitions=transitions,
    )


_WORD_STRATEGY = st.text(alphabet=_ALPHABET, min_size=0, max_size=6)


@given(dfa=dfa_strategy(), word=_WORD_STRATEGY)
@settings(max_examples=75, deadline=None)
def test_dfa_to_regex_to_nfa_preserves_language(dfa: Automaton, word: str) -> None:
    regex = fa_to_regex(dfa)
    rebuilt = nfa_to_dfa(regex_to_nfa(regex, alphabet=_ALPHABET)).dfa
    minimized = minimize_dfa(rebuilt).dfa
    assert DFASimulator(dfa).accepts(word) == DFASimulator(minimized).accepts(word)


@given(word=_WORD_STRATEGY)
@settings(max_examples=50, deadline=None)
def test_parse_then_thompson_matches_by_regex(word: str) -> None:
    # `(a|b)*abb` ≡ "ends with the suffix abb".
    nfa = regex_to_nfa(parse_regex("(a|b)*abb"))
    expected = word.endswith("abb")
    assert NFASimulator(nfa).accepts(word) == expected
