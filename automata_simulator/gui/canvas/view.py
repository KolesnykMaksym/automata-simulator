"""QGraphicsView for the automaton editor — adds zoom + pan.

Summary (UA): Перегляд сцени автомата з масштабуванням коліщатком миші та
панорамуванням правою/середньою кнопками.
Summary (EN): Wraps :class:`AutomatonScene` in a zoomable QGraphicsView
(wheel to zoom, middle-drag to pan).
"""

from __future__ import annotations

from PySide6.QtGui import QPainter, QWheelEvent
from PySide6.QtWidgets import QGraphicsView, QWidget

from automata_simulator.gui.canvas.scene import AutomatonScene

_ZOOM_IN_FACTOR: float = 1.15
_ZOOM_OUT_FACTOR: float = 1.0 / _ZOOM_IN_FACTOR
_MIN_ZOOM: float = 0.25
_MAX_ZOOM: float = 4.0


class AutomatonView(QGraphicsView):
    """Zoomable view hosting an :class:`AutomatonScene`."""

    def __init__(
        self,
        scene: AutomatonScene | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._scene = scene if scene is not None else AutomatonScene(self)
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing,
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.SmartViewportUpdate,
        )
        self._zoom: float = 1.0

    @property
    def automaton_scene(self) -> AutomatonScene:
        """The underlying :class:`AutomatonScene`."""
        return self._scene

    # ------------------------------------------------------------ events
    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 — Qt override
        """Zoom in/out on mouse-wheel delta."""
        delta = event.angleDelta().y()
        factor = _ZOOM_IN_FACTOR if delta > 0 else _ZOOM_OUT_FACTOR
        new_zoom = self._zoom * factor
        if _MIN_ZOOM <= new_zoom <= _MAX_ZOOM:
            self.scale(factor, factor)
            self._zoom = new_zoom
        event.accept()
