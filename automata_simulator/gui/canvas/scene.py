"""QGraphicsScene that tracks states and transitions.

Summary (UA): Сцена редактора автомата. Подвійний клік на порожньому місці
створює новий стан; Shift+drag від стану до стану — додає перехід.
Summary (EN): QGraphicsScene managing the editor's state/transition items.
Double-click on empty canvas adds a new state; Shift-drag between two states
creates a transition; context-menu on a state toggles initial/accepting.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsSceneContextMenuEvent,
    QGraphicsSceneMouseEvent,
    QInputDialog,
    QMenu,
    QWidget,
)

from automata_simulator.gui.canvas.state_item import StateItem
from automata_simulator.gui.canvas.transition_item import TransitionItem


class AutomatonScene(QGraphicsScene):
    """Editor scene holding :class:`StateItem`s and :class:`TransitionItem`s."""

    structure_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSceneRect(QRectF(-600.0, -400.0, 1200.0, 800.0))
        self._state_counter = itertools.count()
        self._transitions: list[TransitionItem] = []
        self._pending_source: StateItem | None = None
        self._draft_line: QGraphicsLineItem | None = None

    # ------------------------------------------------------------ queries
    def state_items(self) -> list[StateItem]:
        """Return every :class:`StateItem` currently on the scene."""
        return [it for it in self.items() if isinstance(it, StateItem)]

    def transition_items(self) -> list[TransitionItem]:
        """Return every :class:`TransitionItem` currently on the scene."""
        return list(self._transitions)

    def initial_state(self) -> StateItem | None:
        """Return the state currently flagged as initial, or ``None``."""
        return next((s for s in self.state_items() if s.is_initial), None)

    # ------------------------------------------------------------ mutation
    def add_state(self, x: float, y: float, *, state_id: str | None = None) -> StateItem:
        """Create and register a new state at ``(x, y)``."""
        if state_id is None:
            state_id = self._fresh_state_id()
        item = StateItem(state_id, x, y)
        self.addItem(item)
        self.structure_changed.emit()
        return item

    def add_transition(
        self,
        source: StateItem,
        target: StateItem,
        label: str = "",
    ) -> TransitionItem:
        """Create and register a transition from ``source`` to ``target``."""
        tr = TransitionItem(source, target, label)
        self.addItem(tr)
        self._transitions.append(tr)
        self.structure_changed.emit()
        return tr

    def remove_state(self, state: StateItem) -> None:
        """Remove a state and every transition touching it."""
        for tr in [t for t in self._transitions if state in (t.source, t.target)]:
            self._transitions.remove(tr)
            self.removeItem(tr)
        self.removeItem(state)
        self.structure_changed.emit()

    def remove_transition(self, transition: TransitionItem) -> None:
        """Remove a single transition."""
        if transition in self._transitions:
            self._transitions.remove(transition)
        self.removeItem(transition)
        self.structure_changed.emit()

    def set_initial(self, state: StateItem) -> None:
        """Set ``state`` as the (unique) initial state."""
        for existing in self.state_items():
            existing.set_initial(existing is state)
        self.structure_changed.emit()

    # ------------------------------------------------------------ helpers
    def _fresh_state_id(self) -> str:
        existing = {s.state_id for s in self.state_items()}
        while True:
            candidate = f"q{next(self._state_counter)}"
            if candidate not in existing:
                return candidate

    def _state_at(self, pos: QPointF) -> StateItem | None:
        for item in self.items(pos):
            if isinstance(item, StateItem):
                return item
        return None

    # ------------------------------------------------------------ events
    def mouseDoubleClickEvent(  # noqa: N802 — Qt override
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        """Double-click on empty canvas creates a new state."""
        if self._state_at(event.scenePos()) is None:
            self.add_state(event.scenePos().x(), event.scenePos().y())
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(  # noqa: N802 — Qt override
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        """Shift-click on a state starts a transition drag."""
        if (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            source = self._state_at(event.scenePos())
            if source is not None:
                self._begin_transition_draft(source, event.scenePos())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(  # noqa: N802 — Qt override
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        """Update the draft transition line as the user drags."""
        if self._pending_source is not None and self._draft_line is not None:
            centre = self._pending_source.centre()
            self._draft_line.setLine(
                centre.x(),
                centre.y(),
                event.scenePos().x(),
                event.scenePos().y(),
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(  # noqa: N802 — Qt override
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        """Finish the transition drag by committing an edge if a target exists."""
        if self._pending_source is not None:
            target = self._state_at(event.scenePos())
            source = self._pending_source
            self._finish_transition_draft()
            if target is not None:
                label, ok = QInputDialog.getText(
                    None,
                    "New transition",
                    "Label:",
                )
                if ok:
                    self.add_transition(source, target, label)
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(  # noqa: N802 — Qt override
        self,
        event: QGraphicsSceneContextMenuEvent,
    ) -> None:
        """Right-click a state → initial / accepting / delete menu."""
        state = self._state_at(event.scenePos())
        if state is None:
            super().contextMenuEvent(event)
            return
        menu = QMenu()
        make_initial = QAction("Set as initial", menu)
        make_initial.triggered.connect(lambda: self.set_initial(state))
        toggle_accept = QAction(
            "Unmark accepting" if state.is_accepting else "Mark accepting",
            menu,
        )
        toggle_accept.triggered.connect(
            lambda: state.set_accepting(not state.is_accepting),
        )
        rename = QAction("Rename…", menu)
        rename.triggered.connect(lambda: self._rename_state(state))
        delete = QAction("Delete", menu)
        delete.triggered.connect(lambda: self.remove_state(state))
        menu.addAction(make_initial)
        menu.addAction(toggle_accept)
        menu.addSeparator()
        menu.addAction(rename)
        menu.addAction(delete)
        menu.exec(event.screenPos())
        event.accept()

    # ------------------------------------------------------------ dialogs
    def _rename_state(self, state: StateItem) -> None:
        new_id, ok = QInputDialog.getText(
            None,
            "Rename state",
            "State id:",
            text=state.state_id,
        )
        if ok and new_id:
            state.set_state_id(new_id)
            self.structure_changed.emit()

    # ------------------------------------------------------------ draft arrow
    def _begin_transition_draft(self, source: StateItem, pos: QPointF) -> None:
        self._pending_source = source
        line = QGraphicsLineItem(
            source.centre().x(),
            source.centre().y(),
            pos.x(),
            pos.y(),
        )
        pen = QPen(QColor("#3478f6"), 1.5, Qt.PenStyle.DashLine)
        line.setPen(pen)
        self.addItem(line)
        self._draft_line = line

    def _finish_transition_draft(self) -> None:
        if self._draft_line is not None:
            self.removeItem(self._draft_line)
            self._draft_line = None
        self._pending_source = None

    # ------------------------------------------------------------ bulk ops
    def clear_automaton(self) -> None:
        """Remove every state and transition from the scene."""
        for state in list(self.state_items()):
            self.remove_state(state)

    def populate_from(
        self,
        states: Iterable[tuple[str, float, float, bool, bool]],
        transitions: Iterable[tuple[str, str, str]],
    ) -> None:
        """Reset the scene and repopulate from ``(state_defs, transition_defs)``."""
        self.clear_automaton()
        by_id: dict[str, StateItem] = {}
        for state_id, x, y, is_initial, is_accepting in states:
            item = self.add_state(x, y, state_id=state_id)
            item.set_initial(is_initial)
            item.set_accepting(is_accepting)
            by_id[state_id] = item
        for src_id, tgt_id, label in transitions:
            if src_id in by_id and tgt_id in by_id:
                self.add_transition(by_id[src_id], by_id[tgt_id], label)
