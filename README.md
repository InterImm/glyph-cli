# glyph

The dictionary and toolkit for the **grid script**: how humans write down what Ross 128 b sends, in InterImm's *The Contact Era*.

[![PyPI](https://img.shields.io/pypi/v/glyph-cli)](https://pypi.org/project/glyph-cli/)
[![Python](https://img.shields.io/pypi/pyversions/glyph-cli)](https://pypi.org/project/glyph-cli/)
[![CI](https://github.com/InterImm/glyph-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/InterImm/glyph-cli/actions/workflows/ci.yml)
[![Docs](https://github.com/InterImm/glyph-cli/actions/workflows/docs.yml/badge.svg)](https://interimm.github.io/glyph-cli/)

**Docs:** https://interimm.github.io/glyph-cli/ · **PyPI:** https://pypi.org/project/glyph-cli/

```sh
uvx --from glyph-cli glyph show BODY.OTHER STAR.TIME COUNT.137
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

`glyph` is on [PyPI](https://pypi.org/project/glyph-cli/) as `glyph-cli`:

```sh
uv tool install glyph-cli    # or: pipx install glyph-cli, or: pip install glyph-cli
glyph --version
```

Upgrade with `uv tool upgrade glyph-cli` (or `pipx upgrade glyph-cli`, `pip install -U glyph-cli`). Python 3.10 or newer, no other dependencies.

## Use

```sh
glyph parts                         # the 16 parts
glyph find wind                     # search meanings
glyph check BODY.STAR               # is it a word? exit 1 if not
glyph show BODY.OTHER --symbol ×    # draw words
glyph number 2219                   # COUNT.4.171: base-512 digits
glyph render examples/third-voice.txt         # draw a page
glyph render examples/conversation.txt --per-line 1   # one triplet per line
glyph render examples/third-voice.txt --svg -o page.svg
glyph graph examples/conversation.txt         # read it as a knowledge graph (--json, --dot)
glyph render examples/question.txt | glyph decode -   # and back
glyph init my-vocab.json && export GLYPH_VOCAB=$PWD/my-vocab.json
glyph add BODY.STAR "a star-world" --domain Worlds
```

A page file has one band per line, `SYMBOL: node | relation | node`; a block of bands is one triplet, and a blank line starts the next. See [`examples/`](https://github.com/InterImm/glyph-cli/tree/main/examples) and the [docs](https://interimm.github.io/glyph-cli/pages/).

## Develop

```sh
uv sync --all-groups          # or: pip install -e . pytest ruff zensical
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run python scripts/gen_docs.py    # regenerate docs/vocabulary.md, docs/cli.md and the example drawings
uv run zensical serve                # docs at http://localhost:8000
```

The vocabulary ships in [`src/glyph_cli/data/vocab.json`](https://github.com/InterImm/glyph-cli/blob/main/src/glyph_cli/data/vocab.json). Change it with the tool (`glyph --vocab src/glyph_cli/data/vocab.json add ...`), then run `scripts/gen_docs.py`; the tests fail if the generated docs are stale.

Pushes to `main` publish the docs to GitHub Pages.

## Release

1. Bump `__version__` in `src/glyph_cli/__init__.py` and merge it to `main`.
2. Publish a GitHub release tagged `vX.Y.Z` (the same version).

The release workflow checks the tag matches the version, builds the package, tests the built wheel and uploads it to [PyPI](https://pypi.org/project/glyph-cli/) with Trusted Publishing, so no token is stored.

## License

MIT
