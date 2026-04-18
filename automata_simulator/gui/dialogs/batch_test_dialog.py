"""Batch-test modal dialog — run the scene's automaton on many inputs.

Summary (UA): Діалог пакетного тестування. Користувач вставляє рядки (або
завантажує файл), запускає симуляцію та експортує звіт у CSV/JSON.
Summary (EN): A modal that runs the current scene's automaton on a batch of
input strings, fills a results table (input / verdict / accepted / time_ms),
and exports the table to CSV or JSON.
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from automata_simulator.core.models import Automaton, AutomatonType
from automata_simulator.core.simulators import (
    DFASimulator,
    MealySimulator,
    MooreSimulator,
    NFASimulator,
    PDASimulator,
    TMSimulator,
)
from automata_simulator.gui.canvas import (
    AutomatonScene,
    SceneConversionError,
    scene_to_automaton,
)


@dataclass(frozen=True, slots=True)
class BatchResult:
    """One row of the batch report."""

    input: str
    verdict: str
    accepted: bool
    time_ms: float


def _simulator_for(automaton: Automaton) -> Any:
    match automaton.type:
        case AutomatonType.DFA:
            return DFASimulator(automaton)
        case AutomatonType.NFA | AutomatonType.EPSILON_NFA:
            return NFASimulator(automaton)
        case AutomatonType.MEALY:
            return MealySimulator(automaton)
        case AutomatonType.MOORE:
            return MooreSimulator(automaton)
        case AutomatonType.PDA:
            return PDASimulator(automaton)
        case AutomatonType.TM:
            return TMSimulator(automaton)


class BatchTestDialog(QDialog):
    """Batch-tester for whichever automaton the scene currently represents."""

    def __init__(self, scene: AutomatonScene, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Batch test"))
        self._scene = scene
        self._results: list[BatchResult] = []
        self._build_ui()
        self.resize(640, 480)

    # ------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self._input_edit = QPlainTextEdit()
        self._input_edit.setPlaceholderText(
            self.tr("One input string per line…"),
        )

        load_btn = QPushButton(self.tr("Load file…"))
        load_btn.clicked.connect(self._load_file)
        self._run_btn = QPushButton(self.tr("Run"))
        self._run_btn.clicked.connect(self._run_batch)
        export_csv_btn = QPushButton(self.tr("Export CSV"))
        export_csv_btn.clicked.connect(lambda: self._export("csv"))
        export_json_btn = QPushButton(self.tr("Export JSON"))
        export_json_btn.clicked.connect(lambda: self._export("json"))

        button_row = QHBoxLayout()
        button_row.addWidget(load_btn)
        button_row.addWidget(self._run_btn)
        button_row.addStretch(1)
        button_row.addWidget(export_csv_btn)
        button_row.addWidget(export_json_btn)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            [
                self.tr("Input"),
                self.tr("Verdict"),
                self.tr("Accepted"),
                self.tr("Time (ms)"),
            ],
        )
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self._status_label = QLabel(self.tr("No results yet."))
        self._status_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Input strings:")))
        layout.addWidget(self._input_edit)
        layout.addLayout(button_row)
        layout.addWidget(self._status_label)
        layout.addWidget(self._table)

    # ------------------------------------------------------------ API
    def results(self) -> list[BatchResult]:
        """Return the most recent batch results."""
        return list(self._results)

    def run_with_inputs(self, inputs: list[str]) -> list[BatchResult]:
        """Run synchronously (without touching UI text boxes) — used by tests."""
        try:
            automaton = scene_to_automaton(self._scene)
        except SceneConversionError as exc:
            raise ValueError(str(exc)) from exc
        return self._simulate(automaton, inputs)

    # ------------------------------------------------------------ internals
    def _load_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Load strings file"),
            "",
            "Text files (*.txt);;All files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        self._input_edit.setPlainText(path.read_text(encoding="utf-8"))

    def _run_batch(self) -> None:
        try:
            automaton = scene_to_automaton(self._scene)
        except SceneConversionError as exc:
            QMessageBox.warning(self, self.tr("Scene error"), str(exc))
            return
        lines = [
            line.rstrip("\r\n")
            for line in self._input_edit.toPlainText().splitlines()
        ]
        self._results = self._simulate(automaton, lines)
        self._populate_table(self._results)
        accepted = sum(1 for r in self._results if r.accepted)
        self._status_label.setText(
            self.tr("Tested {n} strings — {a} accepted, {r} rejected.").format(
                n=len(self._results),
                a=accepted,
                r=len(self._results) - accepted,
            ),
        )

    def _simulate(
        self, automaton: Automaton, inputs: list[str],
    ) -> list[BatchResult]:
        sim = _simulator_for(automaton)
        rows: list[BatchResult] = []
        for line in inputs:
            started = time.monotonic()
            trace = sim.run(line)
            elapsed_ms = (time.monotonic() - started) * 1000.0
            rows.append(
                BatchResult(
                    input=line,
                    verdict=trace.verdict.value,
                    accepted=trace.accepted,
                    time_ms=round(elapsed_ms, 3),
                ),
            )
        return rows

    def _populate_table(self, rows: list[BatchResult]) -> None:
        self._table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._set_cell(r, 0, row.input)
            self._set_cell(r, 1, row.verdict)
            self._set_cell(r, 2, "✓" if row.accepted else "✗")
            self._set_cell(r, 3, f"{row.time_ms:.3f}")

    def _set_cell(self, row: int, col: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, col, item)

    def _export(self, fmt: str) -> None:
        if not self._results:
            QMessageBox.information(
                self,
                self.tr("No data"),
                self.tr("Run a batch first."),
            )
            return
        default_name = "batch-report." + fmt
        path_str, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export report"), default_name,
        )
        if not path_str:
            return
        path = Path(path_str)
        if fmt == "csv":
            self.export_csv(path)
        else:
            self.export_json(path)

    # --- public exporters, usable by tests ---
    def export_csv(self, path: Path) -> None:
        """Write current results as a CSV file to ``path``."""
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["input", "verdict", "accepted", "time_ms"])
            for r in self._results:
                writer.writerow([r.input, r.verdict, str(r.accepted), r.time_ms])

    def export_json(self, path: Path) -> None:
        """Write current results as a JSON array to ``path``."""
        payload = [
            {
                "input": r.input,
                "verdict": r.verdict,
                "accepted": r.accepted,
                "time_ms": r.time_ms,
            }
            for r in self._results
        ]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
