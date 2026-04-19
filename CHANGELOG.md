# Changelog

All notable changes to **Automata Simulator** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

## [0.2.0] - 2026-04-19

Post-0.1.0 GUI polish — editor quality-of-life upgrades.

### Added

- **File menu wired up:** New / Open… / Save / Save As… load and save
  native JSON or JFLAP ``.jff`` files. Title bar reflects the active
  file; ``load_path()`` is exposed publicly for scripting.
- **Dark theme:** View → Dark theme toggles between light and dark
  palettes instantly. Canvas items read the palette on every paint
  cycle, so states, transitions, tape and stack follow the theme.
- **Inline transition labels:** creating a transition via Shift-drag
  prompts for the label immediately; double-clicking an existing
  transition reopens the dialog to edit it.
- **Trackpad-friendly navigation:** plain wheel / two-finger swipe
  pans the viewport, pinch gestures zoom via
  ``QNativeGestureEvent``, Ctrl+wheel zooms on keyboards without a
  trackpad. Public ``zoom_in`` / ``zoom_out`` / ``reset_zoom`` /
  ``fit_in_view`` drive new View-menu shortcuts (Cmd+=, Cmd+-,
  Ctrl+0, Ctrl+9) and ``load_path()`` auto-fits new documents.
- **Library dock (left):** ``LibraryPanel`` auto-populates from
  ``examples/`` on start, accumulates every File → Open, dedups and
  bumps the most recent entry to the top, emits ``load_requested``
  on double-click / Enter so the canvas follows.
- **Simulation input presets:** a "Quick inputs:" list below the
  input field offers curated test strings. Lookup is
  name-first (bundled examples get tailored suggestions) and
  type-second (any DFA / NFA / PDA / TM / Mealy / Moore still gets a
  sensible default). Manual input remains available.

### Fixed

- ``DictTranslator`` now falls back to the source text when a key is
  missing from ``TRANSLATIONS_UA`` — previously an empty translation
  collapsed the Ukrainian menu bar to blank entries.

## [0.1.0] - 2026-04-19

First public release.

### Added

#### Core domain (pure Python, no Qt)

- Pydantic domain models: `Automaton`, `State`, `Position`, discriminated
  `Transition` union (`FATransition` / `MealyTransition` / `MooreTransition` /
  `PDATransition` / `TMTransition`), `AutomatonType` StrEnum for all seven
  supported kinds, `TapeMove` direction enum, `EPSILON` / `DEFAULT_BLANK`
  constants. Cross-field validator enforces determinism for DFA, ε-rejection
  for plain NFA, Mealy/Moore output-alphabet rules, PDA stack rules and TM
  tape-count / tape-alphabet rules.
- Simulators with a shared `Verdict` vocabulary (`ACCEPTED`,
  `REJECTED_NON_ACCEPTING`, `REJECTED_STUCK`, `REJECTED_INVALID_SYMBOL`,
  `REJECTED_EMPTY_CONFIG`, `REJECTED_TIMEOUT`): step-by-step `DFASimulator`,
  frontier-based `NFASimulator` (handles NFA and ε-NFA), deterministic
  `MealySimulator` and `MooreSimulator` transducers with `translate()`,
  breadth-first non-deterministic `PDASimulator` with trace reconstruction,
  deterministic multi-tape `TMSimulator` with auto-growing `_MutableTape`.
- Algorithms: `epsilon_closure`, `remove_epsilon_transitions`, Rabin-Scott
  `nfa_to_dfa` (with subset mapping), Hopcroft `minimize_dfa` (with
  `equivalence_classes`), Thompson `regex_to_nfa`, state-elimination
  `fa_to_regex`, `cfg_to_pda`, `normalize_pda`, `pda_to_cfg`.
- Regex AST (`Literal`, `Epsilon`, `EmptySet`, `Concat`, `Union`, `Star`)
  with smart identity constructors, lark-based `parse_regex`, canonical
  `format_regex`.
- CFG model with `Production` and full structural validation.
- I/O: native JSON (pydantic round-trip), JFLAP `.jff` (XML) for
  DFA/NFA/ε-NFA / PDA / single-tape TM / Mealy / Moore, Graphviz DOT
  text export.

#### CLI (`automata`)

- `simulate`, `convert` (NFA→DFA, ε-NFA→NFA), `minimize`, `batch-test`
  (CSV / JSON reports), `export` (DOT / SVG / PNG via pydot).
- Auto-detects file format by extension.

#### GUI (`automata-sim`, PySide6)

- MainWindow with File / Edit / View / Simulation / Algorithms / Help
  menus. Central widget is an `AutomatonView` (zoomable QGraphicsScene),
  right-side dock hosts the simulation panel.
- Canvas: drag-and-drop states, shift-drag transitions, right-click
  context menu (set initial / toggle accepting / rename / delete),
  self-loop rendering, initial-arrow stub, accepting double-ring,
  active-state highlight.
- Simulation panel: input field, Run / Step / Pause / Reset, speed
  slider (0.1×–10×), status label, active-state highlighting.
- Dialogs: ConvertToDFA, RemoveEpsilon, MinimizeDFA, RegexToNFA,
  FAToRegex, BatchTest (with CSV/JSON export).
- Specialised panels: TapeView (TM), StackView (PDA), StepHistoryView.
- Editor undo/redo via `QUndoStack` (AddState / AddTransition /
  RemoveState commands), wired through Ctrl+Z / Ctrl+Y.
- i18n: `DictTranslator` + Python dict translations, runtime UA ↔ EN
  switcher in View → Language.

#### Testing

- 421 tests across core, algorithms, I/O, CLI and GUI.
- Property-based coverage (Hypothesis, 100 examples each) for
  minimisation, subset construction, ε-removal, and end-to-end
  regex round-trips.
- Coverage ≥ 85 % enforced via `pytest-cov`.

#### Ops

- `pyproject.toml` (hatchling), strict ruff + mypy configs.
- Multi-stage `Dockerfile` (python:3.13-slim + Graphviz) for headless
  CLI use; `docker-compose.yml` for dev.
- `mkdocs.yml` + Material-themed docs with mkdocstrings API reference.
- PyInstaller `packaging/automata-sim.spec` for standalone GUI bundles.
- GitHub Actions: `ci.yml` (lint → mypy → tests matrix → build wheel),
  `release.yml` (tag-triggered PyPI publish via OIDC),
  `binaries.yml` (PyInstaller matrix + MkDocs build).
- Canonical `examples/` directory with seven regenerable JSON files.

### Known limitations

- `pda_to_cfg` / `normalize_pda` produce a structurally valid grammar
  but do not guarantee full language-equivalence round-trips — the
  bottom-marker push/pop pairing is intentionally skipped. Documented
  in `pda_to_cfg.py`'s module docstring.
- JFLAP `.jff` export for Turing machines supports single-tape only.
- SVG / PNG export relies on a system `graphviz` binary.

## [Unreleased]
