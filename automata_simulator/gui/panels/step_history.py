"""Scrollable history of simulation steps.

Summary (UA): Панель історії кроків симуляції: список з рядка на кожен крок.
Приймає готовий список рядків; сам перетворення step → рядок залишається в
викликачі.
Summary (EN): Read-only list widget that displays one line per simulator
step. The caller decides how each step is stringified and pushes the result
via ``set_steps`` / ``append_step``.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy, QWidget


class StepHistoryView(QListWidget):
    """Displays one row per simulation step (strings supplied by the caller)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_steps(self, lines: Iterable[str]) -> None:
        """Replace the contents with ``lines``."""
        self.clear()
        for line in lines:
            self.addItem(QListWidgetItem(line))

    def append_step(self, line: str) -> None:
        """Append one new step line and scroll it into view."""
        item = QListWidgetItem(line)
        self.addItem(item)
        self.scrollToBottom()

    def step_lines(self) -> list[str]:
        """Return every displayed line in order."""
        return [self.item(i).text() for i in range(self.count())]
