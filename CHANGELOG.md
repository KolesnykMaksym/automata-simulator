# Changelog

All notable changes to **Automata Simulator** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

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
