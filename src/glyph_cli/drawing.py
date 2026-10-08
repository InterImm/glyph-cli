"""Drawing pages on the grid, and reading drawings back.

Rule 1 of the grammar: spacing is structure. Every mark is a whole 3x3 part.
Parts of one word are 1 empty cell apart, the words of a triplet 2, triplets 4.
Bands of one line are 1 empty row apart; lines are 3 empty rows apart.
"""

from __future__ import annotations

from html import escape

from .page import Band, Page, Triplet, check_symbol
from .script import NUMBER, GlyphError, Half, Vocabulary, Word

GAP_PART = 1  # between the parts of a word
GAP_WORD = 2  # between the words of a triplet
GAP_TRIPLET = 4  # between triplets on a line
BAND_GAP = 1  # rows between the bands (voices) of a line
LINE_GAP = 3  # rows between lines
PER_LINE = 2  # triplets per drawn line, unless asked otherwise
EMPTY_CELL = "."
MARK = "#"

#: Colours of the phase 2 ("137") design: signal blue, white-cyan for them, Sol yellow for us.
BACKGROUND = "#0d1457"
GRID = "#141d6e"
INKS = {"+": "#9ff8ff", "×": "#ffd84a", "x": "#ffd84a"}
OTHER_INKS = ["#c9b3ff", "#7dffa8", "#ffa45c", "#ffffff"]


# ---------- shapes ----------


def number_shape(n: int) -> tuple[str, str, str]:
    """One base-512 digit: nine bits, 256 ... 1, left to right, top to bottom."""
    bits = format(n, "09b")
    return tuple("".join(MARK if bits[r * 3 + c] == "1" else EMPTY_CELL for c in range(3)) for r in range(3))  # type: ignore[return-value]


def shape(vocab: Vocabulary, half: Half) -> tuple[str, str, str]:
    if half is None:
        return (EMPTY_CELL * 3,) * 3  # type: ignore[return-value]
    if isinstance(half, int):
        return number_shape(half)
    return vocab.parts[half].shape


def width(positions: int) -> int:
    """Cells taken by a run of positions inside one word."""
    return 4 * positions - GAP_PART if positions else 0


def band_rows(vocab: Vocabulary, positions: list[Half], symbol: str) -> list[str]:
    """Three rows of text for the positions of one word drawn in one symbol."""
    rows = ["", "", ""]
    for i, half in enumerate(positions):
        s = shape(vocab, half)
        for r in range(3):
            rows[r] += (EMPTY_CELL * GAP_PART if i else "") + s[r].replace(MARK, symbol)
    return rows


def draw_words(vocab: Vocabulary, words: list[Word], symbol: str = "+", spacing: int = 3) -> list[str]:
    """Words side by side, as a quick look-up drawing (not a page)."""
    blocks = [band_rows(vocab, w.positions, symbol) for w in words]
    return [(" " * spacing).join(b[r] for b in blocks) for r in range(3)]


# ---------- pages ----------


def triplet_rows(vocab: Vocabulary, triplet: Triplet, voices: int) -> list[str]:
    """One triplet with ``voices`` bands. Each slot is as wide as its longest word."""
    widths = triplet.widths()
    xs, x = [], 0
    for w in widths:
        xs.append(x)
        x += width(w) + GAP_WORD
    total = x - GAP_WORD
    out: list[str] = []
    for k in range(voices):
        if k:
            out += [EMPTY_CELL * total] * BAND_GAP
        band = [[EMPTY_CELL] * total for _ in range(3)]
        if k < len(triplet.bands):
            b = triplet.bands[k]
            for slot, word in enumerate(b.words):
                if word.is_empty:
                    continue
                for r, row in enumerate(band_rows(vocab, word.positions, b.symbol)):
                    for j, ch in enumerate(row):
                        if ch != EMPTY_CELL:
                            band[r][xs[slot] + j] = ch
        out += ["".join(r) for r in band]
    return out


def render(vocab: Vocabulary, page: Page, per_line: int = PER_LINE) -> list[str]:
    """Draw a page as rows of text.

    Triplets run left to right, ``per_line`` to a line, 4 empty cells apart. Every
    triplet gets as many bands as the page has voices. Rows are padded to one width.
    """
    if per_line < 1:
        raise GlyphError("per_line must be at least 1")
    n = page.voices
    grids = [triplet_rows(vocab, t, n) for t in page.triplets]
    out: list[str] = []
    for i in range(0, len(grids), per_line):
        if i:
            out += [""] * LINE_GAP
        row = grids[i : i + per_line]
        out += [(EMPTY_CELL * GAP_TRIPLET).join(g[r] for g in row) for r in range(len(row[0]))]
    w = max((len(r) for r in out), default=0)
    return [r.ljust(w, EMPTY_CELL) for r in out]


def hidden_zeros(page: Page, per_line: int = PER_LINE) -> list[int]:
    """Triplets whose last word is a number ending in a 0 digit at the end of a drawn line.

    A 0 digit is a blank position, so there the reader cannot see where the number ends.
    """
    out = []
    for i, t in enumerate(page.triplets, 1):
        if i % per_line and i != len(page.triplets):
            continue
        for b in t.bands:
            w = b.words[2]
            if w.is_number and len(w.digits) > 1 and w.digits[-1] == 0:
                out.append(i)
                break
    return out


def ink(symbol: str, symbols: list[str]) -> str:
    if symbol in INKS:
        return INKS[symbol]
    others = [s for s in symbols if s not in INKS]
    return OTHER_INKS[others.index(symbol) % len(OTHER_INKS)]


def render_svg(
    vocab: Vocabulary, page: Page, cell: int = 12, pad: int = 1, grid: bool = True, per_line: int = PER_LINE
) -> str:
    """Draw a page as SVG: square pixels on signal blue, no curves."""
    rows = render(vocab, page, per_line)
    symbols = page.symbols()
    w, h = (len(rows[0]) if rows else 0) + 2 * pad, len(rows) + 2 * pad
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w * cell} {h * cell}" '
        f'width="{w * cell}" height="{h * cell}" shape-rendering="crispEdges">',
        f'<rect width="100%" height="100%" fill="{BACKGROUND}"/>',
    ]
    inset = max(1, cell // 12)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            x, y = (c + pad) * cell + inset, (r + pad) * cell + inset
            size = cell - 2 * inset
            box = f'x="{x}" y="{y}" width="{size}" height="{size}"'
            if ch != EMPTY_CELL:
                out.append(f'<rect {box} fill="{ink(ch, symbols)}"><title>{escape(ch)}</title></rect>')
            elif grid:
                out.append(f'<rect {box} fill="{GRID}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ---------- reading a drawing back ----------


def _structure(rows: list[str]) -> int:
    """Find how many bands each line has, from where the empty rows fall."""
    empty = [not row.strip(EMPTY_CELL) for row in rows]
    total = len(rows)
    for n in range(1, total + 1):
        line_h = 4 * n - 1
        period = line_h + LINE_GAP
        if (total + LINE_GAP) % period:
            continue
        ok = True
        for i in range(total):
            at = i % period
            gap = at >= line_h or (at % 4 == 3)
            if gap and not empty[i]:
                ok = False
                break
        if ok:
            return n
    raise GlyphError("the rows don't fall into lines and bands; is this a picture rather than text?")


def _bits(pattern: tuple[str, ...]) -> int:
    return int("".join(pattern).replace(EMPTY_CELL, "0").replace(MARK, "1"), 2)


class _LineReader:
    """Split one drawn line into triplets and words.

    The gaps say where everything is: 1 empty column inside a word, 2 between words,
    4 between triplets. Some parts (ONE, BEFORE, AFTER) and number digits have empty
    columns of their own, so a gap can look a cell wider than it is: ONE moved one
    cell left is BEFORE, one cell right is AFTER. The reader finds every layout in
    which each position is a part (or a digit, in a number) and keeps the one whose
    statements read best against the vocabulary, like the translating machine of the
    story leaning on its lexicon. It can be wrong; that is part of the story.
    """

    LIMIT = 64  # layouts kept per starting point; real lines have one or two

    def __init__(self, vocab: Vocabulary, bands: list[list[str]]):
        self.vocab = vocab
        self.bands = bands
        self.width = len(bands[0][0])
        self.by_shape = {p.shape: p.name for p in vocab.parts.values()}
        self.filled = [any(row[c] != EMPTY_CELL for band in bands for row in band) for c in range(self.width)]
        self.memo: dict[tuple[int, int], list[list]] = {}

    def empty(self, start: int, stop: int) -> bool:
        return stop <= self.width and not any(self.filled[start:stop])

    def pattern(self, k: int, x: int) -> tuple[str, ...]:
        cells = (row[x : x + 3] for row in self.bands[k])
        return tuple("".join(MARK if ch != EMPTY_CELL else EMPTY_CELL for ch in c) for c in cells)

    def slot(self, x: int, p: int) -> list[Word] | None:
        """The words each band draws in a slot of ``p`` positions at column ``x``, or None if they aren't words."""
        words: list[Word] = []
        number_above = False
        last_used = False
        for k in range(len(self.bands)):
            pats = [self.pattern(k, x + 4 * j) for j in range(p)]
            drawn = [any(MARK in r for r in pat) for pat in pats]
            if not any(drawn):
                words.append(Word())
                continue
            last_used = last_used or drawn[-1]
            kind = self.by_shape.get(pats[0]) if drawn[0] else None
            if drawn[0] and kind is None:
                return None
            if kind == NUMBER or (kind is None and number_above):
                digits = [_bits(pat) for pat in pats[1:]]
                if kind == NUMBER:
                    last_used = last_used or p > 1
                    while digits and digits[0] == 0:
                        digits.pop(0)
                else:
                    while digits and digits[-1] == 0:
                        digits.pop()
                which = None if not digits else digits[0] if len(digits) == 1 else tuple(digits)
                words.append(Word(kind, which))
                number_above = number_above or kind == NUMBER
                continue
            if p > 2 and any(drawn[2:]):
                return None
            which = None
            if p > 1 and drawn[1]:
                which = self.by_shape.get(pats[1])
                if which is None:
                    return None
            words.append(Word(kind, which))
        if p > 1 and not last_used:
            return None
        return words

    def read(self) -> list | None:
        """The best layout of the line: a list of triplets, each 3 slots of (start, end, words per band)."""
        layouts = self.layouts(0, 0)
        return max(layouts, key=self.score) if layouts else None

    def score(self, layout: list) -> int:
        """How many statement words read as known words (first band of each triplet)."""
        total = 0
        for slots in layout:
            words = [next((w for w in s[2] if not w.is_empty), Word()) for s in slots]
            for i, w in enumerate(words):
                if i == 1:
                    part = self.vocab.parts.get(w.kind) if w.kind else None
                    total += bool(part and part.relation) and (w.which is None or str(w.which) in self.vocab.markers)
                else:
                    total += w.kind == NUMBER or w.which is None or self.vocab.lookup(w) is not None
        return total

    def layouts(self, x: int, slot: int) -> list[list]:
        key = (x, slot)
        if key not in self.memo:
            self.memo[key] = self._layouts(x, slot)[: self.LIMIT]
        return self.memo[key]

    def _layouts(self, x: int, slot: int) -> list[list]:
        found: list[list] = []
        p = 1
        while x + width(p) <= self.width:
            if p > 1 and self.filled[x + width(p - 1)]:
                break  # a mark where the 1-cell gap inside a word must be
            words = self.slot(x, p)
            end = x + width(p)
            if words is not None:
                here = (x, end, words)
                if slot < 2:
                    if self.empty(end, end + GAP_WORD):
                        found += [[[here, *rest[0]], *rest[1:]] for rest in self.layouts(end + GAP_WORD, slot + 1)]
                elif self.empty(end, self.width):
                    found.append([[here]])
                elif self.empty(end, end + GAP_TRIPLET):
                    found += [[[here], *rest] for rest in self.layouts(end + GAP_TRIPLET, 0)]
            p += 1
        return found


def decode(vocab: Vocabulary, text: str) -> Page:
    """Read a drawing (as made by :func:`render`) back into a page.

    A position after COUNT is read as nine bits, and so is a position with no
    kind under a number (a reply like ``_.12``); everywhere else it must be a part.
    """
    rows = [r.strip() for r in text.splitlines() if r.strip()]
    if not rows:
        return Page()
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, EMPTY_CELL) for r in rows]
    n = _structure(rows)
    period = 4 * n - 1 + LINE_GAP
    page = Page()
    for top in range(0, len(rows), period):
        bands = [rows[top + 4 * k : top + 4 * k + 3] for k in range(n)]
        layout = _LineReader(vocab, bands).read()
        if layout is None:
            raise GlyphError(
                f"rows {top + 1}-{top + 4 * n - 1}: the marks don't split into 3x3 parts with 1, 2 and 4 cell gaps "
                "(a picture rather than text?)"
            )
        for slots in layout:
            start, stop = slots[0][0], slots[-1][1]
            triplet = Triplet()
            for k in range(n):
                words = tuple(s[2][k] for s in slots)
                if all(word.is_empty for word in words):
                    continue
                marks = {ch for row in bands[k] for ch in row[start:stop] if ch != EMPTY_CELL}
                if len(marks) > 1:
                    r0 = top + 4 * k
                    raise GlyphError(f"rows {r0 + 1}-{r0 + 3}: one band mixes symbols {' '.join(sorted(marks))}")
                triplet.bands.append(Band(check_symbol(marks.pop()), words))  # type: ignore[arg-type]
            if triplet.bands:
                page.triplets.append(triplet)
    return page
