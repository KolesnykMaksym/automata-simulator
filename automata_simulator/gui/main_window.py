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

from PySide6.QtCore import QEvent
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QWidget,
)

from automata_simulator import __version__
from automata_simulator.gui.i18n import Locale, apply_locale


class MainWindow(QMainWindow):
    """Shell for the editor — empty at this stage, GUI wiring lands later."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_locale: Locale = Locale.EN
        self._build_actions()
        self._build_menu_bar()
        self.setStatusBar(QStatusBar(self))
        self.resize(960, 640)
        self.retranslate_ui()

    # ------------------------------------------------------------ menu building
    def _build_actions(self) -> None:
        # File menu
        self.action_new = QAction(self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_open = QAction(self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_save = QAction(self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save_as = QAction(self)
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_quit = QAction(self)
        self.action_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_quit.triggered.connect(self.close)

        # Edit menu
        self.action_undo = QAction(self)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_redo = QAction(self)
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

        # Algorithm menu
        self.action_alg_nfa_to_dfa = QAction(self)
        self.action_alg_enfa_to_nfa = QAction(self)
        self.action_alg_minimise = QAction(self)
        self.action_alg_regex_to_nfa = QAction(self)
        self.action_alg_nfa_to_regex = QAction(self)
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

    # ------------------------------------------------------------ about dialog
    def _show_about(self) -> None:
        title = self.tr("About Automata Simulator")
        description = self.tr(
            "A JFLAP-style educational simulator for DFA, NFA, ε-NFA, Mealy, "
            "Moore, PDA and Turing machines.",
        )
        version_line = self.tr("Version {version}").format(version=__version__)
        QMessageBox.about(self, title, f"{description}\n\n{version_line}")
