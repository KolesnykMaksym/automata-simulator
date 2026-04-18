"""GUI entry point — launches QApplication + :class:`MainWindow`.

Summary (UA): Точка входу GUI — створює QApplication і показує головне вікно.
Summary (EN): Creates the QApplication, instantiates the MainWindow and
starts Qt's event loop.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from automata_simulator.gui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``automata-sim`` console script.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv``).

    Returns:
        The Qt application's exit code.
    """
    args = list(sys.argv if argv is None else argv)
    app = QApplication.instance() or QApplication(args)
    window = MainWindow()
    window.show()
    assert isinstance(app, QApplication)
    return int(app.exec())


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
