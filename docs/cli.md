# Command-line interface

Everything the GUI does against the scene, `automata` can do against files.

File format is inferred from the extension: `.json` (native), `.jff` (JFLAP),
`.dot` (Graphviz).

## `simulate`

```bash
automata simulate automaton.jff -i "aabba"
automata simulate automaton.jff -i "aabba" --step    # print every step
```

## `convert`

```bash
automata convert nfa.jff --to dfa -o dfa.json
automata convert enfa.json --to nfa -o nfa.jff
```

## `minimize`

```bash
automata minimize dfa.json -o minimised.json
```

## `batch-test`

```bash
automata batch-test automaton.jff --strings tests.txt --report report.csv
automata batch-test automaton.jff --strings tests.txt --report report.json
```

CSV columns: `input,verdict,accepted,time_ms`. JSON is an array of the same
records.

## `export`

```bash
automata export dfa.jff --format dot -o diagram.dot
automata export dfa.jff --format svg -o diagram.svg   # requires graphviz
automata export dfa.jff --format png -o diagram.png
```

SVG / PNG rendering uses `pydot` and the system `graphviz` binary. Install
Graphviz via your package manager (`brew install graphviz`, `apt install
graphviz`) before using these formats.
