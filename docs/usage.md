# Quickstart

## Install

```bash
pip install automata-simulator
```

## Launch the GUI

```bash
automata-sim
```

The main window opens with an empty canvas and a simulation dock on the right.

- **Double-click** on empty canvas → new state.
- **Shift-drag** between two states → transition (edit the label afterwards).
- **Right-click** a state → context menu (set initial / toggle accepting /
  rename / delete).
- Menu **View → Language** hot-swaps between English and Ukrainian.

## Run a simulation

1. Type an input string in the "Input string…" field.
2. Press **Step** to advance one symbol, or **Run** for auto-play.
3. Use the speed slider (0.1× – 10×) to control auto-play.
4. Watch the canvas: the active state(s) light up in yellow, the transition
   fired last step turns orange.

## Batch test

`Simulation → Batch test…` opens the modal. Paste many input strings (one per
line) or load them from a file, press **Run**, then export the report as CSV
or JSON.

## Algorithms

The `Algorithms` menu wires up the standard transformations:

- NFA → DFA (subset construction) — shows the DFA state ← NFA subset mapping.
- ε-NFA → NFA (ε-removal) — shows per-state ε-closure.
- Minimise DFA (Hopcroft) — shows equivalence classes.
- Regex → NFA (Thompson) — opens a modal to type a regex.
- NFA → Regex (state elimination) — renders the canonical regex.

**Apply** replaces the canvas with the algorithm's result.
