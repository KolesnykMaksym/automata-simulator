"""MainWindow smoke and i18n tests (pytest-qt)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("pytestqt")

from pathlib import Path

from PySide6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot

from automata_simulator.gui.i18n import Locale
from automata_simulator.gui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    w = MainWindow()
    qtbot.addWidget(w)
    return w


class TestMainWindowStructure:
    def test_title_is_english_by_default(self, window: MainWindow) -> None:
        assert window.windowTitle() == "Automata Simulator"

    def test_has_six_top_level_menus(self, window: MainWindow) -> None:
        # File, Edit, View, Simulation, Algorithms, Help.
        menus = [a.menu() for a in window.menuBar().actions() if a.menu() is not None]
        assert len(menus) == 6

    def test_language_submenu_has_both_locales(self, window: MainWindow) -> None:
        actions = window.menu_language.actions()
        texts = {a.text() for a in actions}
        assert "English" in texts
        assert "Ukrainian" in texts

    def test_default_locale_is_english(self, window: MainWindow) -> None:
        assert window.current_locale is Locale.EN
        assert window.action_lang_en.isChecked()
        assert not window.action_lang_ua.isChecked()


class TestFileLoad:
    def test_load_path_populates_scene(self, window: MainWindow) -> None:
        window.load_path(Path("examples/dfa_contains_abb.json"))
        ids = {s.state_id for s in window.canvas_view.automaton_scene.state_items()}
        assert ids == {"q0", "q1", "q2", "q3"}
        assert "dfa_contains_abb.json" in window.windowTitle()

    def test_load_path_on_missing_file_is_graceful(
        self,
        window: MainWindow,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # QMessageBox.warning would run a modal loop; stub it out.
        def _swallow_warning(*_args: object, **_kw: object) -> QMessageBox.StandardButton:
            return QMessageBox.StandardButton.Ok

        monkeypatch.setattr(QMessageBox, "warning", _swallow_warning)
        window.load_path(Path("/does/not/exist.json"))
        # Scene remains empty.
        assert window.canvas_view.automaton_scene.state_items() == []


class TestLanguageSwitch:
    def test_switching_to_ukrainian_updates_title(self, window: MainWindow) -> None:
        window.set_locale(Locale.UA)
        assert window.current_locale is Locale.UA
        # Title should now be the Ukrainian translation.
        assert window.windowTitle() == "Симулятор автоматів"

    def test_switching_to_ukrainian_updates_menu_text(self, window: MainWindow) -> None:
        window.set_locale(Locale.UA)
        # "&File" mnemonic stripped from display, but translation keeps it.
        assert "Файл" in window.menu_file.title()

    def test_switching_back_restores_english(self, window: MainWindow) -> None:
        window.set_locale(Locale.UA)
        window.set_locale(Locale.EN)
        assert window.windowTitle() == "Automata Simulator"
        assert window.action_lang_en.isChecked()
