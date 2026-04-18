"""Command-line interface for automata-simulator.

Summary (UA): CLI на базі Click. Підтримувані команди: ``simulate``, ``convert``,
``minimize``, ``batch-test``, ``export``. Формат файлу автоматично визначається
за розширенням (``.json`` ↔ native JSON, ``.jff`` ↔ JFLAP, ``.dot`` ↔ Graphviz).
Summary (EN): Click-based CLI with ``simulate`` / ``convert`` / ``minimize`` /
``batch-test`` / ``export`` subcommands. File format is inferred from the
extension: ``.json`` (native), ``.jff`` (JFLAP), ``.dot`` (Graphviz).
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

import click

from automata_simulator import __version__
from automata_simulator.core.algorithms import (
    minimize_dfa,
    nfa_to_dfa,
    remove_epsilon_transitions,
)
from automata_simulator.core.io import (
    load_jff,
    load_json,
    save_dot,
    save_jff,
    save_json,
    to_dot,
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


# ----------------------------------------------------------------- file helpers
def _load_automaton(path: Path) -> Automaton:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json(path)
    if suffix in {".jff", ".xml"}:
        return load_jff(path)
    raise click.BadParameter(
        f"Unsupported input extension: {suffix!r} "
        f"(expected .json, .jff, or .xml)",
    )


def _save_automaton(automaton: Automaton, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        save_json(automaton, path)
        return
    if suffix == ".jff":
        save_jff(automaton, path)
        return
    if suffix == ".dot":
        save_dot(automaton, path)
        return
    raise click.BadParameter(
        f"Unsupported output extension: {suffix!r} "
        f"(expected .json, .jff, or .dot)",
    )


def _simulator_for(automaton: Automaton) -> Any:  # returns the appropriate simulator
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


# ----------------------------------------------------------------- CLI group
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name="automata")
def main() -> None:
    """Automata Simulator — command-line tools for DFA/NFA/PDA/TM/Mealy/Moore."""


# ----------------------------------------------------------------- simulate
@main.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--input", "-i", "input_string", required=True, help="Input string to run.")
@click.option("--step", is_flag=True, help="Print each step of the simulation.")
def simulate(source: Path, input_string: str, step: bool) -> None:
    """Simulate an automaton on INPUT."""
    automaton = _load_automaton(source)
    sim = _simulator_for(automaton)
    trace = sim.run(input_string)
    if step:
        for i, s in enumerate(trace.steps):
            click.echo(f"[{i}] {s}")
    click.echo(f"verdict: {trace.verdict.value}")
    click.echo(f"accepted: {trace.accepted}")


# ----------------------------------------------------------------- convert
@main.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--to",
    "target",
    type=click.Choice(["dfa", "nfa"], case_sensitive=False),
    required=True,
    help="Target automaton kind.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Output file (.json or .jff).",
)
def convert(source: Path, target: str, output: Path) -> None:
    """Convert an NFA/ε-NFA to a DFA, or an ε-NFA to an NFA."""
    automaton = _load_automaton(source)
    target_lower = target.lower()
    if target_lower == "dfa":
        if automaton.type not in (AutomatonType.NFA, AutomatonType.EPSILON_NFA):
            raise click.ClickException(
                f"Cannot convert {automaton.type.value!r} to DFA "
                "(expected NFA or ε-NFA)",
            )
        result = nfa_to_dfa(automaton).dfa
    else:  # target_lower == "nfa"
        if automaton.type is not AutomatonType.EPSILON_NFA:
            raise click.ClickException(
                f"Cannot remove ε-transitions from {automaton.type.value!r}",
            )
        result = remove_epsilon_transitions(automaton).nfa
    _save_automaton(result, output)
    click.echo(f"Wrote {target_lower} to {output}")


# ----------------------------------------------------------------- minimize
@main.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Where to write the minimised DFA.",
)
def minimize(source: Path, output: Path) -> None:
    """Minimise a DFA via Hopcroft's algorithm."""
    automaton = _load_automaton(source)
    if automaton.type is not AutomatonType.DFA:
        raise click.ClickException(
            f"minimize expects a DFA, got {automaton.type.value!r}",
        )
    result = minimize_dfa(automaton).dfa
    _save_automaton(result, output)
    click.echo(
        f"Minimised {len(automaton.states)} → {len(result.states)} states → {output}",
    )


# ----------------------------------------------------------------- batch-test
@main.command("batch-test")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--strings",
    "-s",
    "strings_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Text file with one input string per line.",
)
@click.option(
    "--report",
    "-r",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Output file (.csv or .json).",
)
def batch_test(source: Path, strings_file: Path, report: Path) -> None:
    """Batch-test the automaton on every line of a text file."""
    automaton = _load_automaton(source)
    sim = _simulator_for(automaton)
    rows: list[dict[str, Any]] = []
    for raw in strings_file.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\r\n")
        started = time.monotonic()
        trace = sim.run(line)
        elapsed_ms = (time.monotonic() - started) * 1000.0
        rows.append(
            {
                "input": line,
                "verdict": trace.verdict.value,
                "accepted": trace.accepted,
                "time_ms": round(elapsed_ms, 3),
            },
        )
    suffix = report.suffix.lower()
    if suffix == ".csv":
        with report.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["input", "verdict", "accepted", "time_ms"],
            )
            writer.writeheader()
            writer.writerows(rows)
    elif suffix == ".json":
        report.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    else:
        raise click.BadParameter(
            f"Unsupported report extension: {suffix!r} (expected .csv or .json)",
        )
    accepted = sum(1 for r in rows if r["accepted"])
    click.echo(
        f"Tested {len(rows)} strings: {accepted} accepted, "
        f"{len(rows) - accepted} rejected → {report}",
    )


# ----------------------------------------------------------------- export
@main.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["dot", "svg", "png"], case_sensitive=False),
    required=True,
    help="Output format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Output file.",
)
def export(source: Path, fmt: str, output: Path) -> None:
    """Export automaton diagram in DOT/SVG/PNG format."""
    automaton = _load_automaton(source)
    dot_text = to_dot(automaton)
    fmt_lower = fmt.lower()
    if fmt_lower == "dot":
        output.write_text(dot_text, encoding="utf-8")
    else:
        try:
            import pydot  # noqa: PLC0415 — optional-dep lookup must be lazy
        except ImportError as exc:  # pragma: no cover — pydot is a dev dependency
            raise click.ClickException(
                "pydot is required for SVG/PNG export; install with `pip install pydot`",
            ) from exc
        graphs = pydot.graph_from_dot_data(dot_text)
        if not graphs:
            raise click.ClickException("Failed to parse generated DOT")
        graph = graphs[0]
        # pydot synthesises `create_svg` / `create_png` at runtime; these aren't
        # present on Dot's static surface so mypy cannot see them.
        create_method = getattr(graph, f"create_{fmt_lower}")
        try:
            rendered = create_method()
        except Exception as exc:  # Graphviz binary missing / rendering error.
            raise click.ClickException(
                f"Rendering failed (is the Graphviz binary installed?): {exc}",
            ) from exc
        output.write_bytes(rendered)
    click.echo(f"Wrote {fmt_lower} to {output}")


if __name__ == "__main__":  # pragma: no cover
    main()
