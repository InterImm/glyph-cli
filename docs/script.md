# The script

This is the grammar `glyph` implements: version 7 of the grid script, where **a page is a knowledge graph**. In the story it is our transcription of their data, not a script anyone has seen them use.

## The five rules

1. **Lattice.** Every mark is a whole 3×3 part in a lattice position. Positions are one empty cell apart, so a line is **6 positions wide** (23 cells).
2. **Words are pairs.** A word takes two neighbouring positions: **kind** on the left, **which** on the right. A one-part word leaves the which empty.
3. **Every line is one edge.** Positions 1–2 hold a **node**, 3–4 a **relation**, 5–6 another **node**. The same word on two lines is the same node. Lines are three empty rows apart.
4. **Stacking means another voice.** Only a new party adds a band to a line: a 3-row strip under the band above, one empty row between. Each party has one symbol.
5. **A part answers the part above it.** Read every part in a lower band against the nearest drawn part above it in the same position:

| Below | Means |
|---|---|
| The same part | Yes |
| `NOT` | No |
| A different part | Instead |
| A part under an empty position | And also |
| Nothing | No comment |

## Parts

```text
--8<-- "docs/assets/parts.txt"
```

| Part | As a thing (node) | As a relation (edge) |
|---|---|---|
| SELF | we | know |
| OTHER | you | answer |
| STAR | star | shine on |
| LIGHT | light | see |
| BODY | world, matter | have, contain |
| AIR | air | carry |
| WATER | water | flow to |
| TIME | time | last, wait |
| VOICE | sound | say, send |
| PATH | way, between | go to, reach |
| NOT | not | — |
| ONE | one, this, the same | is, equals |
| BEFORE | earlier | — |
| AFTER | later | — |
| OPEN | what goes here? | — |

## Relations

A relation is one part (the action) plus a which that marks time or polarity:

| Which | Meaning | With `LIGHT` (see) |
|---|---|---|
| empty | no tense | see |
| `BEFORE` | past | saw |
| `ONE` | now | see now |
| `AFTER` | future | will see |
| `PATH` | always | keep seeing |
| `NOT` | not | do not see |
| `OPEN` | asked: does it? | do … see? |

## Numbers

`ONE` with a which read as nine bits, 256 down to 1, left to right and top to bottom. `ONE.137`:

```text
.....+.
.+....+
......+
```

!!! note "Numbers that look like words"
    Some numbers spell a part's shape: 495 is drawn exactly like `SELF`, so `ONE.495` and `ONE.SELF` (*one of us*) look the same on the page. When a drawing is read back, `glyph decode` reads such a which as the vocabulary word, and `glyph check ONE.495` warns about it. The clashes today are 16 (`ONE.ONE`), 170 (`ONE.OPEN`), 273 (`ONE.NOT`), 487 (`ONE.OTHER`) and 495 (`ONE.SELF`). `ONE.0` draws nothing in the which, so it reads back as `ONE` alone.

## "That" and questions

- `ONE` alone in a node slot means **that**: the statement on the line above.
- `OPEN` in any position asks **what goes here?** The asker leaves an empty band for the answer, and whatever is drawn under `OPEN` replaces it. `OPEN` as a relation's which asks yes or no.

## How the machine reads a page

1. Cut the page into 3×3 positions. Anything off the lattice is a picture, not text.
2. Split it into lines at the three-row gaps, and count the bands: that is the number of voices.
3. Read band 1 of each line as an edge. Same word, same node. A lone `ONE` points at the line above.
4. Apply rule 5 to every part in a lower band, and attach the result to that node or edge with the voice that drew it.

`glyph decode` does steps 1 and 2; `glyph graph` does 3 and 4.
