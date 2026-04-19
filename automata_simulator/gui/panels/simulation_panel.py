"""Simulation control panel (Run / Step / Pause / Reset).

Summary (UA): Панель керування симуляцією FA. Користувач вводить тестовий
рядок, тисне Run/Step/Pause/Reset, підсвічуються активні стани і використані
переходи. Швидкість регулюється повзунком (0.1×–10×).
Summary (EN): FA simulation control widget. Accepts an input string, drives
Run/Step/Pause/Reset, highlights the active states and the most-recently
fired transitions on the scene. Speed slider spans 0.1×–10×.
"""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from automata_simulator.core.models import AutomatonType
from automata_simulator.core.simulators import (
    DFASimulator,
    DFAStep,
    NFASimulator,
    NFAStep,
    Verdict,
)
from automata_simulator.gui.canvas import (
    AutomatonScene,
    SceneConversionError,
    scene_to_automaton,
)
from automata_simulator.gui.panels.test_presets import presets_for

_BASE_INTERVAL_MS: int = 500
_SLIDER_MIN: int = -20
_SLIDER_MAX: int = 20


class SimulationPanel(QWidget):
    """A QWidget that drives an FA simulation over an :class:`AutomatonScene`."""

    status_changed = Signal(str)

    def __init__(self, scene: AutomatonScene, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = scene
        self._simulator: DFASimulator | NFASimulator | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(_BASE_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer_tick)
        self._build_ui()
        self.retranslate_ui()

    # ------------------------------------------------------------ UI build
    def _build_ui(self) -> None:
        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText(self.tr("Input string…"))

        self._presets_label = QLabel()
        self._presets_list = QListWidget()
        self._presets_list.setMaximumHeight(140)
        self._presets_list.itemActivated.connect(self._apply_preset)
        self._presets_list.itemDoubleClicked.connect(self._apply_preset)

        self._run_button = QPushButton()
        self._step_button = QPushButton()
        self._pause_button = QPushButton()
        self._reset_button = QPushButton()

        self._run_button.clicked.connect(self.run)
        self._step_button.clicked.connect(self.step_once)
        self._pause_button.clicked.connect(self.pause)
        self._reset_button.clicked.connect(self.reset)

        self._speed_label = QLabel()
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(_SLIDER_MIN, _SLIDER_MAX)
        self._speed_slider.setValue(0)  # 1.0× speed
        self._speed_slider.valueChanged.connect(self._on_speed_changed)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)

        buttons = QHBoxLayout()
        buttons.addWidget(self._run_button)
        buttons.addWidget(self._step_button)
        buttons.addWidget(self._pause_button)
        buttons.addWidget(self._reset_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._input_edit)
        layout.addWidget(self._presets_label)
        layout.addWidget(self._presets_list)
        layout.addLayout(buttons)
        layout.addWidget(self._speed_label)
        layout.addWidget(self._speed_slider)
        layout.addWidget(self._status_label)
        layout.addStretch(1)

        # Populate presets once at startup and whenever the scene structure changes.
        self._refresh_presets()
        self._scene.structure_changed.connect(self._refresh_presets)

    def retranslate_ui(self) -> None:
        """Re-apply localised strings after a language change."""
        self._run_button.setText(self.tr("&Run"))
        self._step_button.setText(self.tr("S&tep"))
        self._pause_button.setText(self.tr("&Pause"))
        self._reset_button.setText(self.tr("R&eset"))
        self._speed_label.setText(self.tr("Speed"))
        self._presets_label.setText(self.tr("Quick inputs:"))
        self._input_edit.setPlaceholderText(self.tr("Input string…"))
        if self._simulator is None:
            self._status_label.setText(self.tr("Ready"))

    # ------------------------------------------------------------ public control
    @property
    def simulator(self) -> DFASimulator | NFASimulator | None:
        """The active simulator, or ``None`` before the first ``reset``."""
        return self._simulator

    def reset(self) -> None:
        """Reset simulation state and clear canvas highlights."""
        self._timer.stop()
        self._simulator = None
        self._clear_highlights()
        self._status_label.setText(self.tr("Ready"))
        self.status_changed.emit(self.tr("Ready"))

    def pause(self) -> None:
        """Stop the auto-run timer; simulator state is preserved."""
        self._timer.stop()

    def run(self) -> None:
        """Kick off auto-run, advancing one step per timer tick."""
        if self._simulator is None and not self._prepare_simulator():
            return
        self._timer.start()

    def step_once(self) -> None:
        """Take exactly one simulation step."""
        if self._simulator is None and not self._prepare_simulator():
            return
        self._advance_one_step()

    # ------------------------------------------------------------ internals
    def _prepare_simulator(self) -> bool:
        try:
            automaton = scene_to_automaton(self._scene)
        except SceneConversionError as exc:
            self._status_label.setText(self.tr("Error: {msg}").format(msg=str(exc)))
            return False
        if automaton.type is AutomatonType.DFA:
            self._simulator = DFASimulator(automaton)
        elif automaton.type in (AutomatonType.NFA, AutomatonType.EPSILON_NFA):
            self._simulator = NFASimulator(automaton)
        else:
            self._status_label.setText(
                self.tr(
                    "Simulation of {kind} automata is not yet supported in the GUI",
                ).format(kind=automaton.type.value),
            )
            return False
        self._simulator.reset(self._input_edit.text())
        self._clear_highlights()
        self._apply_current_highlights()
        return True

    def _on_timer_tick(self) -> None:
        if not self._advance_one_step():
            self._timer.stop()

    def _advance_one_step(self) -> bool:
        sim = self._simulator
        if sim is None:
            return False
        step = sim.step()
        self._clear_highlights()
        self._apply_current_highlights()
        if step is not None:
            self._highlight_step(step)
        if sim.is_halted:
            verdict = cast("Verdict", sim.verdict)
            self._status_label.setText(
                self.tr("Verdict: {v}").format(v=verdict.value),
            )
            self.status_changed.emit(verdict.value)
            return False
        return True

    def _apply_current_highlights(self) -> None:
        sim = self._simulator
        if sim is None:
            return
        active: set[str] = set()
        if isinstance(sim, DFASimulator):
            current = sim.current_state
            if current is not None:
                active.add(current)
        else:
            active.update(sim.current_states)
        for state_item in self._scene.state_items():
            state_item.set_highlighted(state_item.state_id in active)

    def _highlight_step(self, step: DFAStep | NFAStep) -> None:
        if isinstance(step, DFAStep):
            pairs = {(step.from_state, step.to_state)}
        else:
            pairs = {
                (src, tgt) for src in step.from_states for tgt in step.to_states
            }
        for tr_item in self._scene.transition_items():
            is_active = (tr_item.source.state_id, tr_item.target.state_id) in pairs
            tr_item.set_highlighted(is_active)

    def _clear_highlights(self) -> None:
        for state_item in self._scene.state_items():
            state_item.set_highlighted(False)
        for tr_item in self._scene.transition_items():
            tr_item.set_highlighted(False)

    def _apply_preset(self, item: QListWidgetItem) -> None:
        """Copy a preset entry into the input field."""
        stored = item.data(Qt.ItemDataRole.UserRole)
        self._input_edit.setText(stored if isinstance(stored, str) else item.text())
        self._input_edit.setFocus()

    def _refresh_presets(self) -> None:
        """Repopulate the preset list based on the current scene automaton."""
        self._presets_list.clear()
        try:
            automaton = scene_to_automaton(self._scene)
        except SceneConversionError:
            return
        strings = presets_for(automaton.name, automaton.type)
        for text in strings:
            item = QListWidgetItem(text if text else "(ε)")
            item.setData(Qt.ItemDataRole.UserRole, text)
            self._presets_list.addItem(item)

    def _on_speed_changed(self, raw: int) -> None:
        factor = 2.0 ** (raw / 4.0)  # slider -20…20 → 2^(-5)…2^5 ≈ 0.03×–32×
        factor = max(0.1, min(10.0, factor))
        interval = max(20, int(_BASE_INTERVAL_MS / factor))
        self._timer.setInterval(interval)
        self._speed_label.setText(self.tr("Speed: {x:.1f}×").format(x=factor))
