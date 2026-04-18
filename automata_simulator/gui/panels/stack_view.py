"""Stack visualiser for PDA simulations.

Summary (UA): Віджет малює стек PDA вертикально (верх стека — угорі).
Оновлення — через ``set_stack``.
Summary (EN): Vertical stack renderer for PDAs. The top of the stack is
drawn at the top of the widget. Stack contents are pushed in from the
simulation controller via ``set_stack``.
"""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

_CELL_WIDTH: float = 60.0
_CELL_HEIGHT: float = 28.0
_MARGIN: float = 10.0


class StackView(QWidget):
    """Vertical stack display (``stack[-1]`` on top)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stack: tuple[str, ...] = ()
        self.setMinimumSize(int(_CELL_WIDTH + _MARGIN * 2), 120)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    # ------------------------------------------------------------ API
    def set_stack(self, stack: Sequence[str]) -> None:
        """Replace the stack contents (``stack[-1]`` is top)."""
        self._stack = tuple(stack)
        self.update()

    def clear(self) -> None:
        """Empty the displayed stack."""
        self._stack = ()
        self.update()

    def stack(self) -> tuple[str, ...]:
        """Return the current stack snapshot."""
        return self._stack

    # ------------------------------------------------------------ painting
    def paintEvent(self, event: object) -> None:  # noqa: N802, ARG002 — Qt override
        """Render cells bottom-to-top so the stack top appears at the top."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QBrush(QColor("#fafafa")))
        painter.setFont(QFont("Helvetica", 11))
        count = len(self._stack)
        if count == 0:
            painter.setPen(QColor("#666666"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "⌀")
            return
        pen = QPen(QColor("#222222"), 1.0)
        centre_x = self.width() / 2.0
        for i, symbol in enumerate(self._stack):
            # Top of stack is index -1 → drawn at the top row (y smallest).
            row_from_top = count - 1 - i
            rect = QRectF(
                centre_x - _CELL_WIDTH / 2.0,
                _MARGIN + row_from_top * _CELL_HEIGHT,
                _CELL_WIDTH,
                _CELL_HEIGHT,
            )
            is_top = i == count - 1
            painter.setBrush(QBrush(QColor("#cfe7ff") if is_top else QColor("#ffffff")))
            painter.setPen(pen)
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, symbol)
