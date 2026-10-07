# Python API

`glyph` is also a small library. Everything the command line does goes through it.

```python
from glyph_cli import Vocabulary
from glyph_cli.page import parse_page
from glyph_cli.drawing import render, render_svg, decode
from glyph_cli.graph import read_graph, format_graph

vocab = Vocabulary.load()            # the bundled vocabulary; or Vocabulary.load("my-vocab.json")

word = vocab.parse("BODY.OTHER")     # Word(kind='BODY', which='OTHER')
vocab.gloss(word)                    # 'your world'

page = parse_page("""
+: BODY.OTHER | ONE | BODY.AIR
×: _ | _ | _.WATER
""", vocab)

print("\n".join(render(vocab, page)))
svg = render_svg(vocab, page, cell=16)

graph = read_graph(vocab, page)
graph.edges[0].replies[0].responses[0].meaning   # 'instead'
graph.to_json()                                  # plain data, ready for json.dumps

assert decode(vocab, "\n".join(render(vocab, page))) == page
```

## Modules

| Module | Holds |
|---|---|
| `glyph_cli.script` | `Part`, `Word`, `Entry`, `Vocabulary` (load, save, parse, gloss, add, remove, validate) and `GlyphError` |
| `glyph_cli.page` | `Band`, `Line`, `Page`, `parse_page`, `format_page` |
| `glyph_cli.drawing` | `render`, `render_svg`, `decode`, `draw_words` |
| `glyph_cli.graph` | `read_graph`, `format_graph`, `to_dot` and the `Graph`, `Edge`, `Reply`, `Response` records |
| `glyph_cli.export` | `vocabulary_markdown` |

Errors the user can fix (a bad word, a bad page, a bad vocabulary file) raise `GlyphError` with a message that names the problem and, for pages, the line.
