"""JFLAP `.jff` (XML) reader and writer.

Summary (UA): Збереження та завантаження автоматів у форматі JFLAP ``.jff``
(XML). Підтримка: DFA/NFA/ε-NFA (``<type>fa</type>``), PDA, Мілі, Мура,
одностpічкова ТМ. ``ε``-рядки ↔ порожні XML-теги ``<read></read>``.
Summary (EN): Save/load automata in JFLAP's ``.jff`` XML format. Supports:
DFA/NFA/ε-NFA (``<type>fa</type>``), PDA, Mealy, Moore, single-tape TM.
ε-transitions map to empty ``<read></read>`` tags (JFLAP's convention).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from automata_simulator.core.models import (
    EPSILON,
    Automaton,
    AutomatonType,
    FATransition,
    MealyTransition,
    MooreTransition,
    PDATransition,
    Position,
    State,
    TapeMove,
    TMTransition,
    Transition,
)

_JFLAP_TYPE: dict[AutomatonType, str] = {
    AutomatonType.DFA: "fa",
    AutomatonType.NFA: "fa",
    AutomatonType.EPSILON_NFA: "fa",
    AutomatonType.MEALY: "mealy",
    AutomatonType.MOORE: "moore",
    AutomatonType.PDA: "pda",
    AutomatonType.TM: "turing",
}


# -------------------------------------------------------------------------- encode
def automaton_to_jff(automaton: Automaton) -> str:
    """Serialise ``automaton`` into a JFLAP ``.jff`` XML string."""
    root = ET.Element("structure")
    ET.SubElement(root, "type").text = _JFLAP_TYPE[automaton.type]
    auto_el = ET.SubElement(root, "automaton")

    id_map = {s.id: str(i) for i, s in enumerate(automaton.states)}
    for state in automaton.states:
        s_el = ET.SubElement(
            auto_el,
            "state",
            id=id_map[state.id],
            name=state.id,
        )
        pos = state.position or Position()
        ET.SubElement(s_el, "x").text = str(pos.x)
        ET.SubElement(s_el, "y").text = str(pos.y)
        if state.id == automaton.initial_state:
            ET.SubElement(s_el, "initial")
        if state.id in automaton.accepting_states:
            ET.SubElement(s_el, "final")
        if automaton.type is AutomatonType.MOORE and state.moore_output is not None:
            ET.SubElement(s_el, "output").text = state.moore_output

    for tr in automaton.transitions:
        t_el = ET.SubElement(auto_el, "transition")
        ET.SubElement(t_el, "from").text = id_map[tr.source]
        ET.SubElement(t_el, "to").text = id_map[tr.target]
        _encode_transition_body(t_el, tr)

    return ET.tostring(root, encoding="unicode")


def save_jff(automaton: Automaton, path: Path) -> None:
    """Write ``automaton`` to ``path`` in JFLAP XML."""
    path.write_text(automaton_to_jff(automaton), encoding="utf-8")


def _encode_transition_body(parent: ET.Element, tr: Transition) -> None:
    if isinstance(tr, FATransition):
        read_el = ET.SubElement(parent, "read")
        if tr.read != EPSILON:
            read_el.text = tr.read
    elif isinstance(tr, MealyTransition):
        ET.SubElement(parent, "read").text = tr.read
        ET.SubElement(parent, "transout").text = tr.write
    elif isinstance(tr, MooreTransition):
        ET.SubElement(parent, "read").text = tr.read
    elif isinstance(tr, PDATransition):
        read_el = ET.SubElement(parent, "read")
        if tr.read != EPSILON:
            read_el.text = tr.read
        pop_el = ET.SubElement(parent, "pop")
        if tr.pop != EPSILON:
            pop_el.text = tr.pop
        push_el = ET.SubElement(parent, "push")
        if tr.push:
            push_el.text = "".join(tr.push)
    elif isinstance(tr, TMTransition):
        # MVP: single-tape support only.
        ET.SubElement(parent, "read").text = tr.read[0]
        ET.SubElement(parent, "write").text = tr.write[0]
        ET.SubElement(parent, "move").text = tr.move[0].value


# -------------------------------------------------------------------------- decode
def automaton_from_jff(text: str) -> Automaton:  # noqa: PLR0912, PLR0915 — single XML walker is clearest
    """Parse a JFLAP ``.jff`` XML document into an :class:`Automaton`."""
    root = ET.fromstring(text)
    type_el = root.find("type")
    auto_el = root.find("automaton")
    if type_el is None or type_el.text is None or auto_el is None:
        raise ValueError("Malformed JFLAP document: missing <type> or <automaton>")
    jflap_type = type_el.text.strip()

    states_by_jflap_id: dict[str, State] = {}
    initial_state: str | None = None
    accepting: list[str] = []
    alphabet: set[str] = set()
    stack_alphabet: set[str] = set()
    tape_alphabet: set[str] = set()
    output_alphabet: set[str] = set()
    transitions: list[Transition] = []

    for s_el in auto_el.findall("state"):
        jid = s_el.get("id") or ""
        name = s_el.get("name") or f"q{jid}"
        position: Position | None = None
        x_el = s_el.find("x")
        y_el = s_el.find("y")
        if x_el is not None and y_el is not None and x_el.text and y_el.text:
            position = Position(x=float(x_el.text), y=float(y_el.text))
        is_initial = s_el.find("initial") is not None
        is_accepting = s_el.find("final") is not None
        moore_output_el = s_el.find("output")
        moore_output = moore_output_el.text if moore_output_el is not None else None
        if moore_output is not None:
            output_alphabet.add(moore_output)
        state = State(
            id=name,
            is_initial=is_initial,
            is_accepting=is_accepting,
            moore_output=moore_output,
            position=position,
        )
        states_by_jflap_id[jid] = state
        if is_initial:
            initial_state = name
        if is_accepting:
            accepting.append(name)

    for tr_el in auto_el.findall("transition"):
        src_jid = (tr_el.findtext("from") or "").strip()
        tgt_jid = (tr_el.findtext("to") or "").strip()
        src = states_by_jflap_id[src_jid].id
        tgt = states_by_jflap_id[tgt_jid].id
        tr_obj = _decode_transition(
            jflap_type,
            tr_el,
            src,
            tgt,
            alphabet,
            stack_alphabet,
            tape_alphabet,
            output_alphabet,
        )
        transitions.append(tr_obj)

    if initial_state is None:
        # Fallback: take the first state.
        initial_state = next(iter(states_by_jflap_id.values())).id

    automaton_type = _classify_automaton_type(jflap_type, transitions)

    kwargs: dict[str, object] = {
        "type": automaton_type,
        "name": "imported",
        "states": list(states_by_jflap_id.values()),
        "alphabet": sorted(alphabet),
        "initial_state": initial_state,
        "accepting_states": sorted(accepting),
        "transitions": transitions,
    }
    if automaton_type in (AutomatonType.MEALY, AutomatonType.MOORE):
        kwargs["output_alphabet"] = sorted(output_alphabet)
    if automaton_type is AutomatonType.PDA:
        # Choose a stack-bottom symbol that appears in stack alphabet, or synthesise one.
        if "Z" not in stack_alphabet:
            stack_alphabet.add("Z")
        kwargs["stack_alphabet"] = sorted(stack_alphabet)
        kwargs["stack_start"] = "Z"
    if automaton_type is AutomatonType.TM:
        blank = "□"
        if blank not in tape_alphabet:
            tape_alphabet.add(blank)
        kwargs["tape_alphabet"] = sorted(tape_alphabet)
        kwargs["blank_symbol"] = blank
        kwargs["tape_count"] = 1
    return Automaton(**kwargs)  # type: ignore[arg-type]


def load_jff(path: Path) -> Automaton:
    """Load a JFLAP ``.jff`` file."""
    return automaton_from_jff(path.read_text(encoding="utf-8"))


def _decode_transition(
    jflap_type: str,
    tr_el: ET.Element,
    src: str,
    tgt: str,
    alphabet: set[str],
    stack_alphabet: set[str],
    tape_alphabet: set[str],
    output_alphabet: set[str],
) -> Transition:
    read_text = _nonempty(tr_el.findtext("read"))
    if jflap_type == "fa":
        if read_text is None:
            return FATransition(source=src, target=tgt, read=EPSILON)
        alphabet.add(read_text)
        return FATransition(source=src, target=tgt, read=read_text)
    if jflap_type == "mealy":
        read = read_text or ""
        write = _nonempty(tr_el.findtext("transout")) or ""
        alphabet.add(read)
        output_alphabet.add(write)
        return MealyTransition(source=src, target=tgt, read=read, write=write)
    if jflap_type == "moore":
        read = read_text or ""
        alphabet.add(read)
        return MooreTransition(source=src, target=tgt, read=read)
    if jflap_type == "pda":
        read = read_text if read_text is not None else EPSILON
        pop_raw = _nonempty(tr_el.findtext("pop"))
        pop = pop_raw if pop_raw is not None else EPSILON
        push_raw = _nonempty(tr_el.findtext("push"))
        push: tuple[str, ...] = tuple(push_raw) if push_raw else ()
        if read != EPSILON:
            alphabet.add(read)
        if pop != EPSILON:
            stack_alphabet.add(pop)
        for sym in push:
            stack_alphabet.add(sym)
        return PDATransition(source=src, target=tgt, read=read, pop=pop, push=push)
    if jflap_type == "turing":
        read = read_text or "□"
        write = _nonempty(tr_el.findtext("write")) or read
        move_text = (_nonempty(tr_el.findtext("move")) or "S").upper()
        move = TapeMove(move_text if move_text in {"L", "R", "S"} else "S")
        alphabet.add(read)
        tape_alphabet.add(read)
        tape_alphabet.add(write)
        return TMTransition(
            source=src,
            target=tgt,
            read=(read,),
            write=(write,),
            move=(move,),
        )
    raise ValueError(f"Unsupported JFLAP automaton type: {jflap_type!r}")


def _nonempty(text: str | None) -> str | None:
    if text is None:
        return None
    stripped = text.strip()
    return stripped if stripped else None


def _classify_automaton_type(  # noqa: PLR0911 — one return per JFLAP type tag is readable
    jflap_type: str, transitions: list[Transition],
) -> AutomatonType:
    """For JFLAP ``fa`` type, narrow to DFA / NFA / EPSILON_NFA heuristically."""
    if jflap_type == "mealy":
        return AutomatonType.MEALY
    if jflap_type == "moore":
        return AutomatonType.MOORE
    if jflap_type == "pda":
        return AutomatonType.PDA
    if jflap_type == "turing":
        return AutomatonType.TM
    # "fa" — narrow it.
    fa_trs = [tr for tr in transitions if isinstance(tr, FATransition)]
    if any(tr.read == EPSILON for tr in fa_trs):
        return AutomatonType.EPSILON_NFA
    seen: set[tuple[str, str]] = set()
    for tr in fa_trs:
        key = (tr.source, tr.read)
        if key in seen:
            return AutomatonType.NFA
        seen.add(key)
    return AutomatonType.DFA
