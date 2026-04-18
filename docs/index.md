# Automata Simulator

> Відкритий освітній симулятор автоматів — сучасна заміна JFLAP. /
> Open-source educational automata simulator — a modern JFLAP replacement.

## Supported machines

| Machine | Class |
|---|---|
| DFA | Deterministic finite automaton |
| NFA | Non-deterministic finite automaton |
| ε-NFA | NFA with ε-transitions |
| Mealy | Transducer (output on transition) |
| Moore | Transducer (output on state) |
| PDA | Pushdown automaton (deterministic & non-deterministic) |
| TM | Turing machine (single and multi-tape) |

## Key features

- Drag-and-drop canvas editor (PySide6) with undo/redo.
- Step-by-step simulation with animation of active state(s) and transitions.
- Batch testing with CSV/JSON reports.
- Algorithms: NFA→DFA (subset construction), ε-removal, Hopcroft minimisation,
  Thompson's regex→NFA, state-elimination NFA→regex, CFG↔PDA.
- JFLAP `.jff` import/export, native JSON, Graphviz DOT.
- Bilingual UI (Ukrainian / English), runtime switchable.
- CLI for headless use and a Docker image for batch runs.

## Getting started

```bash
pip install automata-simulator
automata-sim           # GUI
automata --help        # CLI
```

See [Quickstart](usage.md) for a guided tour or the [Architecture](architecture.md)
page for an overview of the internals.

## Українською

Автомата Simulator — інструмент для симуляції, візуалізації та трансформації
класичних моделей автоматів. Графічний редактор побудовано на **PySide6**,
алгоритми — в чистому Python з повною статичною типізацією (`mypy --strict`)
та property-based тестами (Hypothesis). Підтримка українського інтерфейсу —
через runtime-перемикач мови в меню **View → Language**.
