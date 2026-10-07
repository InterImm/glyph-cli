"""The ``glyph`` command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path

from . import __version__
from .drawing import decode, draw_words, render, render_svg
from .export import vocabulary_markdown
from .graph import format_graph, read_graph, to_dot
from .page import check_symbol, format_page, parse_page
from .script import NUMBER, GlyphError, Vocabulary

ENV_VOCAB = "GLYPH_VOCAB"

DESCRIPTION = """\
glyph: the dictionary and toolkit for the grid script of Ross 128 b.

Words are written KIND.WHICH (BODY.OTHER = "your world"), or KIND alone.
A number is COUNT.<n> (0-511); COUNT alone is zero. "_" is an empty position or an empty word.
Pages are text files, one band per line: "SYMBOL: node | relation | node".
"""

EPILOG = f"""\
The vocabulary is the bundled one unless --vocab or ${ENV_VOCAB} names a file.
Run `glyph init` to make an editable copy. Docs: https://interimm.github.io/glyph-cli/
"""


# ---------- helpers ----------


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise GlyphError(f"file not found: {path}") from None


def write_output(text: str, path: str | None) -> None:
    if path:
        Path(path).write_text(text, encoding="utf-8")
        print(f"wrote {path}", file=sys.stderr)
    else:
        sys.stdout.write(text)


def emit_json(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ---------- commands ----------


def cmd_parts(v: Vocabulary, a: argparse.Namespace) -> int:
    if a.json:
        emit_json({"parts": v.to_json()["parts"], "markers": v.markers})
        return 0
    for p in v.parts.values():
        print(f"{p.name:<7} {p.shape[0]}  {p.thing:<22} as relation: {p.relation or '—'}")
        print(f"{'':<7} {p.shape[1]}")
        print(f"{'':<7} {p.shape[2]}")
    print("\nRelation markers (the which of a relation word):")
    for m, g in v.markers.items():
        print(f"  {m:<7} {g}")
    return 0


def cmd_list(v: Vocabulary, a: argparse.Namespace) -> int:
    entries = [e for e in v.entries if not a.domain or a.domain.lower() in e.domain.lower()]
    if a.json:
        emit_json([dict(e.to_json(), word=str(e.word)) for e in entries])
        return 0
    if not entries:
        print(f'no domain matches "{a.domain}"; domains: {", ".join(v.domains())}', file=sys.stderr)
        return 1
    for domain in v.domains():
        rows = [e for e in entries if e.domain == domain]
        if not rows:
            continue
        print(f"\n{domain}")
        for e in rows:
            note = f"  ({e.note})" if e.note else ""
            print(f"  {str(e.word):<14} {e.gloss}{note}")
    return 0


def cmd_check(v: Vocabulary, a: argparse.Namespace) -> int:
    word = v.parse(a.word)
    e = v.lookup(word)
    if e:
        print(f'yes: {word} = "{e.gloss}" ({e.domain})')
        return 0
    if word.kind == NUMBER:
        print(f"yes: {word} = the number {word.which or 0} (numbers are built in)")
        return 0
    print(f"no: {word} is not in the vocabulary. Literal reading: {v.gloss(word)}")
    same_kind = [x for x in v.entries if x.word.kind == word.kind]
    if same_kind:
        print("  other words of this kind: " + ", ".join(f"{x.word} {x.gloss}" for x in same_kind))
    return 1


def cmd_find(v: Vocabulary, a: argparse.Namespace) -> int:
    words, parts = v.search(a.text)
    for e in words:
        print(f"{str(e.word):<14} {e.gloss}  [{e.domain}]")
    for p in parts:
        print(f"{p.name:<14} part: {p.thing}; as relation: {p.relation or '—'}")
    if not words and not parts:
        print(f'nothing matches "{a.text}"')
        return 1
    return 0


def cmd_show(v: Vocabulary, a: argparse.Namespace) -> int:
    words = [v.parse(s) for s in a.words]
    print("\n".join(draw_words(v, words, check_symbol(a.symbol))))
    for w in words:
        print(f"  {w}: {v.gloss(w)}")
    return 0


def cmd_add(v: Vocabulary, a: argparse.Namespace) -> int:
    e = v.add(v.parse(a.word), a.gloss, a.domain, a.note, a.force)
    path = v.save()
    print(f'added {e.word} = "{e.gloss}" to {path}')
    return 0


def cmd_remove(v: Vocabulary, a: argparse.Namespace) -> int:
    e = v.remove(v.parse(a.word))
    path = v.save()
    print(f'removed {e.word} ("{e.gloss}") from {path}')
    return 0


def cmd_validate(v: Vocabulary, a: argparse.Namespace) -> int:
    errors = v.validate()
    for x in errors:
        print("error:", x)
    print(f"{len(v.parts)} parts, {len(v.entries)} words, {len(errors)} problems")
    return 1 if errors else 0


def cmd_render(v: Vocabulary, a: argparse.Namespace) -> int:
    page = parse_page(read_input(a.file), v)
    if a.svg:
        write_output(render_svg(v, page, cell=a.cell, grid=not a.no_grid), a.output)
    else:
        write_output("\n".join(render(v, page)) + "\n", a.output)
    return 0


def cmd_graph(v: Vocabulary, a: argparse.Namespace) -> int:
    g = read_graph(v, parse_page(read_input(a.file), v))
    if a.json:
        emit_json(g.to_json())
    elif a.dot:
        sys.stdout.write(to_dot(g))
    else:
        print("\n".join(format_graph(v, g)))
    return 0


def cmd_decode(v: Vocabulary, a: argparse.Namespace) -> int:
    sys.stdout.write(format_page(decode(v, read_input(a.file))))
    return 0


def cmd_export(v: Vocabulary, a: argparse.Namespace) -> int:
    write_output(vocabulary_markdown(v, a.title), a.output)
    return 0


def cmd_init(v: Vocabulary, a: argparse.Namespace) -> int:
    target = Path(a.path)
    if target.exists() and not a.force:
        raise GlyphError(f"{target} already exists; use --force to overwrite")
    v.save(target)
    print(f"wrote {target} ({len(v.entries)} words). Use it with:")
    print(f"  export {ENV_VOCAB}={target.resolve()}")
    return 0


# ---------- parser ----------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="glyph", description=DESCRIPTION, epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--vocab", metavar="PATH", help=f"vocabulary file (default: ${ENV_VOCAB}, else the bundled one)")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    def add(name: str, func: Callable, help: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help, description=help)
        p.set_defaults(func=func)
        return p

    p = add("parts", cmd_parts, "list the parts and the relation markers")
    p.add_argument("--json", action="store_true", help="print JSON")
    p = add("list", cmd_list, "list the vocabulary")
    p.add_argument("--domain", help="only domains containing this text")
    p.add_argument("--json", action="store_true", help="print JSON")
    p = add("check", cmd_check, "is a word in the vocabulary? (exit 1 if not)")
    p.add_argument("word")
    p = add("find", cmd_find, "search meanings and notes")
    p.add_argument("text")
    p = add("show", cmd_show, "draw words")
    p.add_argument("words", nargs="+", metavar="WORD")
    p.add_argument("--symbol", default="+", help="the party's symbol (default +)")
    p = add("add", cmd_add, "add a word to an editable vocabulary")
    p.add_argument("word")
    p.add_argument("gloss", help="its meaning")
    p.add_argument("--domain", default="Unsorted")
    p.add_argument("--note", default="")
    p.add_argument("--force", action="store_true", help="add even if the meaning is already used")
    p = add("remove", cmd_remove, "remove a word from an editable vocabulary")
    p.add_argument("word")
    add("validate", cmd_validate, "check the vocabulary (exit 1 on problems)")
    p = add("render", cmd_render, "draw a page from page source")
    p.add_argument("file", help="page source file, or - for stdin")
    p.add_argument("--svg", action="store_true", help="draw SVG pixels instead of text")
    p.add_argument("--cell", type=int, default=12, help="SVG cell size in pixels (default 12)")
    p.add_argument("--no-grid", action="store_true", help="SVG: leave empty cells undrawn")
    p.add_argument("-o", "--output", help="write to a file instead of stdout")
    p = add("graph", cmd_graph, "read a page as a knowledge graph")
    p.add_argument("file", help="page source file, or - for stdin")
    fmt = p.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="print JSON")
    fmt.add_argument("--dot", action="store_true", help="print Graphviz DOT")
    p = add("decode", cmd_decode, "read a drawing back into page source")
    p.add_argument("file", help="drawing file, or - for stdin")
    p = add("export-md", cmd_export, "print the vocabulary as Markdown")
    p.add_argument("--title", help="add a top-level heading")
    p.add_argument("-o", "--output", help="write to a file instead of stdout")
    p = add("init", cmd_init, "copy the vocabulary to a file you can edit")
    p.add_argument("path", nargs="?", default="vocab.json")
    p.add_argument("--force", action="store_true", help="overwrite an existing file")
    return ap


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = build_parser()
    a = ap.parse_args(argv)
    try:
        vocab = Vocabulary.load(a.vocab or os.environ.get(ENV_VOCAB) or None)
        return a.func(vocab, a)
    except GlyphError as exc:
        print(f"glyph: error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
