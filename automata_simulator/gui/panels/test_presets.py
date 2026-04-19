"""Ready-made test strings per automaton kind / example name.

Summary (UA): Набір готових тестових рядків для швидкого вибору в панелі
симуляції. Ключ — або точне ім'я автомата (для прикладів з каталогу
``examples/``), або тип автомата.
Summary (EN): Quick-pick input strings for the simulation panel. Lookup is
name-first (so bundled examples show a tailored list), type-second (so any
automaton of a given kind still gets a sensible default selection).
"""

from __future__ import annotations

from automata_simulator.core.models import AutomatonType

_BY_NAME: dict[str, list[str]] = {
    "contains-abb": ["", "abb", "aabb", "aabbabb", "babb", "ab", "ba", "aaabb"],
    "ends-in-abb": ["abb", "aabb", "babb", "ababb", "aabba", "b"],
    "a-star-b-star": ["", "a", "b", "ab", "aaabbb", "ba"],
    "a-n-b-n": ["", "ab", "aabb", "aaabbb", "aaaabbbb", "aab", "abab"],
    "bit-inverter": ["", "0", "1", "01", "1100", "0000"],
    "detect-101": ["0", "101", "11010", "10101", "1011010", "000111"],
    "mod3": ["", "1", "10", "11", "110", "1101", "11011"],
}


_BY_TYPE: dict[AutomatonType, list[str]] = {
    AutomatonType.DFA: ["", "a", "ab", "aa", "bab"],
    AutomatonType.NFA: ["", "a", "aa", "ab", "bab"],
    AutomatonType.EPSILON_NFA: ["", "a", "b", "ab", "ba"],
    AutomatonType.MEALY: ["0", "1", "101", "01010"],
    AutomatonType.MOORE: ["", "1", "10", "110", "1101"],
    AutomatonType.PDA: ["", "ab", "aabb", "aaabbb", "ba"],
    AutomatonType.TM: ["", "0", "1", "01", "10", "0011"],
}


def presets_for(name: str, kind: AutomatonType) -> list[str]:
    """Return a prioritised test-string list.

    Lookup order:
        1. Exact match on ``name`` (covers bundled examples).
        2. Default set for ``kind``.
    """
    if name in _BY_NAME:
        return list(_BY_NAME[name])
    return list(_BY_TYPE.get(kind, []))
