# Getting started

## Install

`glyph` is published on [PyPI](https://pypi.org/project/glyph-cli/) as **`glyph-cli`** (the command it installs is `glyph`). It needs Python 3.10 or newer and has no other dependencies.

=== "uv"

    ```sh
    uv tool install glyph-cli
    ```

=== "pipx"

    ```sh
    pipx install glyph-cli
    ```

=== "pip"

    ```sh
    pip install glyph-cli
    ```

Check it works:

```sh
glyph --version
```

To get a newer release later:

=== "uv"

    ```sh
    uv tool upgrade glyph-cli
    ```

=== "pipx"

    ```sh
    pipx upgrade glyph-cli
    ```

=== "pip"

    ```sh
    pip install -U glyph-cli
    ```

!!! tip "Unreleased changes"
    PyPI has the latest release. To try what is on `main` before it is released, install from GitHub instead:
    `uv tool install git+https://github.com/InterImm/glyph-cli`.

## Look at the parts

Everything is built from 16 parts, each a 3×3 shape.

```sh
glyph parts
```

Each part means a thing when it is a node (`BODY` is *world, matter*) and an action when it is a relation (`BODY` is *have, contain*).

## Look words up

A word is two parts side by side, one empty cell apart: a **kind** narrowed by a **which**, written `KIND.WHICH`. A single part is a word too.

```sh
glyph find world          # search meanings
glyph check BODY.OTHER    # yes: BODY.OTHER = "your world"
glyph check BODY.STAR     # no, and its literal reading
glyph show BODY.OTHER BODY.SELF --symbol ×
```

Numbers are built in: `COUNT.137` is 137, its digit drawn as nine bits. Bigger numbers take more digits in base 512, most significant first: `COUNT.4.171` is 4 × 512 + 171 = 2219. `COUNT` alone is zero.

```sh
glyph number 2219         # 2219 = COUNT.4.171, and its drawing
```

## Write a page

A page is a text file. Each line of the file is one band: the party's symbol, then a triplet, `node | relation | node`. Save this as `hello.txt`:

```text
+: SELF | LIGHT.BEFORE | BODY.OTHER
```

Draw it:

```sh
glyph render hello.txt
```

```text
+++..+.+.+....+++.+++
+.+...+..+++..+++.+..
+++..+.+.+....+++.+++
```

And read it:

```sh
glyph graph hello.txt
```

```text
Edges:
1. (+) we --see [past]--> your world
```

"We saw your world." The gaps carry the structure: 1 empty cell inside a word, 2 between the words of a triplet, and 4 between triplets. A blank line in the file starts the next triplet, and `glyph render` puts two triplets on each drawn line (change it with `--per-line`).

## Reply

Another voice answers in a band under the statement, part by part. Something drawn under a part means *yes* if it is the same part, *no* if it is `NOT`, and *instead* if it is different. Add our reply:

```text
+: BODY.OTHER | ONE | BODY.AIR
×: _ | _ | _.WATER
```

`_` leaves a position empty. `glyph graph` reads: *your world is an air-world*, and `×` says *water instead*. The full rules are in [The script](script.md).

## Draw it as pixels

```sh
glyph render conversation.txt --svg -o conversation.svg
```

The SVG uses the phase 2 colours: signal blue, white-cyan `+` for them, Sol yellow `×` for us. Any other symbol gets its own colour.

## Read a drawing back

The translating machine works the other way too: give it a drawing and it gives you the page.

```sh
glyph render conversation.txt | glyph decode -
```

It finds the words from the gaps alone.

## Grow the vocabulary

The bundled vocabulary is read-only. Make your own copy, point `glyph` at it, and add words:

```sh
glyph init my-vocab.json
export GLYPH_VOCAB=$PWD/my-vocab.json
glyph add BODY.STAR "a star-world" --domain Worlds --note "hypothetical"
glyph validate
glyph export-md --title Vocabulary -o vocabulary.md
```

`add` refuses a word that already exists and warns when the meaning is taken by another word. `validate` checks that every word and meaning is unique and every part has its own shape.
