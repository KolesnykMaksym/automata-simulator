"""CLI end-to-end tests via click.testing.CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from automata_simulator.cli.main import main
from automata_simulator.core.io import load_json, save_json
from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    State,
)


def _dfa_ends_in_ab() -> Automaton:
    return Automaton(
        type=AutomatonType.DFA,
        name="ends-in-ab",
        states=[State(id=s) for s in ("q0", "q1", "q2")],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q2"],
        transitions=[
            FATransition(source="q0", target="q1", read="a"),
            FATransition(source="q0", target="q0", read="b"),
            FATransition(source="q1", target="q1", read="a"),
            FATransition(source="q1", target="q2", read="b"),
            FATransition(source="q2", target="q1", read="a"),
            FATransition(source="q2", target="q0", read="b"),
        ],
    )


def _nfa_ends_in_01() -> Automaton:
    return Automaton(
        type=AutomatonType.NFA,
        name="ends-in-01",
        states=[State(id=s) for s in ("q0", "q1", "q2")],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q2"],
        transitions=[
            FATransition(source="q0", target="q0", read="0"),
            FATransition(source="q0", target="q0", read="1"),
            FATransition(source="q0", target="q1", read="0"),
            FATransition(source="q1", target="q2", read="1"),
        ],
    )


def _enfa() -> Automaton:
    return Automaton(
        type=AutomatonType.EPSILON_NFA,
        name="enfa",
        states=[State(id="q0"), State(id="q1")],
        alphabet=["a"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions=[
            FATransition(source="q0", target="q1", read=EPSILON),
            FATransition(source="q1", target="q1", read="a"),
        ],
    )


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def dfa_json(tmp_path: Path) -> Path:
    path = tmp_path / "dfa.json"
    save_json(_dfa_ends_in_ab(), path)
    return path


class TestVersion:
    def test_version_prints_semver(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "automata" in result.output


class TestSimulate:
    def test_accepts(self, runner: CliRunner, dfa_json: Path) -> None:
        result = runner.invoke(main, ["simulate", str(dfa_json), "-i", "ab"])
        assert result.exit_code == 0
        assert "accepted: True" in result.output

    def test_rejects(self, runner: CliRunner, dfa_json: Path) -> None:
        result = runner.invoke(main, ["simulate", str(dfa_json), "-i", "a"])
        assert result.exit_code == 0
        assert "accepted: False" in result.output

    def test_step_flag_prints_steps(self, runner: CliRunner, dfa_json: Path) -> None:
        result = runner.invoke(
            main,
            ["simulate", str(dfa_json), "-i", "ab", "--step"],
        )
        assert result.exit_code == 0
        assert "[0]" in result.output

    def test_unsupported_extension_fails(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "x.unknown"
        path.write_text("{}")
        result = runner.invoke(main, ["simulate", str(path), "-i", "a"])
        assert result.exit_code != 0


class TestConvert:
    def test_nfa_to_dfa_round_trip(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        src = tmp_path / "nfa.json"
        save_json(_nfa_ends_in_01(), src)
        dst = tmp_path / "dfa.json"
        result = runner.invoke(
            main,
            ["convert", str(src), "--to", "dfa", "-o", str(dst)],
        )
        assert result.exit_code == 0, result.output
        # The produced DFA file must load.
        restored = load_json(dst)
        assert restored.type is AutomatonType.DFA

    def test_enfa_to_nfa(self, runner: CliRunner, tmp_path: Path) -> None:
        src = tmp_path / "enfa.json"
        save_json(_enfa(), src)
        dst = tmp_path / "nfa.json"
        result = runner.invoke(
            main,
            ["convert", str(src), "--to", "nfa", "-o", str(dst)],
        )
        assert result.exit_code == 0, result.output

    def test_rejects_dfa_to_dfa_conversion(
        self,
        runner: CliRunner,
        dfa_json: Path,
        tmp_path: Path,
    ) -> None:
        dst = tmp_path / "out.json"
        result = runner.invoke(
            main,
            ["convert", str(dfa_json), "--to", "dfa", "-o", str(dst)],
        )
        assert result.exit_code != 0  # DFA→DFA is rejected


class TestMinimize:
    def test_minimize_drops_equivalent_states(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        src = tmp_path / "dfa.json"
        save_json(_dfa_ends_in_ab(), src)
        dst = tmp_path / "min.json"
        result = runner.invoke(main, ["minimize", str(src), "-o", str(dst)])
        assert result.exit_code == 0, result.output
        assert "Minimised" in result.output

    def test_rejects_non_dfa(self, runner: CliRunner, tmp_path: Path) -> None:
        src = tmp_path / "nfa.json"
        save_json(_nfa_ends_in_01(), src)
        dst = tmp_path / "out.json"
        result = runner.invoke(main, ["minimize", str(src), "-o", str(dst)])
        assert result.exit_code != 0


class TestBatchTest:
    def test_csv_report(
        self,
        runner: CliRunner,
        dfa_json: Path,
        tmp_path: Path,
    ) -> None:
        inputs = tmp_path / "inputs.txt"
        inputs.write_text("ab\nba\naab\n", encoding="utf-8")
        report = tmp_path / "report.csv"
        result = runner.invoke(
            main,
            [
                "batch-test",
                str(dfa_json),
                "--strings",
                str(inputs),
                "--report",
                str(report),
            ],
        )
        assert result.exit_code == 0, result.output
        content = report.read_text()
        assert "input,verdict,accepted,time_ms" in content
        assert "ab,accepted,True" in content

    def test_json_report(
        self,
        runner: CliRunner,
        dfa_json: Path,
        tmp_path: Path,
    ) -> None:
        inputs = tmp_path / "inputs.txt"
        inputs.write_text("ab\nba\n", encoding="utf-8")
        report = tmp_path / "report.json"
        result = runner.invoke(
            main,
            [
                "batch-test",
                str(dfa_json),
                "--strings",
                str(inputs),
                "--report",
                str(report),
            ],
        )
        assert result.exit_code == 0
        rows = json.loads(report.read_text())
        assert len(rows) == 2
        assert rows[0]["input"] == "ab"
        assert rows[0]["accepted"] is True


class TestExport:
    def test_dot_export(self, runner: CliRunner, dfa_json: Path, tmp_path: Path) -> None:
        dst = tmp_path / "g.dot"
        result = runner.invoke(
            main,
            ["export", str(dfa_json), "--format", "dot", "-o", str(dst)],
        )
        assert result.exit_code == 0
        content = dst.read_text()
        assert "digraph" in content

    def test_unsupported_format_rejected_by_click(
        self,
        runner: CliRunner,
        dfa_json: Path,
        tmp_path: Path,
    ) -> None:
        dst = tmp_path / "g.xyz"
        result = runner.invoke(
            main,
            ["export", str(dfa_json), "--format", "bogus", "-o", str(dst)],
        )
        assert result.exit_code != 0
