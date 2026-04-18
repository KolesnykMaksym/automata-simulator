"""Modal dialogs for running transformations against the current scene.

Summary (UA): Діалоги алгоритмів: NFA→DFA, мінімізація DFA, Regex↔NFA.
Кожен показує результат (структуру нового автомата, таблицю відповідностей,
фінальний регекс) і має кнопку "Apply", що повертає результат до викликача.
Summary (EN): Small QDialog modals that run a core algorithm on the scene's
automaton and display a preview — new state/transition counts, class/subset
mapping, Thompson-built NFA, or state-elimination regex — plus an Apply
button that passes the resulting :class:`Automaton` back through
``applied_automaton``.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from automata_simulator.core.algorithms import (
    fa_to_regex,
    minimize_dfa,
    nfa_to_dfa,
    regex_to_nfa,
    remove_epsilon_transitions,
)
from automata_simulator.core.models import Automaton, AutomatonType
from automata_simulator.core.regex import format_regex, parse_regex


class _AlgorithmDialog(QDialog):
    """Common base — stores the ``applied_automaton`` until the user accepts."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self._applied: Automaton | None = None

    @property
    def applied_automaton(self) -> Automaton | None:
        """The automaton the user wants to apply, or ``None`` until accepted."""
        return self._applied


def _summary_lines(automaton: Automaton) -> list[str]:
    return [
        f"Type: {automaton.type.value}",
        f"States: {len(automaton.states)}",
        f"Alphabet: {{{', '.join(automaton.alphabet)}}}",
        f"Transitions: {len(automaton.transitions)}",
        f"Initial: {automaton.initial_state}",
        f"Accepting: {{{', '.join(automaton.accepting_states)}}}",
    ]


class ConvertToDFADialog(_AlgorithmDialog):
    """NFA / ε-NFA → DFA via subset construction, with mapping preview."""

    def __init__(self, source: Automaton, parent: QWidget | None = None) -> None:
        super().__init__("Convert NFA → DFA", parent)
        if source.type not in (AutomatonType.NFA, AutomatonType.EPSILON_NFA):
            raise ValueError(
                f"ConvertToDFADialog expects NFA/ε-NFA, got {source.type.value!r}",
            )
        result = nfa_to_dfa(source)
        self._result = result.dfa

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Resulting DFA:"))
        for line in _summary_lines(result.dfa):
            layout.addWidget(QLabel(line))
        layout.addWidget(QLabel("Subset mapping (DFA state → NFA subset):"))
        self._mapping_list = QListWidget()
        for dfa_id, subset in sorted(result.subset_by_state.items()):
            entry = f"{dfa_id}  ←  {{{', '.join(sorted(subset))}}}"
            self._mapping_list.addItem(QListWidgetItem(entry))
        layout.addWidget(self._mapping_list)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel,
        )
        apply_btn = buttons.button(QDialogButtonBox.StandardButton.Apply)
        apply_btn.clicked.connect(self._on_apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_apply(self) -> None:
        self._applied = self._result
        self.accept()


class MinimizeDFADialog(_AlgorithmDialog):
    """DFA → minimised DFA via Hopcroft with equivalence-class preview."""

    def __init__(self, source: Automaton, parent: QWidget | None = None) -> None:
        super().__init__("Minimise DFA", parent)
        if source.type is not AutomatonType.DFA:
            raise ValueError(
                f"MinimizeDFADialog expects a DFA, got {source.type.value!r}",
            )
        result = minimize_dfa(source)
        self._result = result.dfa

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                f"Minimised {len(source.states)} → {len(result.dfa.states)} states.",
            ),
        )
        for line in _summary_lines(result.dfa):
            layout.addWidget(QLabel(line))
        layout.addWidget(QLabel("Equivalence classes (new state → original states):"))
        self._class_list = QListWidget()
        for new_id, block in sorted(result.equivalence_classes.items()):
            entry = f"{new_id}  ←  {{{', '.join(sorted(block))}}}"
            self._class_list.addItem(QListWidgetItem(entry))
        layout.addWidget(self._class_list)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._on_apply,
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_apply(self) -> None:
        self._applied = self._result
        self.accept()


class RegexToNFADialog(_AlgorithmDialog):
    """Accept a regex string and build an ε-NFA via Thompson's construction."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Regex → NFA", parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Regular expression:"))
        self._regex_edit = QLineEdit()
        self._regex_edit.setPlaceholderText("e.g. (a|b)*abb")
        layout.addWidget(self._regex_edit)
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._on_apply,
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_apply(self) -> None:
        source = self._regex_edit.text().strip()
        if not source:
            self._status_label.setText("Enter a regular expression first.")
            return
        try:
            ast = parse_regex(source)
        except ValueError as exc:
            self._status_label.setText(str(exc))
            return
        nfa = regex_to_nfa(ast, name=f"regex-{source}")
        self._applied = nfa
        self.accept()


class FAToRegexDialog(_AlgorithmDialog):
    """Convert the scene's FA to a regular expression via state elimination."""

    def __init__(self, source: Automaton, parent: QWidget | None = None) -> None:
        super().__init__("NFA → Regex", parent)
        if source.type not in (
            AutomatonType.DFA,
            AutomatonType.NFA,
            AutomatonType.EPSILON_NFA,
        ):
            raise ValueError(
                f"FAToRegexDialog expects a DFA/NFA/ε-NFA, got {source.type.value!r}",
            )
        regex_node = fa_to_regex(source)
        self._regex_text = format_regex(regex_node)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Resulting regular expression:"))
        text_view = QPlainTextEdit()
        text_view.setReadOnly(True)
        text_view.setPlainText(self._regex_text)
        layout.addWidget(text_view)
        layout.addWidget(
            QLabel(
                "Apply will replace the scene with an ε-NFA built from this regex.",
            ),
        )
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._on_apply,
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def regex_text(self) -> str:
        """The canonical string form of the produced regex."""
        return self._regex_text

    def _on_apply(self) -> None:
        ast = parse_regex(self._regex_text)
        self._applied = regex_to_nfa(ast, name="regex-roundtrip")
        self.accept()


class RemoveEpsilonDialog(_AlgorithmDialog):
    """ε-NFA → NFA via ε-closure folding, with closure preview."""

    def __init__(self, source: Automaton, parent: QWidget | None = None) -> None:
        super().__init__("ε-NFA → NFA", parent)
        if source.type is not AutomatonType.EPSILON_NFA:
            raise ValueError(
                f"RemoveEpsilonDialog expects ε-NFA, got {source.type.value!r}",
            )
        result = remove_epsilon_transitions(source)
        self._result = result.nfa

        layout = QVBoxLayout(self)
        for line in _summary_lines(result.nfa):
            layout.addWidget(QLabel(line))
        layout.addWidget(QLabel("ε-closure per state:"))
        self._closure_list = QListWidget()
        for sid, closure in sorted(result.closure_by_state.items()):
            entry = f"{sid}  →  {{{', '.join(sorted(closure))}}}"
            self._closure_list.addItem(QListWidgetItem(entry))
        layout.addWidget(self._closure_list)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._on_apply,
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_apply(self) -> None:
        self._applied = self._result
        self.accept()
