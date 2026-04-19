"""Tape visualiser for Turing-machine simulations.

Summary (UA): Віджет, що малює горизонтальну стрічку TM: комірки з символами
і підсвічений курсор головки. Для багатострічкової TM малюється кілька стрічок
одна під одною.
Summary (EN): Widget that renders a (possibly multi-tape) TM tape as a row of
fixed-width cells with a highlighted head position. Updates are pushed from
the simulation controller via ``set_tapes``.
"""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

_CELL_WIDTH: float = 28.0
_CELL_HEIGHT: float = 32.0
_TAPE_GAP: float = 8.0
_MARGIN: float = 10.0


class TapeView(QWidget):
    """Displays one or more TM tapes (cells + head indicator)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tapes: list[tuple[tuple[str, ...], int]] = []
        self.setMinimumHeight(int(_CELL_HEIGHT + _MARGIN * 2))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    # ------------------------------------------------------------ API
    def set_tapes(
        self,
        tapes: Sequence[tuple[Sequence[str], int]],
    ) -> None:
        """Replace the displayed tapes with ``(cells, head_position)`` pairs."""
        self._tapes = [(tuple(cells), head) for cells, head in tapes]
        tape_count = max(1, len(self._tapes))
        needed_height = int(
            _MARGIN * 2 + _CELL_HEIGHT * tape_count + _TAPE_GAP * max(0, tape_count - 1),
        )
        self.setMinimumHeight(needed_height)
        self.update()

    def clear(self) -> None:
        """Remove every tape from the view."""
        self._tapes = []
        self.update()

    def tapes(self) -> list[tuple[tuple[str, ...], int]]:
        """Return the current tape snapshots."""
        return list(self._tapes)

    # ------------------------------------------------------------ painting
    def paintEvent(self, event: object) -> None:  # noqa: N802, ARG002 — Qt override
        """Render every tape row with cells and a highlighted head."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QBrush(QColor("#fafafa")))
        painter.setFont(QFont("Helvetica", 11))
        for row, (cells, head) in enumerate(self._tapes):
            self._paint_row(painter, row, cells, head)

    def _paint_row(
        self,
        painter: QPainter,
        row: int,
        cells: tuple[str, ...],
        head: int,
    ) -> None:
        top = _MARGIN + row * (_CELL_HEIGHT + _TAPE_GAP)
        pen = QPen(QColor("#222222"), 1.0)
        for i, symbol in enumerate(cells):
            rect = QRectF(
                _MARGIN + i * _CELL_WIDTH,
                top,
                _CELL_WIDTH,
                _CELL_HEIGHT,
            )
            is_head = i == head
            painter.setBrush(QBrush(QColor("#ffd85c") if is_head else QColor("#ffffff")))
            painter.setPen(pen)
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, symbol)
