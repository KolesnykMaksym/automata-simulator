"""Native JSON save/load — round-trip guaranteed by pydantic.

Summary (UA): Нативний JSON-формат проєкту: серіалізація/десеріалізація
``Automaton`` через pydantic ``model_dump_json`` / ``model_validate_json``.
Round-trip безвтратний (protected by model validator).
Summary (EN): Project-native JSON format — lossless round-trip backed by
pydantic's ``model_dump_json`` / ``model_validate_json`` plus the Automaton
validator.
"""

from __future__ import annotations

from pathlib import Path

from automata_simulator.core.models import Automaton


def automaton_to_json(automaton: Automaton, *, indent: int | None = 2) -> str:
    """Serialise ``automaton`` to a JSON string."""
    return automaton.model_dump_json(indent=indent)


def automaton_from_json(text: str) -> Automaton:
    """Parse and validate an automaton from a JSON string."""
    return Automaton.model_validate_json(text)


def save_json(automaton: Automaton, path: Path, *, indent: int | None = 2) -> None:
    """Write ``automaton`` to ``path`` as UTF-8 JSON."""
    path.write_text(automaton_to_json(automaton, indent=indent), encoding="utf-8")


def load_json(path: Path) -> Automaton:
    """Read an automaton from ``path`` (UTF-8 JSON)."""
    return automaton_from_json(path.read_text(encoding="utf-8"))
