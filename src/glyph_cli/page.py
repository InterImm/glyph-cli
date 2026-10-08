"""Page source: the plain-text form of a page.

One band per line, ``SYMBOL: node | relation | node``. A block of bands is one
triplet: the first band is the statement (one edge of the graph), the bands
under it are other voices replying, part by part. A blank line starts the next
triplet. ``#`` starts a comment. How many triplets go on one drawn line is a
choice made when drawing, not part of the source.

    +: BODY.OTHER | ONE | BODY.AIR     # their statement: your world is an air-world
    ×: _ | _ | _.WATER                 # our reply: water instead of air
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .script import GlyphError, Vocabulary, Word

#: Characters that cannot be a party's symbol: they mean something in the formats.
RESERVED_SYMBOLS = set(".#|:_ \t")

SLOTS = ("subject", "relation", "object")


@dataclass(frozen=True)
class Band:
    """One voice's row of marks within a line."""

    symbol: str
    words: tuple[Word, Word, Word]

    @property
    def positions(self) -> list[list]:
        """The lattice positions of each slot, left to right."""
        return [w.positions for w in self.words]


@dataclass
class Triplet:
    """One triplet (node, relation, node): a statement band and the voices that answer it."""

    bands: list[Band] = field(default_factory=list)

    @property
    def statement(self) -> Band:
        return self.bands[0]

    @property
    def replies(self) -> list[Band]:
        return self.bands[1:]

    def widths(self) -> list[int]:
        """Positions per slot: as many as the longest word any band puts there."""
        return [max(len(b.words[i].positions) for b in self.bands) for i in range(3)]


@dataclass
class Page:
    triplets: list[Triplet] = field(default_factory=list)

    @property
    def voices(self) -> int:
        """The most bands any triplet has: every line is drawn this tall."""
        return max((len(t.bands) for t in self.triplets), default=0)

    def symbols(self) -> list[str]:
        out: list[str] = []
        for t in self.triplets:
            for band in t.bands:
                if band.symbol not in out:
                    out.append(band.symbol)
        return out


def check_symbol(symbol: str) -> str:
    if len(symbol) != 1 or symbol in RESERVED_SYMBOLS:
        reserved = " ".join(sorted(RESERVED_SYMBOLS - {" ", "\t"}))
        raise GlyphError(f"a symbol is one character, not a space or any of {reserved}: {symbol!r}")
    return symbol


def parse_page(text: str, vocab: Vocabulary) -> Page:
    """Read page source into a :class:`Page`."""
    page, current = Page(), Triplet()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            if current.bands:
                page.triplets.append(current)
                current = Triplet()
            continue
        symbol, sep, rest = line.partition(":")
        where = f"line {number}"
        if not sep:
            raise GlyphError(f'{where}: expected "SYMBOL: node | relation | node", got {raw.strip()!r}')
        try:
            check_symbol(symbol.strip())
        except GlyphError as exc:
            raise GlyphError(f"{where}: {exc}") from None
        cells = rest.split("|")
        if len(cells) != 3:
            raise GlyphError(f"{where}: need exactly three slots separated by |, got {len(cells)}")
        try:
            words = tuple(vocab.parse(c) for c in cells)
        except GlyphError as exc:
            raise GlyphError(f"{where}: {exc}") from None
        current.bands.append(Band(symbol.strip(), words))  # type: ignore[arg-type]
    if current.bands:
        page.triplets.append(current)
    return page


def format_page(page: Page) -> str:
    """Write a :class:`Page` back as page source."""
    blocks = []
    for t in page.triplets:
        blocks.append("\n".join(f"{b.symbol}: " + " | ".join(str(w) for w in b.words) for b in t.bands))
    return "\n\n".join(blocks) + ("\n" if blocks else "")
