# Examples

Canonical automata in the project's native JSON format. Regenerate with:

```bash
python scripts/generate_examples.py
```

| File | Kind | Language / behaviour |
|---|---|---|
| `dfa_contains_abb.json` | DFA | strings over `{a,b}` that contain `abb` as a substring |
| `nfa_ends_in_abb.json` | NFA | strings over `{a,b}` ending in `abb` |
| `enfa_a_star_b_star.json` | ε-NFA | `a*b*` |
| `pda_a_n_b_n.json` | PDA | `{aⁿbⁿ : n ≥ 0}` |
| `tm_bit_inverter.json` | TM | flip every bit on the tape, then halt |
| `mealy_detect_101.json` | Mealy | output `1` exactly when the last three symbols were `101` |
| `moore_mod3.json` | Moore | Moore counter — each state's output is `(binary prefix) mod 3` |

Load any of them from the CLI:

```bash
automata simulate examples/dfa_contains_abb.json -i "aabbabb"
automata batch-test examples/pda_a_n_b_n.json \
    --strings tests.txt --report report.csv
```

Or from the GUI via **File → Open…**.
