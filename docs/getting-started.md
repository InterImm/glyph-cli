# Getting started

## Install

`glyph` needs Python 3.10 or newer and has no other dependencies.

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

The latest code on `main` installs with `uv tool install git+https://github.com/InterImm/glyph-cli`.

Check it works:

```sh
glyph --version
```

## Look at the parts

Everything is built from 16 parts, each a 3×3 shape.

```sh
glyph parts
```

Each part means a thing when it is a node (`BODY` is *world, matter*) and an action when it is a relation (`BODY` is *have, contain*).

## Look words up

A word is two parts side by side: a **kind** narrowed by a **which**, written `KIND.WHICH`.

```sh
glyph find world          # search meanings
glyph check BODY.OTHER    # yes: BODY.OTHER = "your world"
glyph check BODY.STAR     # no, and its literal reading
glyph show BODY.OTHER BODY.SELF --symbol ×
```

Numbers are built in: `COUNT.137` is 137, its which drawn as nine bits. `COUNT` alone is zero.

## Write a page

A page is a text file. Each line of the file is one band: the party's symbol, then three slots, `node | relation | node`. Save this as `hello.txt`:

```text
+: SELF | LIGHT.BEFORE | BODY.OTHER
```

Draw it:

```sh
glyph render hello.txt
```

```text
+++.....+.+.....+++.+++
+.+......+..+...+++.+..
+++.....+.+.....+++.+++
```

And read it:

```sh
glyph graph hello.txt
```

```text
Edges:
1. (+) we --see [past]--> your world
```

"We saw your world."

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
