import pytest
from conftest import EXAMPLES

from glyph_cli import GlyphError
from glyph_cli.drawing import WIDTH, decode, number_shape, render, render_svg
from glyph_cli.graph import format_graph, read_graph
from glyph_cli.page import format_page, parse_page

ALL_EXAMPLES = sorted(EXAMPLES.glob("*.txt"))


def page(vocab, text):
    return parse_page(text, vocab)


# Drawings copied from the canon grammar (story/grid-grammar.md, v7).
GRAMMAR = {
    "+: SELF | LIGHT.BEFORE | BODY.OTHER": """
+++.....+.+.....+++.+++
+.+......+..+...+++.+..
+++.....+.+.....+++.+++
""",
    "+: STAR.TIME | ONE | COUNT.12": """
.+..+.+................
+++.+.+..+............+
.+..+.+.........+++.+..
""",
    "+: STAR.TIME | ONE | OPEN.COUNT\n×: _ | _ | COUNT.12": """
.+..+.+..........+.....
+++.+.+..+......+.+....
.+..+.+..........+..+++
.......................
.......................
......................×
................×××.×..
""",
    "+: BODY.OTHER | ONE | BODY.AIR\n×: _ | _ | _.WATER\n*: _ | _ | _.AIR": """
+++.+++.........+++.+.+
+++.+....+......+++....
+++.+++.........+++.+.+
.......................
....................×××
.......................
....................×××
.......................
....................*.*
.......................
....................*.*
""",
}


@pytest.mark.parametrize("source, drawing", GRAMMAR.items())
def test_render_matches_grammar(vocab, source, drawing):
    assert render(vocab, page(vocab, source)) == drawing.strip().splitlines()


def test_numbers_are_nine_bits():
    assert number_shape(137) == (".#.", "..#", "..#")  # 010 001 001 = 128 + 8 + 1
    assert number_shape(12) == ("...", "..#", "#..")


def test_lines_are_padded_to_the_page_voices(vocab):
    rows = render(vocab, page(vocab, "+: SELF | ONE | OTHER\n×: _ | _ | _.NOT\n\n+: SELF | ONE | SELF"))
    assert len(rows) == 7 + 3 + 7
    assert all(len(r) == WIDTH for r in rows)


@pytest.mark.parametrize("path", ALL_EXAMPLES, ids=lambda p: p.name)
def test_decode_round_trips_examples(vocab, path):
    p = page(vocab, path.read_text(encoding="utf-8"))
    assert decode(vocab, "\n".join(render(vocab, p))) == p


@pytest.mark.parametrize("n", [0, 1, 12, 16, 137, 170, 273, 487, 495, 511])
def test_decode_numbers(vocab, n):
    # Numbers whose bits spell a part's shape (495 is SELF) read back as numbers: they sit under COUNT.
    p = page(vocab, f"+: STAR.TIME | ONE | COUNT.{n}")
    back = decode(vocab, "\n".join(render(vocab, p)))
    assert str(back.lines[0].statement.words[2]) == ("COUNT" if n == 0 else f"COUNT.{n}")


def test_decode_kindless_number_reply(vocab):
    p = page(vocab, "+: STAR.TIME | ONE | COUNT.12\n×: _ | _ | _.495")
    assert decode(vocab, "\n".join(render(vocab, p))) == p


def test_decode_words(vocab):
    p = page(vocab, "+: ONE.SELF | ONE | ONE.OTHER")
    assert decode(vocab, "\n".join(render(vocab, p))) == p


def test_decode_rejects_pictures(vocab):
    with pytest.raises(GlyphError, match="wide"):
        decode(vocab, "+++\n...\n")
    with pytest.raises(GlyphError, match="between lattice"):
        decode(vocab, "...+...................\n" + ("." * 23 + "\n") * 2)
    with pytest.raises(GlyphError, match="mixes symbols"):
        decode(vocab, "+++.×××................\n+.+.×.×................\n+++.×××................\n")
    with pytest.raises(GlyphError, match="not a part"):
        decode(vocab, "+.+....................\n.......................\n.......................\n")


def test_parse_errors_name_the_line(vocab):
    with pytest.raises(GlyphError, match="line 2"):
        page(vocab, "+: SELF | ONE | OTHER\n+ SELF | ONE | OTHER")
    with pytest.raises(GlyphError, match="three slots"):
        page(vocab, "+: SELF | ONE")
    with pytest.raises(GlyphError, match="unknown part"):
        page(vocab, "+: SELF | ONE | WIND")
    with pytest.raises(GlyphError, match="symbol"):
        page(vocab, ".: SELF | ONE | OTHER")


def test_format_page_round_trips(vocab):
    for path in ALL_EXAMPLES:
        p = page(vocab, path.read_text(encoding="utf-8"))
        assert page(vocab, format_page(p)) == p


def test_graph_reads_edges_and_replies(vocab):
    g = read_graph(vocab, page(vocab, (EXAMPLES / "conversation.txt").read_text(encoding="utf-8")))
    assert format_graph(vocab, g)[:6] == [
        "Edges:",
        "1. (+) your world --is, equals--> air-world",
        '   (×) object.which: instead "water" (to +)',
        '   (*) object.which: instead "air" (to ×)',
        "2. (+) we --see [past]--> your world",
        "3. (+) we --say, send [now]--> [statement 2]",
    ]
    assert g.nodes == {"BODY.OTHER": "your world", "BODY.AIR": "air-world", "SELF": "we"}


@pytest.mark.parametrize(
    "reply, expected",
    [
        ("×: _ | _ | BODY.AIR", ["object.kind: yes (to +)", "object.which: yes (to +)"]),
        ("×: _ | _ | _.NOT", ["object.which: no (to +)"]),
        ("×: _ | _ | _.WATER", ['object.which: instead "water" (to +)']),
        ("×: _ | ONE.PATH | _", ["relation.kind: yes (to +)", 'relation.which: and also "way, between"']),
        ("×: _ | _ | _", []),
    ],
)
def test_rule_five(vocab, reply, expected):
    g = read_graph(vocab, page(vocab, "+: BODY.OTHER | ONE | BODY.AIR\n" + reply))
    assert [r.text(vocab) for r in g.edges[0].replies[0].responses] == expected


def test_that_on_the_first_line(vocab):
    g = read_graph(vocab, page(vocab, "+: SELF | LIGHT.BEFORE | ONE"))
    assert g.edges[0].object.label() == "[that: nothing above]"


def test_svg(vocab):
    svg = render_svg(vocab, page(vocab, (EXAMPLES / "third-voice.txt").read_text(encoding="utf-8")))
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "#9ff8ff" in svg and "#ffd84a" in svg and "#c9b3ff" in svg
    assert "<circle" not in svg and "<path" not in svg  # no curves
