# The script

This is the grammar `glyph` implements: version 8 of the grid script, where **a text is a knowledge graph** and **spacing is structure**. In the story it is our transcription of their data, not a script anyone has seen them use.

## The five rules

1. **Spacing is structure.** Every mark is a whole 3×3 part. The gaps between parts say how they group: **1 empty cell** between the parts of a word, **2** between the words of a triplet, **4** between triplets. Lines are **3 empty rows** apart.
2. **Words are pairs.** A word is a **kind** narrowed by a **which**, `KIND.WHICH`. A one-part word is just its kind, 3 cells wide. Only numbers have more parts.
3. **Every triplet is one edge.** A text is a run of triplets, `(node, relation, node)`, read left to right. The same word in two triplets is the same node, and a lone `ONE` in a node slot means **that**: the triplet before.
4. **Stacking means another voice.** Only a new party adds a band to a triplet: a 3-row strip under the band above, one empty row between. Each party has one symbol.
5. **A part answers the part above it.** Read every part in a lower band against the nearest drawn part above it, in the same position of the same slot:

| Below | Means |
|---|---|
| The same part | Yes |
| `NOT` | No |
| A different part | Instead |
| A part under an empty position | And also |
| Nothing | No comment |

Two triplets on one line, "We saw your world. We will say that.":

```text
+++..+.+.+....+++.+++....+++..+.....+.....
+.+...+..+++..+++.+......+.+..++..+++...+.
+++..+.+.+....+++.+++....+++..+++...+.....
```

`SELF`, 2 cells, `LIGHT.BEFORE` (1 cell inside), 2 cells, `BODY.OTHER`; then 4 cells and the next triplet.

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
| COUNT | number | — |

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

`COUNT` followed by **base-512 digits**, most significant first. Each digit is a part's worth of nine bits, 256 down to 1, left to right and top to bottom, and the digits are one cell apart like the parts of any word. `COUNT` alone is zero.

| Number | Written | Because |
|---|---|---|
| 137 | `COUNT.137` | one digit |
| 2219 | `COUNT.4.171` | 4 × 512 + 171 |
| 70,491 | `COUNT.137.347` | 137 × 512 + 347 |
| 3,200,000 | `COUNT.12.106.0` | 12 × 512² + 106 × 512 + 0 |

`COUNT.137`:

```text
.....+.
......+
+++...+
```

`glyph number N` writes any number this way, and `COUNT.2219` in a page is accepted and written as `COUNT.4.171`.

COUNT is the only kind whose positions are read as bits, and it never takes a part, so a number can never be drawn like a word. (Under v6, numbers were `ONE` plus bits, and 495 was drawn exactly like `ONE.SELF`, *one of us*.)

A 0 digit is a blank position. Inside a line that is fine, because the next gap shows where the number ends, but a number ending in 0 digits as the last word of a line can't be told from a shorter one. `glyph render` warns when that happens.

## "That" and questions

- `ONE` alone in a node slot means **that**: the triplet before.
- `OPEN` in any position asks **what goes here?** The asker leaves an empty band for the answer, and whatever is drawn under `OPEN` replaces it. `OPEN` as a relation's which asks yes or no.
- **How many?** is `OPEN.COUNT` (*what number?*), answered with a `COUNT` word.

## Why no part is another part moved sideways

Because gaps carry the structure, a part with empty edge columns could make a 1-cell gap look like a 2-cell gap. `ONE` is a single dot in the middle, so `BEFORE` and `AFTER` are drawn as a path with a tick at its start and its end, not as dots at the edges: otherwise `BODY.AFTER | OTHER` (*will have, you*) and `BODY | ONE.OTHER` (*have, one of you*) would be the same drawing. `glyph validate` checks that no part moved one cell sideways is another part.

## How the machine reads a page

1. Split the drawing into lines at the three-row gaps, and count the bands: that is the number of voices.
2. Split each line into triplets, words and parts from the 1, 2 and 4 cell gaps. Anything that won't split into whole parts is a picture, not text. Number digits can have empty edges of their own, so when more than one split fits, the machine keeps the one that reads best against the vocabulary.
3. Read the first band of each triplet as an edge. Same word, same node. A lone `ONE` points at the triplet before.
4. Apply rule 5 to every part in a lower band, and attach the result to that node or edge with the voice that drew it.

`glyph decode` does steps 1 and 2; `glyph graph` does 3 and 4.
