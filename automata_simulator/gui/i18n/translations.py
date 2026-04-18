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
    "&Batch test…": "&Пакетне тестування…",
    "Batch test": "Пакетне тестування",
    "One input string per line…": "Один вхідний рядок на рядок…",
    "Load file…": "Завантажити файл…",
    "Run": "Запустити",
    "Export CSV": "Експорт CSV",
    "Export JSON": "Експорт JSON",
    "Input": "Вхід",
    "Verdict": "Вердикт",
    "Accepted": "Прийнято",
    "Time (ms)": "Час (мс)",
    "Input strings:": "Вхідні рядки:",
    "No results yet.": "Ще немає результатів.",
    "Tested {n} strings — {a} accepted, {r} rejected.": (
        "Протестовано {n} рядків — {a} прийнято, {r} відхилено."
    ),
    "Load strings file": "Завантажити файл рядків",
    "Export report": "Експорт звіту",
    "No data": "Немає даних",
    "Run a batch first.": "Спочатку запустіть пакетне тестування.",
    "Scene error": "Помилка сцени",
    "Unsupported": "Не підтримується",
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
