"""Context-free grammar model.

Summary (UA): Модель контекстно-вільної граматики з pydantic-валідацією:
перевірка disjoint-ності терміналів і нетерміналів, існування head у
нетерміналах, перевірка символів у body.
Summary (EN): Pydantic CFG model. Validates: disjoint terminal / nonterminal
sets, non-empty symbols, start ∈ nonterminals, each production head is a
nonterminal, and body symbols are in the combined vocabulary.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class Production(BaseModel):
    """A single production rule ``head → body``.

    Attributes:
        head: Left-hand-side nonterminal.
        body: Right-hand-side symbol sequence. An empty tuple is the
            ε-production ``head → ε``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    head: str
    body: tuple[str, ...] = ()

    @property
    def is_epsilon(self) -> bool:
        """Whether this is an ε-production."""
        return len(self.body) == 0


class CFG(BaseModel):
    """A context-free grammar ``(V, Σ, P, S)``.

    Attributes:
        name: Human-readable identifier.
        nonterminals: The set V of nonterminal symbols.
        terminals: The set Σ of terminal symbols (disjoint from V).
        productions: The rules P.
        start: The start symbol S (must be in ``nonterminals``).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = "grammar"
    nonterminals: list[str]
    terminals: list[str]
    productions: list[Production]
    start: str

    @model_validator(mode="after")
    def _validate(self) -> Self:
        nt_set = set(self.nonterminals)
        t_set = set(self.terminals)
        if len(nt_set) != len(self.nonterminals):
            raise ValueError("Duplicate nonterminal symbols")
        if len(t_set) != len(self.terminals):
            raise ValueError("Duplicate terminal symbols")
        if "" in nt_set or "" in t_set:
            raise ValueError("CFG symbols must be non-empty strings")
        overlap = nt_set & t_set
        if overlap:
            raise ValueError(
                f"nonterminals and terminals must be disjoint; overlap: {sorted(overlap)}",
            )
        vocab = nt_set | t_set
        if self.start not in nt_set:
            raise ValueError(f"Start symbol {self.start!r} is not a nonterminal")
        for prod in self.productions:
            if prod.head not in nt_set:
                raise ValueError(
                    f"Production head {prod.head!r} is not a nonterminal",
                )
            for sym in prod.body:
                if sym not in vocab:
                    raise ValueError(
                        f"Production body symbol {sym!r} is neither terminal nor nonterminal",
                    )
        return self

    def productions_for(self, nonterminal: str) -> list[Production]:
        """Return every production whose head is ``nonterminal``."""
        return [p for p in self.productions if p.head == nonterminal]
