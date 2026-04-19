# Automata Simulator

> Сучасний open-source симулятор автоматів — заміна JFLAP для навчання
> теорії формальних мов.
>
> A modern open-source automata simulator — a JFLAP replacement for formal
> language theory courses.

[![CI](https://github.com/KolesnykMaksym/automata-simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/KolesnykMaksym/automata-simulator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

---

## 🇺🇦 Українською

**Automata Simulator** — десктоп-додаток і бібліотека для симуляції,
візуалізації та трансформації класичних моделей автоматів:

- **DFA** — детермінований скінченний автомат
- **NFA / ε-NFA** — недетермінований скінченний автомат (з ε-переходами)
- **Mealy / Moore** — перетворювачі з виходом на переході / в стані
- **PDA** — автомат з магазинною пам'яттю (детермінований та недетермінований)
- **TM** — машина Тьюрінга (1-стрічкова та багатострічкова)

### Можливості

- Drag-and-drop редактор із темною темою (PySide6).
- Покрокова симуляція з анімацією активних станів, стрічки (TM) і стеку (PDA).
- Трекпад-first навігація: pinch-to-zoom, двопальцевий свайп — пан.
- Ліва панель-бібліотека зі всіма відкритими автоматами + прикладами.
- Швидкі тест-рядки (preset inputs) для кожного типу автомата.
- Алгоритми: `NFA→DFA`, `ε-NFA→NFA`, мінімізація Хопкрофта, Regex↔NFA
  (Томпсон / state elimination), CFG↔PDA.
- Пакетне тестування з експортом CSV/JSON-звітів.
- Імпорт/експорт JFLAP `.jff`, власний JSON, Graphviz DOT/SVG/PNG.
- Двомовний UI (українська / англійська), runtime-перемикач.
- CLI для headless-режиму та Docker-образ.

### Встановлення

```bash
pip install automata-simulator
automata-sim        # GUI
automata --help     # CLI
```

### Гарячі клавіші GUI

| Дія | macOS | Linux / Windows |
|---|---|---|
| Відкрити | ⌘O | Ctrl+O |
| Зберегти | ⌘S | Ctrl+S |
| Вмістити у вікно | Ctrl+9 | Ctrl+9 |
| Збільшити / Зменшити | ⌘= / ⌘- | Ctrl+= / Ctrl+- |
| 100% масштаб | Ctrl+0 | Ctrl+0 |
| Undo / Redo | ⌘Z / ⇧⌘Z | Ctrl+Z / Ctrl+Y |
| Вийти | ⌘Q | Ctrl+Q |

---

## 🇬🇧 English

**Automata Simulator** is a desktop application and Python library for
simulating, visualising and transforming the classical automaton models:

- **DFA** — deterministic finite automaton
- **NFA / ε-NFA** — non-deterministic finite automaton (with ε-transitions)
- **Mealy / Moore** — transducers (output on transition / in state)
- **PDA** — pushdown automaton (deterministic and non-deterministic)
- **TM** — Turing machine (single-tape and multi-tape)

### Features

- Drag-and-drop editor with light/dark themes (PySide6).
- Step-by-step simulation with animated active states, tape (TM) and stack (PDA).
- Trackpad-first navigation: pinch-to-zoom, two-finger swipe pans.
- Left library dock listing opened files + bundled examples.
- Quick-pick test strings per automaton kind.
- Algorithms: `NFA→DFA`, `ε-NFA→NFA`, Hopcroft minimization, Regex↔NFA
  (Thompson / state elimination), CFG↔PDA.
- Batch testing with CSV/JSON report export.
- JFLAP `.jff` import/export, native JSON format, Graphviz DOT/SVG/PNG.
- Bilingual UI (Ukrainian / English), runtime switchable.
- CLI for headless operation and a Docker image.

### Install

```bash
pip install automata-simulator
automata-sim        # GUI
automata --help     # CLI
```

### CLI quick reference

```bash
automata simulate examples/dfa_contains_abb.json -i "aabbabb"
automata simulate examples/dfa_contains_abb.json -i "aabbabb" --step
automata convert examples/nfa_ends_in_abb.json --to dfa -o dfa.json
automata minimize dfa.json -o min.json
automata batch-test examples/pda_a_n_b_n.json \
    --strings tests.txt --report report.csv
automata export dfa.json --format dot -o diagram.dot
```

### Development setup

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install
pytest
mypy
```

Docs site (`mkdocs serve`), Docker build (`docker build -t automata-simulator .`)
and PyInstaller bundles (`pyinstaller packaging/automata-sim.spec --clean`) are
all wired through GitHub Actions — see
[`.github/workflows/`](.github/workflows/).

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide.

---

## License

MIT — see [LICENSE](LICENSE).
