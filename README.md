# glyph

The dictionary and toolkit for the **grid script**: how humans write down what Ross 128 b sends, in InterImm's *The Contact Era*.

**Docs:** https://interimm.github.io/glyph-cli/

```sh
uvx --from git+https://github.com/InterImm/glyph-cli glyph show BODY.OTHER STAR.TIME COUNT.137
```

```text
+++.+++   .+..+.+   .....+.
+++.+..   +++.+.+   ......+
+++.+++   .+..+.+   +++...+
  BODY.OTHER: your world
  STAR.TIME: pulsar
  COUNT.137: 137
```

## Install

```sh
uv tool install git+https://github.com/InterImm/glyph-cli    # or: pipx install git+https://github.com/InterImm/glyph-cli
```

Python 3.10 or newer, no other dependencies.

## Use

```sh
glyph parts                         # the 16 parts
glyph find wind                     # search meanings
glyph check BODY.STAR               # is it a word? exit 1 if not
glyph show BODY.OTHER --symbol ×    # draw words
glyph render examples/third-voice.txt         # draw a page
glyph render examples/third-voice.txt --svg -o page.svg
glyph graph examples/conversation.txt         # read it as a knowledge graph (--json, --dot)
glyph render examples/question.txt | glyph decode -   # and back
glyph init my-vocab.json && export GLYPH_VOCAB=$PWD/my-vocab.json
glyph add BODY.STAR "a star-world" --domain Worlds
```

A page file has one band per line, `SYMBOL: node | relation | node`; a blank line starts the next statement. See [`examples/`](examples) and the [docs](https://interimm.github.io/glyph-cli/pages/).

## Develop

```sh
uv sync --all-groups          # or: pip install -e . pytest ruff zensical
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run python scripts/gen_docs.py    # regenerate docs/vocabulary.md, docs/cli.md and the example drawings
uv run zensical serve                # docs at http://localhost:8000
```

The vocabulary ships in [`src/glyph_cli/data/vocab.json`](src/glyph_cli/data/vocab.json). Change it with the tool (`glyph --vocab src/glyph_cli/data/vocab.json add ...`), then run `scripts/gen_docs.py`; the tests fail if the generated docs are stale.

Pushes to `main` publish the docs to GitHub Pages.

## License

MIT
