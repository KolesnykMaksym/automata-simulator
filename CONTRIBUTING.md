# Contributing

Thanks for taking the time to make **Automata Simulator** better.

## Local setup

```bash
git clone https://github.com/kolesnyk-maksym/automata-simulator.git
cd automata-simulator
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install
```

Run the full quality gate before every commit:

```bash
ruff check .
ruff format --check .
mypy
QT_QPA_PLATFORM=offscreen pytest --cov
```

All four must pass; the project enforces **≥ 85 % coverage** via `pytest-cov`.

## Architecture ground rules

- **`automata_simulator.core` never imports from `automata_simulator.gui`.**
  The core ships as a standalone library; keep it pure Python.
- **Pydantic for data.** Every automaton / CFG / regex round-trip is validated
  through pydantic v2 models. Don't introduce parallel plain-dataclass models.
- **Simulators own mutable state; models don't.** `run()` is reset-plus-loop
  sugar around `step()`.
- **Strict typing.** `mypy --strict` is mandatory. Prefer `cast(...)` over
  `# type: ignore`, and document any `# type: ignore` with a reason.
- **Docstrings.** Every public symbol uses Google-style bilingual docstrings
  (short `Summary (UA):` + `Summary (EN):` blocks at the module level, English
  Args/Returns/Raises).
- **Commits.** Conventional Commits (`feat:` / `fix:` / `docs:` / `test:` /
  `chore:` / `refactor:` / `ci:`). One logical change per commit.

## Adding a new automaton kind (rough checklist)

1. Extend `AutomatonType` + model validator in `core/models/`.
2. Add the corresponding `Transition` subclass.
3. Write a `*Simulator` in `core/simulators/` with `step()` / `run()` /
   `accepts()` returning a `Verdict`.
4. Handle it in `core/io/json_io.py` (automatic) and `core/io/jflap.py`.
5. Extend `cli/main.py::_simulator_for` so the CLI dispatches.
6. Add it to `gui/canvas/scene_conversion.py` if it should be editable.
7. Ship at least 10 unit tests — happy path, every validation failure, a JSON
   round-trip. For algorithms, add a Hypothesis property test.

## Filing issues

Use the templates under `.github/ISSUE_TEMPLATE/`. When reporting a bug,
please attach a minimal `.json` or `.jff` automaton plus the exact input that
reproduces the problem.
