"""QUndoCommand subclasses for the canvas editor.

Summary (UA): Команди undo/redo для редактора canvas (додавання/видалення
станів і переходів). Використовуються через ``QUndoStack`` у ``MainWindow``.
Summary (EN): Reversible canvas edits as QUndoCommands. Pair them with a
``QUndoStack`` in the main window so the editor honours Ctrl+Z / Ctrl+Y.
"""

from __future__ import annotations

from PySide6.QtGui import QUndoCommand

from automata_simulator.gui.canvas.scene import AutomatonScene
from automata_simulator.gui.canvas.state_item import StateItem
from automata_simulator.gui.canvas.transition_item import TransitionItem


class AddStateCommand(QUndoCommand):
    """Add a new :class:`StateItem` at ``(x, y)`` with optional ``state_id``."""

    def __init__(
        self,
        scene: AutomatonScene,
        x: float,
        y: float,
        *,
        state_id: str | None = None,
    ) -> None:
        super().__init__("Add state")
        self._scene = scene
        self._x = x
        self._y = y
        self._state_id = state_id
        self._item: StateItem | None = None

    def redo(self) -> None:
        """Create the state (or re-add the previously removed instance)."""
        if self._item is None:
            self._item = self._scene.add_state(
                self._x,
                self._y,
                state_id=self._state_id,
            )
            self._state_id = self._item.state_id
        else:
            self._scene.addItem(self._item)
            self._scene.structure_changed.emit()

    def undo(self) -> None:
        """Remove the state (and any transitions we've since added)."""
        if self._item is not None:
            self._scene.remove_state(self._item)

    @property
    def created_item(self) -> StateItem | None:
        """The :class:`StateItem` created by :meth:`redo`."""
        return self._item


class AddTransitionCommand(QUndoCommand):
    """Add a transition between two existing states."""

    def __init__(
        self,
        scene: AutomatonScene,
        source: StateItem,
        target: StateItem,
        label: str = "",
    ) -> None:
        super().__init__("Add transition")
        self._scene = scene
        self._source = source
        self._target = target
        self._label = label
        self._item: TransitionItem | None = None

    def redo(self) -> None:
        """Insert (or re-insert) the transition."""
        if self._item is None:
            self._item = self._scene.add_transition(
                self._source,
                self._target,
                self._label,
            )
        else:
            self._scene.addItem(self._item)
            self._scene._transitions.append(self._item)
            self._scene.structure_changed.emit()

    def undo(self) -> None:
        """Remove the transition."""
        if self._item is not None:
            self._scene.remove_transition(self._item)

    @property
    def created_item(self) -> TransitionItem | None:
        """The :class:`TransitionItem` created by :meth:`redo`."""
        return self._item


class RemoveStateCommand(QUndoCommand):
    """Remove a state (and all incident transitions) reversibly."""

    def __init__(self, scene: AutomatonScene, state: StateItem) -> None:
        super().__init__("Remove state")
        self._scene = scene
        self._state = state
        self._incident: list[TransitionItem] = []

    def redo(self) -> None:
        """Detach and hide the state + every incident transition."""
        self._incident = [
            tr for tr in self._scene.transition_items() if self._state in (tr.source, tr.target)
        ]
        self._scene.remove_state(self._state)

    def undo(self) -> None:
        """Put the state and transitions back."""
        self._scene.addItem(self._state)
        for tr in self._incident:
            self._scene.addItem(tr)
            self._scene._transitions.append(tr)
        self._scene.structure_changed.emit()
