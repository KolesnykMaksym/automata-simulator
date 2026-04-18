# Algorithms

## NFA → DFA (subset construction)

`core.algorithms.nfa_to_dfa` implements Rabin-Scott. Returns a
`SubsetConstructionResult`:

```python
result = nfa_to_dfa(nfa)
print(result.dfa)                # the DFA
print(result.subset_by_state)    # {dfa_state_id: frozenset of NFA ids}
```

Works on both NFA and ε-NFA (ε-closure is folded in).

## ε-NFA → NFA (ε-removal)

`core.algorithms.remove_epsilon_transitions` collapses ε-closures. Returns an
`EpsilonRemovalResult` with `nfa` and `closure_by_state`.

## Minimisation (Hopcroft)

`core.algorithms.minimize_dfa` applies `remove_unreachable_states →
totalise → partition refinement → rebuild`. Returns a `MinimizationResult`
with the DFA and `equivalence_classes`. Empty languages collapse to a single
`[dead]` state.

## Regex ↔ NFA

- `parse_regex(text) → RegexNode` (lark earley grammar).
- `regex_to_nfa(node) → Automaton` via Thompson's construction.
- `fa_to_regex(automaton) → RegexNode` via state elimination with smart
  identity constructors (`ε·r=r`, `r|∅=r`, `(r*)*=r*`).
- `format_regex(node) → str` — canonical pretty-printer.

## CFG ↔ PDA

- `cfg_to_pda(cfg)` — canonical 3-state construction (load / main / accept)
  around a `$` bottom marker.
- `normalize_pda(pda)` — brings a PDA to Sipser's normal form (single
  start/accept, stack cleared before accepting, every transition pure push-one
  or pure pop-one).
- `pda_to_cfg(pda)` — Sipser Th. 2.20 construction. Starts by normalising
  the input. **Known limitation:** the normaliser does not explicitly push
  the bottom sentinel, so language-equivalence isn't strictly round-tripped.
  The GUI / CLI surface this as a documented caveat.

## Property-based coverage

Every transformation is exercised by Hypothesis property tests
(`tests/algorithms/test_properties.py`) with `max_examples=100`:

- `minimize(dfa).accepts(w) == dfa.accepts(w)`
- `nfa_to_dfa(nfa).accepts(w) == nfa.accepts(w)` (incl. ε-NFA)
- `remove_epsilon(enfa).accepts(w) == enfa.accepts(w)`
- `NFA → DFA → minimise` preserves language
- `DFA → regex → Thompson → subset → minimise` preserves language
