"""Light / dark theme palette helpers.

Summary (UA): Перемикання світлої і темної теми через ``QApplication.setPalette``.
Усі графічні елементи canvas читають palette під час paint, тож тема працює
однаково для станів, переходів, стрічки та стеку.
Summary (EN): Light/dark palette helpers. The canvas items read
``QApplication.palette()`` on every paint cycle so theme swaps are instant;
accepting/highlight colours stay fixed for visibility on both themes.
"""

from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class Theme(StrEnum):
    """Supported GUI themes."""

    LIGHT = "light"
    DARK = "dark"


def _light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f7f7f7"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#222222"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#eaeaea"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#222222"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#f0f0f0"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#222222"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#3478f6"))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    return palette


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6e6e6"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#333333"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e6e6e6"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#3a3a3a"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e6e6e6"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#64a4ff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    return palette


def apply_theme(app: QApplication, theme: Theme) -> None:
    """Install the palette for ``theme`` on ``app``."""
    palette = _dark_palette() if theme is Theme.DARK else _light_palette()
    app.setPalette(palette)
