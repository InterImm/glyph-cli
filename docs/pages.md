# Page files

A page is a plain text file that `glyph render`, `glyph graph` and `glyph decode` read and write.

## Format

- One **band** per line: `SYMBOL: node | relation | node`.
- A block of bands is one **triplet**. Its first band is the **statement**, one edge of the graph. Bands under it are **other voices** replying, part by part.
- A **blank line** starts the next triplet.
- `#` starts a comment.
- A word is `KIND.WHICH`, `KIND`, `_.WHICH`, or `_` for nothing. Numbers are `COUNT` and base-512 digits, most significant first: `COUNT.137`, `COUNT.4.171` (2219). `COUNT.2219` is accepted and written as `COUNT.4.171`. `COUNT` alone is zero. In a reply under a number, `_.12` answers just the digits.
- A symbol is any single character except a space, `.`, `#`, `|`, `:` and `_`. By convention `+` is Ross 128 b and `×` is Earth.

```text
+: BODY.OTHER | ONE | BODY.AIR     # their statement: your world is an air-world
×: _ | _ | _.WATER                 # our reply: water instead of air
```

## Drawing

- Triplets run left to right, two to a drawn line by default (`glyph render --per-line N`). Lines are three empty rows apart.
- Inside a triplet, each slot is as wide as the longest word any band puts there: a one-part word is 3 cells, a pair 7, a number 4 more per digit.
- Every triplet is drawn with as many bands as the page has voices, so all lines are the same height. To leave room for an answer, add a band with nothing in it, such as `×: _ | _ | _`.
- A 0 digit is a blank position. A number ending in 0 digits as the last word of a drawn line can't be read back, because nothing shows where it ends; `glyph render` warns about it. Put such a number in the subject slot, or another triplet after it.

## Examples

These are the examples from the grammar. Their sources are in [`examples/`](https://github.com/InterImm/glyph-cli/tree/main/examples).

### “We saw your world.”

=== "Pixels"

    ![“We saw your world.”](assets/examples/saw-your-world.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/saw-your-world.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/saw-your-world.txt"
    ```

```sh
glyph graph examples/saw-your-world.txt
```

### “We no longer see you.”

The shadow transmission. Change over time is two edges: we saw you; we do not see you.

=== "Pixels"

    ![“We no longer see you.”](assets/examples/shadow.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/shadow.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/shadow.txt"
    ```

```sh
glyph graph examples/shadow.txt
```

### “Your world is water. We saw that.”

A lone `ONE` in a node slot is *that*, the triplet before.

=== "Pixels"

    ![“Your world is water. We saw that.”](assets/examples/saw-that.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/saw-that.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/saw-that.txt"
    ```

```sh
glyph graph examples/saw-that.txt
```

### “We see pulsars. The pulsars are twelve.”

*Pulsar* in two triplets is one node with two edges.

=== "Pixels"

    ![“We see pulsars. The pulsars are twelve.”](assets/examples/pulsars.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/pulsars.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/pulsars.txt"
    ```

```sh
glyph graph examples/pulsars.txt
```

### “Your world is what?”

We answer *water-world* under `OPEN`.

=== "Pixels"

    ![“Your world is what?”](assets/examples/question.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/question.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/question.txt"
    ```

```sh
glyph graph examples/question.txt
```

### “How many pulsars?”

We answer 12.

=== "Pixels"

    ![“How many pulsars?”](assets/examples/how-many.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/how-many.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/how-many.txt"
    ```

```sh
glyph graph examples/how-many.txt
```

### “Now is 2219.”

A four-digit year takes two base-512 digits: `COUNT.4.171`.

=== "Pixels"

    ![“Now is 2219.”](assets/examples/numbers.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/numbers.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/numbers.txt"
    ```

```sh
glyph graph examples/numbers.txt
```

### A third voice

It answers our *water* with *air*: it sides with them, against us, about our own world.

=== "Pixels"

    ![A third voice](assets/examples/third-voice.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/third-voice.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/third-voice.txt"
    ```

```sh
glyph graph examples/third-voice.txt
```

### A short conversation

Three edges; the last points back at the second.

=== "Pixels"

    ![A short conversation](assets/examples/conversation.svg)

=== "Text"

    ```text
    --8<-- "docs/assets/examples/conversation.drawing.txt"
    ```

=== "Source"

    ```text
    --8<-- "examples/conversation.txt"
    ```

```sh
glyph graph examples/conversation.txt
```
