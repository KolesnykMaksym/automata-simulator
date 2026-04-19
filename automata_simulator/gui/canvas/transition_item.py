"""QGraphicsItem representing a transition between two states.

Summary (UA): Стрілка-перехід між двома станами. Підтримує self-loop (коло
над станом) та пряму стрілку між різними станами; над стрілкою показується
мітка (символ переходу).
Summary (EN): Arrow-shaped transition with an inline label. Renders a
self-loop when source == target, otherwise a straight arrow between the
boundaries of the two state circles.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QInputDialog,
    QStyleOptionGraphicsItem,
    QWidget,
)

from automata_simulator.gui.canvas.state_item import StateItem

_HIGHLIGHT_COLOUR = QColor("#ff8c00")
_SELECTED_COLOUR = QColor("#3478f6")

_ARROW_HEAD_LENGTH: float = 10.0
_ARROW_HEAD_WIDTH: float = 6.0
_LOOP_RADIUS: float = 22.0


class TransitionItem(QGraphicsItem):
    """Directed edge with a text label between two :class:`StateItem`s."""

    def __init__(self, source: StateItem, target: StateItem, label: str = "") -> None:
        super().__init__()
        self._source = source
        self._target = target
        self._label = label
        self._highlighted = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(-1.0)  # behind states

    # ------------------------------------------------------------ properties
    @property
    def source(self) -> StateItem:
        """Source state."""
        return self._source

    @property
    def target(self) -> StateItem:
        """Target state."""
        return self._target

    @property
    def label(self) -> str:
        """Transition's displayed label (e.g. the read symbol)."""
        return self._label

    def set_label(self, label: str) -> None:
        """Replace the displayed label."""
        self._label = label
        self.update()

    def set_highlighted(self, value: bool) -> None:
        """Visual highlight used by the simulation view."""
        if self._highlighted == value:
            return
        self._highlighted = value
        self.update()

    # ------------------------------------------------------------ geometry
    def boundingRect(self) -> QRectF:  # noqa: N802 — Qt override
        """Envelope the whole stroke plus label in scene coordinates."""
        if self._source is self._target:
            c = self._source.centre()
            pad = _LOOP_RADIUS + 16.0
            return QRectF(c.x() - pad, c.y() - pad * 1.5, pad * 2, pad * 2)
        a = self._source.centre()
        b = self._target.centre()
        left = min(a.x(), b.x()) - 20.0
        top = min(a.y(), b.y()) - 20.0
        width = abs(a.x() - b.x()) + 40.0
        height = abs(a.y() - b.y()) + 40.0
        return QRectF(left, top, width, height)

    # ------------------------------------------------------------ painting
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,  # noqa: ARG002
        widget: QWidget | None = None,
    ) -> None:
        """Draw the line/arrow/loop and render the label."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = widget.palette() if widget is not None else QApplication.palette()
        pen_colour = (
            _HIGHLIGHT_COLOUR
            if self._highlighted
            else palette.windowText().color()
        )
        if self.isSelected():
            pen_colour = _SELECTED_COLOUR
        painter.setPen(QPen(pen_colour, 2.0))
        if self._source is self._target:
            self._paint_self_loop(painter)
        else:
            self._paint_arrow(painter)

    def mouseDoubleClickEvent(  # noqa: N802 — Qt override
        self, event: QGraphicsSceneMouseEvent,
    ) -> None:
        """Open an inline dialog to edit the transition label."""
        new_label, ok = QInputDialog.getText(
            None,
            "Edit transition",
            "Label:",
            text=self._label,
        )
        if ok:
            self.set_label(new_label)
        event.accept()

    def _paint_self_loop(self, painter: QPainter) -> None:
        centre = self._source.centre()
        loop_top = centre.y() - self._source.radius() - _LOOP_RADIUS
        rect = QRectF(
            centre.x() - _LOOP_RADIUS,
            loop_top,
            _LOOP_RADIUS * 2,
            _LOOP_RADIUS * 2,
        )
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawEllipse(rect)
        if self._label:
            painter.setFont(QFont("Helvetica", 10))
            painter.drawText(
                QRectF(rect.x() - 20, loop_top - 20, rect.width() + 40, 20),
                Qt.AlignmentFlag.AlignCenter,
                self._label,
            )

    def _paint_arrow(self, painter: QPainter) -> None:
        a = self._source.centre()
        b = self._target.centre()
        dx = b.x() - a.x()
        dy = b.y() - a.y()
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        # Trim both endpoints to the circles' circumferences.
        ux, uy = dx / dist, dy / dist
        start = QPointF(a.x() + ux * self._source.radius(), a.y() + uy * self._source.radius())
        end = QPointF(b.x() - ux * self._target.radius(), b.y() - uy * self._target.radius())
        painter.drawLine(start, end)
        self._paint_arrow_head(painter, end, ux, uy)
        if self._label:
            mid = QPointF((start.x() + end.x()) / 2.0, (start.y() + end.y()) / 2.0)
            painter.setFont(QFont("Helvetica", 10))
            painter.drawText(
                QRectF(mid.x() - 60, mid.y() - 20, 120, 18),
                Qt.AlignmentFlag.AlignCenter,
                self._label,
            )

    def _paint_arrow_head(
        self, painter: QPainter, tip: QPointF, ux: float, uy: float,
    ) -> None:
        # Perpendicular normal for the arrow wings.
        px, py = -uy, ux
        tail_x = tip.x() - ux * _ARROW_HEAD_LENGTH
        tail_y = tip.y() - uy * _ARROW_HEAD_LENGTH
        wing1 = QPointF(tail_x + px * _ARROW_HEAD_WIDTH, tail_y + py * _ARROW_HEAD_WIDTH)
        wing2 = QPointF(tail_x - px * _ARROW_HEAD_WIDTH, tail_y - py * _ARROW_HEAD_WIDTH)
        head = QPolygonF([tip, wing1, wing2])
        painter.setBrush(QBrush(painter.pen().color()))
        painter.drawPolygon(head)
