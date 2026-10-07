"""Drawing pages on the lattice, and reading drawings back.

Rule 1 of the grammar: every mark is a whole 3x3 part in a lattice position,
positions are one empty cell apart, so a line is 6 positions (23 cells) wide.
Bands of one line are one empty row apart; lines are three empty rows apart.
"""

from __future__ import annotations

from html import escape

from .page import Band, Line, Page, check_symbol
from .script import GlyphError, Half, Vocabulary, Word

POSITIONS = 6
WIDTH = POSITIONS * 4 - 1  # 23 cells
BAND_GAP = 1
LINE_GAP = 3
EMPTY_CELL = "."
MARK = "#"

#: Colours of the phase 2 ("137") design: signal blue, white-cyan for them, Sol yellow for us.
BACKGROUND = "#0d1457"
GRID = "#141d6e"
INKS = {"+": "#9ff8ff", "×": "#ffd84a", "x": "#ffd84a"}
OTHER_INKS = ["#c9b3ff", "#7dffa8", "#ffa45c", "#ffffff"]


# ---------- shapes ----------


def number_shape(n: int) -> tuple[str, str, str]:
    """Nine bits, 256 ... 1, left to right, top to bottom."""
    bits = format(n, "09b")
    return tuple("".join(MARK if bits[r * 3 + c] == "1" else EMPTY_CELL for c in range(3)) for r in range(3))  # type: ignore[return-value]


def shape(vocab: Vocabulary, half: Half) -> tuple[str, str, str]:
    if half is None:
        return (EMPTY_CELL * 3,) * 3  # type: ignore[return-value]
    if isinstance(half, int):
        return number_shape(half)
    return vocab.parts[half].shape


def band_rows(vocab: Vocabulary, halves: list[Half], symbol: str) -> list[str]:
    """Three rows of text for a run of positions drawn in one symbol."""
    rows = ["", "", ""]
    for i, half in enumerate(halves):
        s = shape(vocab, half)
        for r in range(3):
            rows[r] += (EMPTY_CELL if i else "") + s[r].replace(MARK, symbol)
    return rows


def draw_words(vocab: Vocabulary, words: list[Word], symbol: str = "+", spacing: int = 3) -> list[str]:
    """Words side by side, as a quick look-up drawing (not a page)."""
    blocks = [band_rows(vocab, list(w.halves), symbol) for w in words]
    return [(" " * spacing).join(b[r] for b in blocks) for r in range(3)]


# ---------- pages ----------


def render(vocab: Vocabulary, page: Page) -> list[str]:
    """Draw a page as rows of text. Every line gets as many bands as the page has voices."""
    blank = EMPTY_CELL * WIDTH
    n = page.voices
    out: list[str] = []
    for li, line in enumerate(page.lines):
        if li:
            out += [blank] * LINE_GAP
        for k in range(n):
            if k:
                out += [blank] * BAND_GAP
            if k < len(line.bands):
                band = line.bands[k]
                out += band_rows(vocab, band.halves, band.symbol)
            else:
                out += [blank] * 3
    return out


def ink(symbol: str, symbols: list[str]) -> str:
    if symbol in INKS:
        return INKS[symbol]
    others = [s for s in symbols if s not in INKS]
    return OTHER_INKS[others.index(symbol) % len(OTHER_INKS)]


def render_svg(vocab: Vocabulary, page: Page, cell: int = 12, pad: int = 1, grid: bool = True) -> str:
    """Draw a page as SVG: square pixels on signal blue, no curves."""
    rows = render(vocab, page)
    symbols = page.symbols()
    w, h = WIDTH + 2 * pad, len(rows) + 2 * pad
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


def _which(vocab: Vocabulary, pattern: tuple[str, ...], kind: Half, slot: int, statement_kind: Half) -> Half:
    by_shape = {p.shape: p.name for p in vocab.parts.values()}
    named = by_shape.get(pattern)
    numeric = slot != 1 and (kind == "ONE" or (kind is None and statement_kind == "ONE"))
    if numeric:
        if named and (named == "OPEN" or vocab.lookup(Word("ONE", named))):
            return named
        bits = "".join(pattern).replace(EMPTY_CELL, "0").replace(MARK, "1")
        return int(bits, 2)
    return named


def decode(vocab: Vocabulary, text: str) -> Page:
    """Read a drawing (as made by :func:`render`) back into a page.

    Ambiguity: in a node slot whose kind is ONE, a which that is both a part
    and a number reads as the part only when ONE.PART is a vocabulary word (or
    OPEN, "how many?"); otherwise it reads as the number.
    """
    rows = [r.strip() for r in text.splitlines() if r.strip()]
    if not rows:
        return Page()
    for i, row in enumerate(rows, 1):
        if len(row) != WIDTH:
            raise GlyphError(f"row {i} is {len(row)} cells wide; text is always {WIDTH} (off the lattice: a picture?)")
        for c in range(3, WIDTH, 4):
            if row[c] != EMPTY_CELL:
                raise GlyphError(f"row {i}, column {c + 1}: a mark between lattice positions (a picture?)")
    n = _structure(rows)
    period = 4 * n - 1 + LINE_GAP
    by_shape = {p.shape: p.name for p in vocab.parts.values()}
    page = Page()
    for top in range(0, len(rows), period):
        line = Line()
        for k in range(n):
            r0 = top + 4 * k
            band = rows[r0 : r0 + 3]
            marks = {ch for row in band for ch in row if ch != EMPTY_CELL}
            if not marks:
                continue
            if len(marks) > 1:
                raise GlyphError(f"rows {r0 + 1}-{r0 + 3}: one band mixes symbols {' '.join(sorted(marks))}")
            symbol = check_symbol(marks.pop())
            halves: list[Half] = []
            for pos in range(POSITIONS):
                pattern = tuple(
                    "".join(MARK if ch != EMPTY_CELL else EMPTY_CELL for ch in row[pos * 4 : pos * 4 + 3])
                    for row in band
                )
                if not any(MARK in p for p in pattern):
                    halves.append(None)
                    continue
                slot = pos // 2
                if pos % 2 == 0:
                    name = by_shape.get(pattern)
                    if name is None:
                        raise GlyphError(f"rows {r0 + 1}-{r0 + 3}, position {pos + 1}: not a part")
                    halves.append(name)
                else:
                    statement_kind = line.bands[0].words[slot].kind if line.bands else None
                    which = _which(vocab, pattern, halves[-1], slot, statement_kind)
                    if which is None:
                        raise GlyphError(f"rows {r0 + 1}-{r0 + 3}, position {pos + 1}: not a part or a number here")
                    halves.append(which)
            words = tuple(Word(halves[i], halves[i + 1]) for i in (0, 2, 4))
            line.bands.append(Band(symbol, words))  # type: ignore[arg-type]
        if line.bands:
            page.lines.append(line)
    return page
