import pytest
from conftest import EXAMPLES

from glyph_cli import GlyphError
from glyph_cli.drawing import decode, hidden_zeros, number_shape, render, render_svg
from glyph_cli.graph import format_graph, read_graph
from glyph_cli.page import format_page, parse_page

ALL_EXAMPLES = sorted(EXAMPLES.glob("*.txt"))


def page(vocab, text):
    return parse_page(text, vocab)


# Drawings from the canon grammar (story/grid-grammar.md, v8): 1 cell inside a word,
# 2 between words, 4 between triplets; a one-part word is 3 cells wide.
GRAMMAR = {
    "+: SELF | LIGHT.BEFORE | BODY.OTHER": """
+++..+.+.+....+++.+++
+.+...+..+++..+++.+..
+++..+.+.+....+++.+++
""",
    "+: STAR.TIME | ONE | COUNT.12": """
.+..+.+..............
+++.+.+...+.........+
.+..+.+.......+++.+..
""",
    "+: STAR.TIME | ONE | OPEN.COUNT\n×: _ | _ | COUNT.12": """
.+..+.+........+.....
+++.+.+...+...+.+....
.+..+.+........+..+++
.....................
.....................
....................×
..............×××.×..
""",
    "+: BODY.OTHER | ONE | BODY.AIR\n×: _ | _ | _.WATER\n*: _ | _ | _.AIR": """
+++.+++.......+++.+.+
+++.+.....+...+++....
+++.+++.......+++.+.+
.....................
..................×××
.....................
..................×××
.....................
..................*.*
.....................
..................*.*
""",
    "+: SELF | LIGHT | BODY.OTHER\n\n+: SELF | VOICE.AFTER | ONE": """
+++..+.+..+++.+++....+++..+.....+.....
+.+...+...+++.+......+.+..++..+++...+.
+++..+.+..+++.+++....+++..+++...+.....
""",
}


@pytest.mark.parametrize("source, drawing", GRAMMAR.items())
def test_render_matches_grammar(vocab, source, drawing):
    assert render(vocab, page(vocab, source)) == drawing.strip().splitlines()


def test_numbers_are_nine_bits():
    assert number_shape(137) == (".#.", "..#", "..#")  # 010 001 001 = 128 + 8 + 1
    assert number_shape(12) == ("...", "..#", "#..")


def test_triplets_are_padded_to_the_page_voices(vocab):
    p = page(vocab, "+: SELF | ONE | OTHER\n×: _ | _ | _.NOT\n\n+: SELF | ONE | SELF.OTHER")
    rows = render(vocab, p, per_line=1)
    assert len(rows) == 7 + 3 + 7
    assert len({len(r) for r in rows}) == 1
    rows = render(vocab, p)  # both triplets on one line, 4 cells apart
    assert len(rows) == 7 and rows[0] == "+++.......+++........+++.......+++.+++"


def test_one_part_words_are_three_cells(vocab):
    assert render(vocab, page(vocab, "+: SELF | ONE | OTHER")) == [
        "+++.......+++",
        "+.+...+...+..",
        "+++.......+++",
    ]


def test_slots_widen_for_the_longest_word(vocab):
    rows = render(vocab, page(vocab, "+: SELF | ONE | OTHER\n×: SELF.NOT | _ | _"))
    assert rows[0] == "+++...........+++"  # the subject slot is two positions wide for the reply


@pytest.mark.parametrize("n, source", [(2219, "COUNT.4.171"), (70491, "COUNT.137.347"), (3200000, "COUNT.12.106.0")])
def test_big_numbers(vocab, n, source):
    w = vocab.parse(f"COUNT.{n}")
    assert str(w) == source and w.value == n
    assert vocab.parse(source) == w


@pytest.mark.parametrize("path", ALL_EXAMPLES, ids=lambda p: p.name)
def test_decode_round_trips_examples(vocab, path):
    p = page(vocab, path.read_text(encoding="utf-8"))
    assert decode(vocab, "\n".join(render(vocab, p))) == p
    assert decode(vocab, "\n".join(render(vocab, p, per_line=1))) == p


@pytest.mark.parametrize("n", [0, 1, 12, 16, 137, 170, 273, 487, 495, 511, 513, 2219, 70491, 262143, 3200001])
def test_decode_numbers(vocab, n):
    # Numbers whose bits spell a part's shape (495 is SELF) read back as numbers: they sit under COUNT.
    for where in (f"STAR.TIME | ONE | COUNT.{n}", f"COUNT.{n} | ONE | STAR.TIME"):
        p = page(vocab, "+: " + where)
        back = decode(vocab, "\n".join(render(vocab, p)))
        assert back == p


def test_a_zero_digit_at_the_end_of_a_line_is_invisible(vocab):
    p = page(vocab, "+: SELF | LIGHT | COUNT.12.106.0")
    assert hidden_zeros(p) == [1]
    assert str(decode(vocab, "\n".join(render(vocab, p))).triplets[0].statement.words[2]) == "COUNT.12.106"
    p = page(vocab, "+: SELF | LIGHT | COUNT.12.106.0\n\n+: SELF | VOICE | ONE")
    assert hidden_zeros(p) == [] and decode(vocab, "\n".join(render(vocab, p))) == p
    p = page(vocab, "+: COUNT.12.106.0 | ONE | COUNT.6250")
    assert hidden_zeros(p) == [] and decode(vocab, "\n".join(render(vocab, p))) == p


def test_decode_ambiguous_gaps(vocab):
    # ONE and the gaps around it: every one of these reads back as written.
    for src in ("+: BODY.AFTER | ONE | OTHER", "+: BODY | ONE.OTHER | OTHER", "+: SELF | VOICE.ONE | ONE"):
        p = page(vocab, src)
        assert decode(vocab, "\n".join(render(vocab, p))) == p


def test_decode_kindless_number_reply(vocab):
    p = page(vocab, "+: STAR.TIME | ONE | COUNT.12\n×: _ | _ | _.495")
    assert decode(vocab, "\n".join(render(vocab, p))) == p


def test_decode_words(vocab):
    p = page(vocab, "+: ONE.SELF | ONE | ONE.OTHER")
    assert decode(vocab, "\n".join(render(vocab, p))) == p


def test_decode_rejects_pictures(vocab):
    with pytest.raises(GlyphError, match="lines and bands"):
        decode(vocab, "+++\n...\n")
    with pytest.raises(GlyphError, match="1, 2 and 4 cell gaps"):
        decode(vocab, "+++++++\n+.+.+.+\n+++++++\n")
    with pytest.raises(GlyphError, match="mixes symbols"):
        decode(vocab, "+++.......×××\n+.+...+...×.×\n+++.......×××\n")
    with pytest.raises(GlyphError, match="1, 2 and 4 cell gaps"):
        decode(vocab, "+.+..........\n.............\n.............\n")


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
        "3. (+) we --say, send [now]--> [triplet 2]",
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
    assert g.edges[0].object.label() == "[that: nothing before]"


def test_rule_five_by_digit(vocab):
    g = read_graph(vocab, page(vocab, "+: SELF | LIGHT | COUNT.4.171\n×: _ | _ | _.4.170"))
    assert [r.text(vocab) for r in g.edges[0].replies[0].responses] == [
        "object.digit 1: yes (to +)",
        'object.digit 2: instead "170" (to +)',
    ]


def test_svg(vocab):
    svg = render_svg(vocab, page(vocab, (EXAMPLES / "third-voice.txt").read_text(encoding="utf-8")))
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "#9ff8ff" in svg and "#ffd84a" in svg and "#c9b3ff" in svg
    assert "<circle" not in svg and "<path" not in svg  # no curves
