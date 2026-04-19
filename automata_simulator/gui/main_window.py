"""Top-level MainWindow with menu bar and language switcher.

Summary (UA): Головне вікно з меню (Файл / Редагування / Вигляд / Симуляція /
Алгоритми / Довідка) і runtime-перемикачем мови UA↔EN через підменю
"Вигляд → Мова".
Summary (EN): Top-level QMainWindow. The menu bar includes a ``View →
Language`` submenu that hot-swaps the translator. Every user-facing string is
wrapped in ``self.tr(...)`` and re-applied inside ``retranslate_ui()``, which
runs on every ``QEvent.LanguageChange``.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QUndoStack
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QWidget,
)

from automata_simulator import __version__
from automata_simulator.core.io import load_jff, load_json, save_jff, save_json
from automata_simulator.core.models import Automaton
from automata_simulator.gui.canvas import (
    AutomatonView,
    SceneConversionError,
    automaton_to_scene,
    scene_to_automaton,
)
from automata_simulator.gui.dialogs import (
    BatchTestDialog,
    ConvertToDFADialog,
    FAToRegexDialog,
    MinimizeDFADialog,
    RegexToNFADialog,
    RemoveEpsilonDialog,
)
from automata_simulator.gui.i18n import Locale, apply_locale
from automata_simulator.gui.panels import SimulationPanel


def _read_automaton(path: Path) -> Automaton:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json(path)
    if suffix in {".jff", ".xml"}:
        return load_jff(path)
    raise ValueError(f"Unsupported extension: {suffix!r} (use .json, .jff or .xml)")


def _write_automaton(automaton: Automaton, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        save_json(automaton, path)
    elif suffix == ".jff":
        save_jff(automaton, path)
    else:
        raise ValueError(f"Unsupported extension: {suffix!r} (use .json or .jff)")


class MainWindow(QMainWindow):
    """Shell for the editor — empty at this stage, GUI wiring lands later."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_locale: Locale = Locale.EN
        self._current_path: Path | None = None
        self._canvas_view = AutomatonView()
        self.setCentralWidget(self._canvas_view)
        self._undo_stack = QUndoStack(self)
        self._simulation_panel = SimulationPanel(self._canvas_view.automaton_scene)
        self._sim_dock = QDockWidget(self)
        self._sim_dock.setWidget(self._simulation_panel)
        self._sim_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._sim_dock)
        self._build_actions()
        self._build_menu_bar()
        self.setStatusBar(QStatusBar(self))
        self.resize(1120, 720)
        self.retranslate_ui()

    @property
    def canvas_view(self) -> AutomatonView:
        """The central :class:`AutomatonView` widget."""
        return self._canvas_view

    @property
    def simulation_panel(self) -> SimulationPanel:
        """The embedded :class:`SimulationPanel` widget."""
        return self._simulation_panel

    @property
    def undo_stack(self) -> QUndoStack:
        """The editor's QUndoStack (Ctrl+Z / Ctrl+Y)."""
        return self._undo_stack

    # ------------------------------------------------------------ menu building
    def _build_actions(self) -> None:
        # File menu
        self.action_new = QAction(self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.triggered.connect(self._new_file)
        self.action_open = QAction(self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self._open_file)
        self.action_save = QAction(self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self._save_file)
        self.action_save_as = QAction(self)
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.triggered.connect(self._save_file_as)
        self.action_quit = QAction(self)
        self.action_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_quit.triggered.connect(self.close)

        # Edit menu — wire directly into the QUndoStack.
        self.action_undo = self._undo_stack.createUndoAction(self)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_redo = self._undo_stack.createRedoAction(self)
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)

        # View → Language actions (mutually exclusive)
        self.language_group = QActionGroup(self)
        self.language_group.setExclusive(True)
        self.action_lang_en = QAction(self)
        self.action_lang_en.setCheckable(True)
        self.action_lang_en.setChecked(True)
        self.action_lang_en.triggered.connect(lambda: self._switch_locale(Locale.EN))
        self.language_group.addAction(self.action_lang_en)
        self.action_lang_ua = QAction(self)
        self.action_lang_ua.setCheckable(True)
        self.action_lang_ua.triggered.connect(lambda: self._switch_locale(Locale.UA))
        self.language_group.addAction(self.action_lang_ua)

        # Simulation menu
        self.action_sim_run = QAction(self)
        self.action_sim_step = QAction(self)
        self.action_sim_pause = QAction(self)
        self.action_sim_reset = QAction(self)
        self.action_batch_test = QAction(self)
        self.action_batch_test.triggered.connect(self._run_batch_test)

        # Algorithm menu
        self.action_alg_nfa_to_dfa = QAction(self)
        self.action_alg_nfa_to_dfa.triggered.connect(self._run_nfa_to_dfa)
        self.action_alg_enfa_to_nfa = QAction(self)
        self.action_alg_enfa_to_nfa.triggered.connect(self._run_enfa_to_nfa)
        self.action_alg_minimise = QAction(self)
        self.action_alg_minimise.triggered.connect(self._run_minimize)
        self.action_alg_regex_to_nfa = QAction(self)
        self.action_alg_regex_to_nfa.triggered.connect(self._run_regex_to_nfa)
        self.action_alg_nfa_to_regex = QAction(self)
        self.action_alg_nfa_to_regex.triggered.connect(self._run_fa_to_regex)
        self.action_alg_cfg_to_pda = QAction(self)
        self.action_alg_pda_to_cfg = QAction(self)

        # Help menu
        self.action_about = QAction(self)
        self.action_about.triggered.connect(self._show_about)

    def _build_menu_bar(self) -> None:
        menubar = self.menuBar()

        self.menu_file = QMenu(self)
        self.menu_file.addAction(self.action_new)
        self.menu_file.addAction(self.action_open)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_save)
        self.menu_file.addAction(self.action_save_as)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)
        menubar.addMenu(self.menu_file)

        self.menu_edit = QMenu(self)
        self.menu_edit.addAction(self.action_undo)
        self.menu_edit.addAction(self.action_redo)
        menubar.addMenu(self.menu_edit)

        self.menu_view = QMenu(self)
        self.menu_language = QMenu(self.menu_view)
        self.menu_language.addAction(self.action_lang_en)
        self.menu_language.addAction(self.action_lang_ua)
        self.menu_view.addMenu(self.menu_language)
        menubar.addMenu(self.menu_view)

        self.menu_sim = QMenu(self)
        self.menu_sim.addAction(self.action_sim_run)
        self.menu_sim.addAction(self.action_sim_step)
        self.menu_sim.addAction(self.action_sim_pause)
        self.menu_sim.addAction(self.action_sim_reset)
        self.menu_sim.addSeparator()
        self.menu_sim.addAction(self.action_batch_test)
        menubar.addMenu(self.menu_sim)

        self.menu_algorithms = QMenu(self)
        self.menu_algorithms.addAction(self.action_alg_nfa_to_dfa)
        self.menu_algorithms.addAction(self.action_alg_enfa_to_nfa)
        self.menu_algorithms.addAction(self.action_alg_minimise)
        self.menu_algorithms.addSeparator()
        self.menu_algorithms.addAction(self.action_alg_regex_to_nfa)
        self.menu_algorithms.addAction(self.action_alg_nfa_to_regex)
        self.menu_algorithms.addSeparator()
        self.menu_algorithms.addAction(self.action_alg_cfg_to_pda)
        self.menu_algorithms.addAction(self.action_alg_pda_to_cfg)
        menubar.addMenu(self.menu_algorithms)

        self.menu_help = QMenu(self)
        self.menu_help.addAction(self.action_about)
        menubar.addMenu(self.menu_help)

    # ------------------------------------------------------------ locale control
    @property
    def current_locale(self) -> Locale:
        """The currently-active GUI locale."""
        return self._current_locale

    def set_locale(self, locale: Locale) -> None:
        """Public setter (mainly for tests) that mirrors the menu action."""
        if locale is Locale.EN:
            self.action_lang_en.setChecked(True)
        else:
            self.action_lang_ua.setChecked(True)
        self._switch_locale(locale)

    def _switch_locale(self, locale: Locale) -> None:
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            return
        apply_locale(app, locale)
        self._current_locale = locale
        # Qt's installTranslator doesn't reliably emit LanguageChange for a
        # Python-subclassed translator, so re-apply strings explicitly.
        self.retranslate_ui()

    # ------------------------------------------------------------ retranslate
    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 — Qt override
        """Handle Qt events; refresh strings on ``LanguageChange``."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def retranslate_ui(self) -> None:
        """Refresh every user-visible string based on the current locale."""
        self.setWindowTitle(self.tr("Automata Simulator"))
        self.statusBar().showMessage(self.tr("Ready"))
        self._sim_dock.setWindowTitle(self.tr("&Simulation"))
        self._simulation_panel.retranslate_ui()

        self.menu_file.setTitle(self.tr("&File"))
        self.action_new.setText(self.tr("&New"))
        self.action_open.setText(self.tr("&Open…"))
        self.action_save.setText(self.tr("&Save"))
        self.action_save_as.setText(self.tr("Save &As…"))
        self.action_quit.setText(self.tr("&Quit"))

        self.menu_edit.setTitle(self.tr("&Edit"))
        self.action_undo.setText(self.tr("&Undo"))
        self.action_redo.setText(self.tr("&Redo"))

        self.menu_view.setTitle(self.tr("&View"))
        self.menu_language.setTitle(self.tr("&Language"))
        self.action_lang_en.setText(self.tr("English"))
        self.action_lang_ua.setText(self.tr("Ukrainian"))

        self.menu_sim.setTitle(self.tr("&Simulation"))
        self.action_sim_run.setText(self.tr("&Run"))
        self.action_sim_step.setText(self.tr("S&tep"))
        self.action_sim_pause.setText(self.tr("&Pause"))
        self.action_sim_reset.setText(self.tr("R&eset"))
        self.action_batch_test.setText(self.tr("&Batch test…"))

        self.menu_algorithms.setTitle(self.tr("&Algorithms"))
        self.action_alg_nfa_to_dfa.setText(self.tr("NFA → DFA"))
        self.action_alg_enfa_to_nfa.setText(self.tr("ε-NFA → NFA"))
        self.action_alg_minimise.setText(self.tr("Minimise DFA"))
        self.action_alg_regex_to_nfa.setText(self.tr("Regex → NFA"))
        self.action_alg_nfa_to_regex.setText(self.tr("NFA → Regex"))
        self.action_alg_cfg_to_pda.setText(self.tr("CFG → PDA"))
        self.action_alg_pda_to_cfg.setText(self.tr("PDA → CFG"))

        self.menu_help.setTitle(self.tr("&Help"))
        self.action_about.setText(self.tr("&About"))

    # ------------------------------------------------------------ file handlers
    def _new_file(self) -> None:
        """Clear the canvas and forget the current file path."""
        self._canvas_view.automaton_scene.clear_automaton()
        self._undo_stack.clear()
        self._current_path = None
        self.setWindowTitle(self.tr("Automata Simulator"))

    def _open_file(self) -> None:
        """Prompt for a ``.json`` / ``.jff`` file and load it into the scene."""
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Open automaton"),
            str(Path.cwd() / "examples"),
            "Automata (*.json *.jff *.xml);;All files (*)",
        )
        if not path_str:
            return
        self.load_path(Path(path_str))

    def load_path(self, path: Path) -> None:
        """Load an automaton from ``path`` into the scene (public for tests)."""
        try:
            automaton = _read_automaton(path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, self.tr("Open failed"), str(exc))
            return
        automaton_to_scene(automaton, self._canvas_view.automaton_scene)
        self._undo_stack.clear()
        self._current_path = path
        self.setWindowTitle(f"{path.name} — {self.tr('Automata Simulator')}")

    def _save_file(self) -> None:
        if self._current_path is None:
            self._save_file_as()
            return
        self._write_scene_to(self._current_path)

    def _save_file_as(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save automaton"),
            str(self._current_path or Path.cwd() / "automaton.json"),
            "JSON (*.json);;JFLAP (*.jff)",
        )
        if not path_str:
            return
        path = Path(path_str)
        self._write_scene_to(path)
        self._current_path = path
        self.setWindowTitle(f"{path.name} — {self.tr('Automata Simulator')}")

    def _write_scene_to(self, path: Path) -> None:
        automaton = self._current_automaton()
        if automaton is None:
            return
        try:
            _write_automaton(automaton, path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, self.tr("Save failed"), str(exc))

    # ------------------------------------------------------------ algorithms
    def _current_automaton(self) -> Automaton | None:
        try:
            return scene_to_automaton(self._canvas_view.automaton_scene)
        except SceneConversionError as exc:
            QMessageBox.warning(self, self.tr("Scene error"), str(exc))
            return None

    def _apply_automaton(self, automaton: Automaton) -> None:
        automaton_to_scene(automaton, self._canvas_view.automaton_scene)
        self._undo_stack.clear()

    def _run_nfa_to_dfa(self) -> None:
        automaton = self._current_automaton()
        if automaton is None:
            return
        try:
            dialog = ConvertToDFADialog(automaton, self)
        except ValueError as exc:
            QMessageBox.warning(self, self.tr("Unsupported"), str(exc))
            return
        if dialog.exec() and dialog.applied_automaton is not None:
            self._apply_automaton(dialog.applied_automaton)

    def _run_enfa_to_nfa(self) -> None:
        automaton = self._current_automaton()
        if automaton is None:
            return
        try:
            dialog = RemoveEpsilonDialog(automaton, self)
        except ValueError as exc:
            QMessageBox.warning(self, self.tr("Unsupported"), str(exc))
            return
        if dialog.exec() and dialog.applied_automaton is not None:
            self._apply_automaton(dialog.applied_automaton)

    def _run_minimize(self) -> None:
        automaton = self._current_automaton()
        if automaton is None:
            return
        try:
            dialog = MinimizeDFADialog(automaton, self)
        except ValueError as exc:
            QMessageBox.warning(self, self.tr("Unsupported"), str(exc))
            return
        if dialog.exec() and dialog.applied_automaton is not None:
            self._apply_automaton(dialog.applied_automaton)

    def _run_regex_to_nfa(self) -> None:
        dialog = RegexToNFADialog(self)
        if dialog.exec() and dialog.applied_automaton is not None:
            self._apply_automaton(dialog.applied_automaton)

    def _run_fa_to_regex(self) -> None:
        automaton = self._current_automaton()
        if automaton is None:
            return
        try:
            dialog = FAToRegexDialog(automaton, self)
        except ValueError as exc:
            QMessageBox.warning(self, self.tr("Unsupported"), str(exc))
            return
        if dialog.exec() and dialog.applied_automaton is not None:
            self._apply_automaton(dialog.applied_automaton)

    def _run_batch_test(self) -> None:
        dialog = BatchTestDialog(self._canvas_view.automaton_scene, self)
        dialog.exec()

    # ------------------------------------------------------------ about dialog
    def _show_about(self) -> None:
        title = self.tr("About Automata Simulator")
        description = self.tr(
            "A JFLAP-style educational simulator for DFA, NFA, ε-NFA, Mealy, "
            "Moore, PDA and Turing machines.",
        )
        version_line = self.tr("Version {version}").format(version=__version__)
        QMessageBox.about(self, title, f"{description}\n\n{version_line}")
