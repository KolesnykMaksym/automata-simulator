"""Left-side library panel — quick access to loaded automata.

Summary (UA): Панель зліва з переліком автоматів: готові приклади з каталогу
``examples/`` + всі файли, які користувач відкривав. Подвійний клік завантажує
автомат у сцену.
Summary (EN): Dockable left-side panel listing automata the user has access
to: bundled examples plus any file opened via File → Open. Double-click an
entry (or select + press Enter) to load it into the scene.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LibraryPanel(QWidget):
    """List of automata files, emits :attr:`load_requested` with the path."""

    load_requested = Signal(Path)

    def __init__(
        self,
        examples_dir: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._entries: list[Path] = []
        self._build_ui()
        if examples_dir is not None and examples_dir.is_dir():
            self.populate_from_directory(examples_dir)

    # ------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        title = QLabel(self.tr("Library"))
        title.setStyleSheet("font-weight: bold;")

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._emit_from_item)
        self._list.itemActivated.connect(self._emit_from_item)

        open_btn = QPushButton(self.tr("Load selected"))
        open_btn.clicked.connect(self._emit_current)
        remove_btn = QPushButton(self.tr("Remove"))
        remove_btn.clicked.connect(self._remove_current)

        buttons = QHBoxLayout()
        buttons.addWidget(open_btn)
        buttons.addWidget(remove_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(title)
        layout.addWidget(self._list)
        layout.addLayout(buttons)

    def retranslate_ui(self) -> None:
        """Refresh localised strings (called from MainWindow)."""
        # Labels and buttons are indexed in build order — cheap to rebuild.
        layout_parent = self.layout()
        if layout_parent is None:
            return
        title_item = layout_parent.itemAt(0)
        title_widget = title_item.widget() if title_item is not None else None
        if isinstance(title_widget, QLabel):
            title_widget.setText(self.tr("Library"))

    # ------------------------------------------------------------ public API
    def entries(self) -> list[Path]:
        """Return every path currently listed in the library."""
        return list(self._entries)

    def add_entry(self, path: Path) -> None:
        """Add a single automaton path to the library (dedup)."""
        abs_path = path.resolve()
        if abs_path in self._entries:
            # Still move it to the top so the most recent is first.
            idx = self._entries.index(abs_path)
            self._entries.pop(idx)
            item = self._list.takeItem(idx)
            if item is not None:
                del item
        self._entries.insert(0, abs_path)
        item = QListWidgetItem(abs_path.name)
        item.setData(Qt.ItemDataRole.UserRole, abs_path)
        item.setToolTip(str(abs_path))
        self._list.insertItem(0, item)

    def populate_from_directory(self, directory: Path) -> None:
        """Scan ``directory`` for ``.json`` / ``.jff`` files and add them."""
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in {".json", ".jff", ".xml"}:
                self.add_entry(path)

    def select_path(self, path: Path) -> None:
        """Highlight the row corresponding to ``path`` (if present)."""
        target = path.resolve()
        for row in range(self._list.count()):
            item = self._list.item(row)
            stored = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(stored, Path) and stored == target:
                self._list.setCurrentRow(row)
                return

    # ------------------------------------------------------------ slots
    def _emit_from_item(self, item: QListWidgetItem) -> None:
        stored = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(stored, Path):
            self.load_requested.emit(stored)

    def _emit_current(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self._emit_from_item(item)

    def _remove_current(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        taken = self._list.takeItem(row)
        if taken is not None:
            stored = taken.data(Qt.ItemDataRole.UserRole)
            if isinstance(stored, Path) and stored in self._entries:
                self._entries.remove(stored)
            del taken
