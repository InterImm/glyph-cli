"""Reading a page as a knowledge graph (grammar rules 3 and 5).

Rule 3: the first band of every line is one edge, node | relation | node. The
same word on two lines is the same node, and a lone ONE in a node slot means
"that", the statement on the line above.

Rule 5: every part in a lower band answers the nearest drawn part above it in
the same position: the same part is *yes*, NOT is *no*, a different part is
*instead*, a part under an empty position is *and also*.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .page import SLOTS, Page
from .script import Half, Vocabulary, Word

HALVES = ("kind", "which")
THAT = Word("ONE", None)


@dataclass
class Node:
    word: str | None = None
    gloss: str = ""
    statement: int | None = None  # set when the node is "that": edge number it points at

    def label(self) -> str:
        if self.statement is not None:
            return f"[statement {self.statement}]" if self.statement else "[that: nothing above]"
        return self.gloss


@dataclass
class Response:
    slot: str
    half: str
    meaning: str  # yes | no | instead | and also
    part: str
    to: str | None  # symbol of the voice answered, None when answering an empty position

    def text(self, vocab: Vocabulary) -> str:
        tail = "" if self.meaning in ("yes", "no") else f' "{self.part}"'
        to = f" (to {self.to})" if self.to else ""
        return f"{self.slot}.{self.half}: {self.meaning}{tail}{to}"


@dataclass
class Reply:
    symbol: str
    responses: list[Response] = field(default_factory=list)


@dataclass
class Edge:
    number: int
    symbol: str
    subject: Node
    relation: str
    relation_word: str
    object: Node
    replies: list[Reply] = field(default_factory=list)


@dataclass
class Graph:
    edges: list[Edge] = field(default_factory=list)
    nodes: dict[str, str] = field(default_factory=dict)  # word -> gloss

    def to_json(self) -> dict:
        return {"edges": [asdict(e) for e in self.edges], "nodes": self.nodes}


def respond(above: Half, below: Half) -> str | None:
    if below is None:
        return None
    if above is None:
        return "and also"
    if below == above:
        return "yes"
    if below == "NOT":
        return "no"
    return "instead"


def read_graph(vocab: Vocabulary, page: Page) -> Graph:
    g = Graph()
    for i, line in enumerate(page.lines, 1):
        st = line.statement
        subject_w, relation_w, object_w = st.words

        def node(word: Word, i: int = i) -> Node:
            if word == THAT:
                return Node(statement=i - 1)
            gloss = vocab.gloss(word)
            if not word.is_empty:
                g.nodes.setdefault(str(word), gloss)
            return Node(str(word) if not word.is_empty else None, gloss)

        relation = vocab.gloss(relation_w, role="relation")
        edge = Edge(i, st.symbol, node(subject_w), relation, str(relation_w), node(object_w))
        for b, band in enumerate(line.bands[1:], 1):
            reply = Reply(band.symbol)
            for pos, below in enumerate(band.halves):
                above, by = None, None
                for prev in reversed(line.bands[:b]):
                    if prev.halves[pos] is not None:
                        above, by = prev.halves[pos], prev.symbol
                        break
                meaning = respond(above, below)
                if meaning:
                    reply.responses.append(Response(SLOTS[pos // 2], HALVES[pos % 2], meaning, vocab.thing(below), by))
            edge.replies.append(reply)
        g.edges.append(edge)
    return g


def format_graph(vocab: Vocabulary, g: Graph) -> list[str]:
    out = ["Edges:"]
    for e in g.edges:
        out.append(f"{e.number}. ({e.symbol}) {e.subject.label()} --{e.relation}--> {e.object.label()}")
        for r in e.replies:
            text = "; ".join(x.text(vocab) for x in r.responses) or "present, no comment"
            out.append(f"   ({r.symbol}) {text}")
    out += ["", "Nodes:"]
    out += [f"  {word:<14} {gloss}" for word, gloss in g.nodes.items()]
    return out


def to_dot(g: Graph) -> str:
    """Graphviz DOT, for anyone who wants to draw the graph."""

    def nid(n: Node) -> str:
        return f'"statement {n.statement}"' if n.statement is not None else f'"{n.word or "_"}"'

    def q(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    lines = ["digraph page {", "  rankdir=LR;"]
    for word, gloss in g.nodes.items():
        lines.append(f'  "{word}" [label="{q(gloss)}"];')
    for e in g.edges:
        label = q(f"{e.number}. {e.relation} ({e.symbol})")
        lines.append(f'  {nid(e.subject)} -> {nid(e.object)} [label="{label}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"
