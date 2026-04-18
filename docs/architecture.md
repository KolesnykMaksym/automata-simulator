# Architecture

## Layout

```
automata_simulator/
├── core/            # pure domain (no Qt imports)
│   ├── models/      # Automaton, State, Transition (pydantic)
│   ├── simulators/  # DFA / NFA / ε-NFA / Mealy / Moore / PDA / TM
│   ├── algorithms/  # NFA→DFA, ε-removal, Hopcroft, Thompson, state-elim,
│   │                # CFG↔PDA
│   ├── regex/       # Regex AST + lark-based parser + formatter
│   ├── cfg/         # Context-free grammar model
│   └── io/          # JSON, JFLAP .jff, Graphviz DOT
├── cli/             # Click-based CLI (automata)
└── gui/             # PySide6 editor (automata-sim)
    ├── canvas/      # QGraphicsScene, items, undo commands, scene ↔ automaton
    ├── panels/      # SimulationPanel, TapeView, StackView, StepHistoryView
    ├── dialogs/     # Algorithm / batch-test modals
    └── i18n/        # UA / EN DictTranslator
```

## Key design choices

- **Core is pure** — `automata_simulator.core.*` never imports from `gui`. The
  core ships as a standalone Python library.
- **Discriminated union for transitions** — one `Transition` type alias over
  `FATransition | MealyTransition | MooreTransition | PDATransition |
  TMTransition`, keyed on `kind`, lets pydantic validate round-trips without
  bespoke encoders.
- **Simulators own mutable state** — immutable `Automaton` model on one side,
  stateful `*Simulator` on the other. `run()` is reset-plus-loop sugar around
  step-by-step `step()` so GUI and CLI share the same primitives.
- **Scene ↔ automaton is explicit** — the GUI never mutates a Python
  `Automaton`; instead `scene_to_automaton()` lowers the canvas into a model
  and `automaton_to_scene()` does the reverse.
- **Translations without `lrelease`** — `DictTranslator` is a 30-line
  `QTranslator` subclass reading a Python dict. Shipping new locales means
  editing `translations.py`, not regenerating `.qm` files.
