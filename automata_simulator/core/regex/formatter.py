"""Regex AST → canonical string representation.

Summary (UA): Форматує AST регулярного виразу у строкове представлення з
мінімально необхідними дужками (за пріоритетом: Star > Concat > Union).
Summary (EN): Pretty-print a regex AST using the minimal number of parens
required by operator precedence (Star > Concat > Union).
"""

from __future__ import annotations

from automata_simulator.core.regex.ast import (
    Concat,
    EmptySet,
    Epsilon,
    Literal,
    RegexNode,
    Star,
    Union,
)


def format_regex(node: RegexNode) -> str:
    """Return a human-readable string for ``node``."""
    match node:
        case Literal(c):
            return c
        case Epsilon():
            return "ε"
        case EmptySet():
            return "∅"
        case Star(expr):
            inner = format_regex(expr)
            return f"({inner})*" if isinstance(expr, (Concat, Union)) else f"{inner}*"
        case Concat(lhs, rhs):
            left = format_regex(lhs)
            right = format_regex(rhs)
            if isinstance(lhs, Union):
                left = f"({left})"
            if isinstance(rhs, Union):
                right = f"({right})"
            return left + right
        case Union(lhs, rhs):
            return f"{format_regex(lhs)}|{format_regex(rhs)}"
