# Automata Simulator

> Сучасний open-source симулятор автоматів — заміна JFLAP для навчання теорії
> формальних мов.
>
> A modern open-source automata simulator — a JFLAP replacement for formal
> language theory courses.

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

- Редактор з drag-and-drop станів і переходів (PySide6).
- Покрокова симуляція з анімацією активних станів, стрічки (TM) і стеку (PDA).
- Алгоритми: `NFA→DFA`, `ε-NFA→NFA`, мінімізація Хопкрофта, Regex↔NFA
  (Томпсон / state elimination), CFG↔PDA, перевірка еквівалентності.
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

### Етап розробки

Проєкт у стадії активної розробки. Поточний етап — **Етап 0 (Bootstrap)** —
див. `CLAUDE.md`, розділ 9.

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

- Drag-and-drop editor for states and transitions (PySide6).
- Step-by-step simulation with animated active states, tape (TM) and stack (PDA).
- Algorithms: `NFA→DFA`, `ε-NFA→NFA`, Hopcroft minimization, Regex↔NFA
  (Thompson / state elimination), CFG↔PDA, equivalence checking.
- Batch testing with CSV/JSON report export.
- JFLAP `.jff` import/export, native JSON format, Graphviz DOT/SVG/PNG.
- Bilingual UI (Ukrainian / English), runtime switchable.
- CLI for headless operation and a Docker image.

### Installation

```bash
pip install automata-simulator
automata-sim        # GUI
automata --help     # CLI
```

### Development status

Active development. Current phase — **Stage 0 (Bootstrap)** — see `CLAUDE.md`,
section 9.

### Development setup

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install
pytest
```

---

## License

MIT — see [LICENSE](LICENSE) (to be added in Stage 16).
