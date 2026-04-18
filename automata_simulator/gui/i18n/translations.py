"""English → Ukrainian translations for the GUI.

Summary (UA): Словник перекладу з англійської на українську для всіх рядків
GUI. Використовується ``DictTranslator`` для runtime-перемикання мов без
збірки ``.qm``-файлів.
Summary (EN): Source-to-Ukrainian dictionary used by the DictTranslator. We
avoid compiling ``.qm`` files (lrelease dependency) — translations live
directly in Python and are hot-swappable at runtime.
"""

from __future__ import annotations

TRANSLATIONS_UA: dict[str, str] = {
    # Application
    "Automata Simulator": "Симулятор автоматів",
    "Ready": "Готово",
    # File menu
    "&File": "&Файл",
    "&New": "&Новий",
    "&Open…": "&Відкрити…",
    "&Save": "&Зберегти",
    "Save &As…": "Зберегти &як…",
    "&Quit": "В&ийти",
    # Edit menu
    "&Edit": "&Редагування",
    "&Undo": "Ска&сувати",
    "&Redo": "По&вторити",
    # View menu
    "&View": "&Вигляд",
    "&Language": "&Мова",
    "English": "English",
    "Ukrainian": "Українська",
    # Simulation menu
    "&Simulation": "&Симуляція",
    "&Run": "З&апустити",
    "S&tep": "&Крок",
    "&Pause": "&Пауза",
    "R&eset": "С&кинути",
    "Speed": "Швидкість",
    "Speed: {x:.1f}×": "Швидкість: {x:.1f}×",
    "Input string…": "Вхідний рядок…",
    "Verdict: {v}": "Вердикт: {v}",
    "Error: {msg}": "Помилка: {msg}",
    "Simulation of {kind} automata is not yet supported in the GUI": (
        "Симуляція автоматів {kind} поки не підтримується в GUI"
    ),
    # Algorithms menu
    "&Algorithms": "&Алгоритми",
    "NFA → DFA": "NFA → DFA",
    "ε-NFA → NFA": "ε-NFA → NFA",
    "Minimise DFA": "Мінімізувати DFA",
    "Regex → NFA": "Regex → NFA",
    "NFA → Regex": "NFA → Regex",
    "CFG → PDA": "CFG → PDA",
    "PDA → CFG": "PDA → CFG",
    # Help menu
    "&Help": "&Довідка",
    "&About": "&Про програму",
    "About Automata Simulator": "Про Symulator автоматів",
    (
        "A JFLAP-style educational simulator for DFA, NFA, ε-NFA, Mealy, "
        "Moore, PDA and Turing machines."
    ): (
        "Навчальний симулятор у стилі JFLAP для DFA, NFA, ε-NFA, автоматів "
        "Мілі та Мура, PDA і машин Тьюрінга."
    ),
    "Version {version}": "Версія {version}",
}
