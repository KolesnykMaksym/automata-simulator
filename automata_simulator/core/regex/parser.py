"""Lark-based regular-expression parser.

Summary (UA): Парсер регулярних виразів на базі Lark. Підтримувані оператори:
конкатенація, ``|``, ``*``, ``+``, ``?``; літерали [A-Za-z0-9]; ``ε`` і ``∅``;
круглі дужки.
Summary (EN): Lark-based regex parser. Supports concatenation, ``|``, ``*``,
``+``, ``?``, alphanumeric literals, ``ε`` / ``∅``, and parentheses.
"""

from __future__ import annotations

from lark import Lark, Token, Transformer

from automata_simulator.core.regex.ast import (
    EmptySet as EmptySetNode,
)
from automata_simulator.core.regex.ast import (
    Epsilon,
    Literal,
    RegexNode,
    concat,
    star,
    union,
)

_GRAMMAR = r"""
start: alt
alt: seq ("|" seq)*
seq: post*
post: atom POSTFIX*
POSTFIX: "*" | "+" | "?"
?atom: CHAR
     | EPSILON -> epsilon_atom
     | EMPTY   -> empty_atom
     | "(" alt ")"
CHAR: /[A-Za-z0-9]/
EPSILON: "ε"
EMPTY: "∅"
"""


class _RegexTransformer(Transformer[Token, RegexNode]):
    """Lark transformer that converts the parse tree into a RegexNode."""

    def start(self, items: list[RegexNode]) -> RegexNode:
        return items[0]

    def alt(self, items: list[RegexNode]) -> RegexNode:
        result = items[0]
        for n in items[1:]:
            result = union(result, n)
        return result

    def seq(self, items: list[RegexNode]) -> RegexNode:
        if not items:
            return Epsilon()
        result = items[0]
        for n in items[1:]:
            result = concat(result, n)
        return result

    def post(self, items: list[RegexNode | Token]) -> RegexNode:
        first = items[0]
        if isinstance(first, Token):  # defensive — lark gives us a RegexNode here
            raise ValueError(f"Unexpected token in post rule: {first!r}")
        node: RegexNode = first
        for op_tok in items[1:]:
            op = str(op_tok)
            if op == "*":
                node = star(node)
            elif op == "+":
                node = concat(node, star(node))
            elif op == "?":
                node = union(node, Epsilon())
        return node

    def CHAR(self, token: Token) -> RegexNode:  # noqa: N802 — Lark terminal rule naming
        return Literal(str(token))

    def epsilon_atom(self, _items: list[Token]) -> RegexNode:
        return Epsilon()

    def empty_atom(self, _items: list[Token]) -> RegexNode:
        return EmptySetNode()


_parser: Lark = Lark(_GRAMMAR, parser="earley")
_transformer: _RegexTransformer = _RegexTransformer()


def parse_regex(text: str) -> RegexNode:
    """Parse ``text`` into a :data:`RegexNode`.

    Args:
        text: Regular-expression source. Whitespace is significant.

    Returns:
        The parsed AST.

    Raises:
        ValueError: If ``text`` is not a valid regular expression.
    """
    try:
        tree = _parser.parse(text)
        result = _transformer.transform(tree)
    except Exception as exc:  # Lark raises a variety of exceptions.
        raise ValueError(f"Invalid regex {text!r}: {exc}") from exc
    return result
