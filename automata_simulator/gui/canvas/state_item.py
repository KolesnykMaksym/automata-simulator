"""QGraphicsItem representing an automaton state on the canvas.

Summary (UA): Графічний елемент стану: коло з міткою, двошарове коло для
прикінцевого стану, стрілочка для початкового. Перетягується мишею.
Summary (EN): Circle-with-label QGraphicsItem. Draws a double-ring for
accepting states, an incoming arrow stub for the initial state, and is
freely movable by the user.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

_HIGHLIGHT_FILL = QColor("#ffd85c")
_SELECTED_PEN = QColor("#3478f6")

STATE_RADIUS: float = 30.0
_ACCEPTING_INNER_GAP: float = 5.0
_INITIAL_ARROW_LENGTH: float = 18.0


class StateItem(QGraphicsItem):
    """A draggable circular state node."""

    def __init__(self, state_id: str, x: float = 0.0, y: float = 0.0) -> None:
        super().__init__()
        self._state_id = state_id
        self._label = state_id
        self._is_initial = False
        self._is_accepting = False
        self._radius = STATE_RADIUS
        self._highlighted = False
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )
        self.setAcceptHoverEvents(True)

    # ------------------------------------------------------------ properties
    @property
    def state_id(self) -> str:
        """Stable identifier (used as the Automaton State id)."""
        return self._state_id

    def set_state_id(self, new_id: str) -> None:
        """Rename the state; updates the displayed label if it was unchanged."""
        if self._label == self._state_id:
            self._label = new_id
        self._state_id = new_id
        self.update()

    @property
    def label(self) -> str:
        """Human-friendly label (defaults to ``state_id``)."""
        return self._label

    def set_label(self, label: str) -> None:
        """Change the state's visible label."""
        self._label = label
        self.update()

    @property
    def is_initial(self) -> bool:
        """Whether this state is the automaton's initial state."""
        return self._is_initial

    def set_initial(self, value: bool) -> None:
        """Mark this state as (not) the initial state."""
        if self._is_initial == value:
            return
        self._is_initial = value
        self.update()

    @property
    def is_accepting(self) -> bool:
        """Whether this state is accepting."""
        return self._is_accepting

    def set_accepting(self, value: bool) -> None:
        """Mark this state as (not) accepting."""
        if self._is_accepting == value:
            return
        self._is_accepting = value
        self.update()

    def set_highlighted(self, value: bool) -> None:
        """Highlight the state (used by the simulation view)."""
        if self._highlighted == value:
            return
        self._highlighted = value
        self.update()

    # ------------------------------------------------------------ geometry
    def boundingRect(self) -> QRectF:  # noqa: N802 — Qt override
        """Include the initial-arrow stub and a small stroke margin."""
        margin = 4.0
        left = -self._radius - margin
        if self._is_initial:
            left -= _INITIAL_ARROW_LENGTH
        width = (self._radius + margin) - left
        height = (self._radius + margin) * 2
        return QRectF(left, -self._radius - margin, width, height)

    def centre(self) -> QPointF:
        """The centre point of the state in scene coordinates."""
        return self.scenePos()

    def radius(self) -> float:
        """Outer radius of the circle."""
        return self._radius

    # ------------------------------------------------------------ painting
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,  # noqa: ARG002 — Qt callback shape
        widget: QWidget | None = None,
    ) -> None:
        """Draw the state circle, label, optional double ring and initial arrow."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = widget.palette() if widget is not None else QApplication.palette()
        base_fill = palette.base().color()
        text_colour = palette.windowText().color()
        outer = QRectF(
            -self._radius,
            -self._radius,
            self._radius * 2,
            self._radius * 2,
        )
        fill_colour = _HIGHLIGHT_FILL if self._highlighted else base_fill
        painter.setBrush(QBrush(fill_colour))
        pen = QPen(text_colour, 2.0)
        if self.isSelected():
            pen.setColor(_SELECTED_PEN)
            pen.setWidthF(2.8)
        painter.setPen(pen)
        painter.drawEllipse(outer)
        if self._is_accepting:
            inner_r = self._radius - _ACCEPTING_INNER_GAP
            painter.drawEllipse(QRectF(-inner_r, -inner_r, inner_r * 2, inner_r * 2))
        if self._is_initial:
            self._draw_initial_arrow(painter, text_colour)
        painter.setPen(text_colour)
        painter.setFont(QFont("Helvetica", 11))
        painter.drawText(outer, Qt.AlignmentFlag.AlignCenter, self._label)

    def _draw_initial_arrow(self, painter: QPainter, colour: QColor) -> None:
        tail_x = -self._radius - _INITIAL_ARROW_LENGTH
        tip_x = -self._radius
        painter.setPen(QPen(colour, 2.0))
        painter.drawLine(QPointF(tail_x, 0.0), QPointF(tip_x, 0.0))
        arrow = QPolygonF(
            [
                QPointF(tip_x, 0.0),
                QPointF(tip_x - 8.0, -5.0),
                QPointF(tip_x - 8.0, 5.0),
            ],
        )
        painter.setBrush(QBrush(colour))
        painter.drawPolygon(arrow)

    # ------------------------------------------------------------ interaction
    def mouseDoubleClickEvent(  # noqa: N802 — Qt override
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        """Toggle accepting on double-click (shortcut for the context menu)."""
        self.set_accepting(not self._is_accepting)
        event.accept()
