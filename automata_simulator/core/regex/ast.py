"""Regular-expression AST with simplifying smart constructors.

Summary (UA): Синтаксичне дерево регулярного виразу: Literal, Epsilon, EmptySet,
Concat, Union, Star + helper-функції зі спрощенням тотожностей (r·ε=r, r|∅=r,
ε*=ε, ∅*=ε, r**=r*).
Summary (EN): Immutable regex AST nodes plus helper constructors that apply
the identity laws (r·ε=r, r|∅=r, ε*=ε, ∅*=ε, r**=r*) to keep results compact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class Literal:
    """A single alphabet symbol."""

    char: str


@dataclass(frozen=True, slots=True)
class Epsilon:
    """The empty-string regex — matches exactly ``""``."""


@dataclass(frozen=True, slots=True)
class EmptySet:
    """The empty-language regex — matches nothing."""


@dataclass(frozen=True, slots=True)
class Concat:
    """Concatenation ``left · right``."""

    left: RegexNode
    right: RegexNode


@dataclass(frozen=True, slots=True)
class Union:
    """Alternation ``left | right``."""

    left: RegexNode
    right: RegexNode


@dataclass(frozen=True, slots=True)
class Star:
    """Kleene star ``expr*``."""

    expr: RegexNode


RegexNode: TypeAlias = Literal | Epsilon | EmptySet | Concat | Union | Star


# -------------------------------------------------------------------------- smart ctors
def concat(left: RegexNode, right: RegexNode) -> RegexNode:
    """Concatenate two AST nodes applying identity laws.

    Identities: ``ε · r = r``, ``r · ε = r``, ``∅ · r = ∅``, ``r · ∅ = ∅``.
    """
    if isinstance(left, Epsilon):
        return right
    if isinstance(right, Epsilon):
        return left
    if isinstance(left, EmptySet) or isinstance(right, EmptySet):
        return EmptySet()
    return Concat(left, right)


def union(left: RegexNode, right: RegexNode) -> RegexNode:
    """Combine two AST nodes via alternation, absorbing ``∅`` and deduplicating."""
    if isinstance(left, EmptySet):
        return right
    if isinstance(right, EmptySet):
        return left
    if left == right:
        return left
    return Union(left, right)


def star(expr: RegexNode) -> RegexNode:
    """Apply Kleene star, folding idempotent / trivial cases.

    Identities: ``ε* = ε``, ``∅* = ε``, ``(r*)* = r*``.
    """
    if isinstance(expr, (Epsilon, EmptySet)):
        return Epsilon()
    if isinstance(expr, Star):
        return expr
    return Star(expr)


def literals_in(node: RegexNode) -> frozenset[str]:
    """Collect every :class:`Literal` character appearing in ``node``."""
    match node:
        case Literal(c):
            return frozenset({c})
        case Epsilon() | EmptySet():
            return frozenset()
        case Concat(lhs, rhs) | Union(lhs, rhs):
            return literals_in(lhs) | literals_in(rhs)
        case Star(inner):
            return literals_in(inner)
