"""QGraphicsView for the automaton editor — trackpad-friendly navigation.

Summary (UA): Перегляд сцени автомата з коректною підтримкою жестів трекпада
(pinch-to-zoom, двопальцевий свайп — панорамування) та кнопками/методами
zoom_in / zoom_out / fit_in_view.
Summary (EN): Wraps :class:`AutomatonScene` in a QGraphicsView with
first-class trackpad support — pinch native gestures zoom, two-finger swipes
(wheel events without Ctrl) pan, Ctrl+wheel zooms. Public ``zoom_in`` /
``zoom_out`` / ``fit_in_view`` drive the View menu and toolbar.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QNativeGestureEvent, QPainter, QWheelEvent
from PySide6.QtWidgets import QGraphicsView, QWidget

from automata_simulator.gui.canvas.scene import AutomatonScene

_ZOOM_IN_FACTOR: float = 1.15
_ZOOM_OUT_FACTOR: float = 1.0 / _ZOOM_IN_FACTOR
_MIN_ZOOM: float = 0.25
_MAX_ZOOM: float = 4.0
_FIT_MARGIN: float = 40.0


class AutomatonView(QGraphicsView):
    """Zoomable view with trackpad-native pan and pinch-to-zoom."""

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
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.SmartViewportUpdate,
        )
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Let native gestures reach this widget (macOS pinch etc.).
        self.grabGesture(Qt.GestureType.PinchGesture)
        self._zoom: float = 1.0

    @property
    def automaton_scene(self) -> AutomatonScene:
        """The underlying :class:`AutomatonScene`."""
        return self._scene

    @property
    def zoom_factor(self) -> float:
        """Current cumulative zoom factor (1.0 = no zoom)."""
        return self._zoom

    # ------------------------------------------------------------ public zoom API
    def zoom_in(self) -> None:
        """Zoom in by one step (keyboard shortcut / toolbar button)."""
        self._apply_zoom(_ZOOM_IN_FACTOR)

    def zoom_out(self) -> None:
        """Zoom out by one step (keyboard shortcut / toolbar button)."""
        self._apply_zoom(_ZOOM_OUT_FACTOR)

    def reset_zoom(self) -> None:
        """Return to 1.0× zoom (no scaling)."""
        if self._zoom == 1.0:
            return
        self.resetTransform()
        self._zoom = 1.0

    def fit_in_view(self) -> None:
        """Scale + translate so every item fits within the viewport."""
        items_rect = self._scene.itemsBoundingRect()
        if items_rect.isEmpty():
            self.reset_zoom()
            return
        margins = items_rect.adjusted(
            -_FIT_MARGIN, -_FIT_MARGIN, _FIT_MARGIN, _FIT_MARGIN,
        )
        self.fitInView(margins, Qt.AspectRatioMode.KeepAspectRatio)
        # Recompute cumulative zoom from the transform.
        self._zoom = self.transform().m11()

    # ------------------------------------------------------------ events
    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 — Qt override
        """Ctrl+wheel zooms; plain wheel / 2-finger swipe pans (default)."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y() or event.pixelDelta().y()
            self._apply_zoom(_ZOOM_IN_FACTOR if delta > 0 else _ZOOM_OUT_FACTOR)
            event.accept()
            return
        super().wheelEvent(event)

    def event(self, event: QEvent) -> bool:
        """Intercept native pinch gestures for zooming."""
        if (
            event.type() == QEvent.Type.NativeGesture
            and isinstance(event, QNativeGestureEvent)
            and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture
        ):
            # ``value()`` is a signed zoom increment (~ -1..1 per step).
            factor = 1.0 + float(event.value())
            if factor > 0:
                self._apply_zoom(factor)
            event.accept()
            return True
        return super().event(event)

    # ------------------------------------------------------------ internals
    def _apply_zoom(self, factor: float) -> None:
        new_zoom = self._zoom * factor
        if new_zoom < _MIN_ZOOM or new_zoom > _MAX_ZOOM:
            return
        self.scale(factor, factor)
        self._zoom = new_zoom
