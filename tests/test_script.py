import pytest

from glyph_cli import GlyphError, Vocabulary, Word


def test_bundled_vocabulary_is_sound(vocab):
    assert len(vocab.parts) == 16
    assert vocab.validate() == []


@pytest.mark.parametrize(
    "text, word",
    [
        ("BODY.OTHER", Word("BODY", "OTHER")),
        ("body.other", Word("BODY", "OTHER")),
        ("SELF", Word("SELF", None)),
        ("COUNT.137", Word("COUNT", 137)),
        ("COUNT.0", Word("COUNT", None)),
        ("COUNT", Word("COUNT", None)),
        ("COUNT.4.171", Word("COUNT", (4, 171))),
        ("COUNT.2219", Word("COUNT", (4, 171))),
        ("COUNT.512", Word("COUNT", (1, 0))),
        ("_.12", Word(None, 12)),
        ("_.WATER", Word(None, "WATER")),
        ("_", Word()),
        ("", Word()),
    ],
)
def test_parse(vocab, text, word):
    assert vocab.parse(text) == word


@pytest.mark.parametrize(
    "text", ["BODY.WIND", "COUNT.4.512", "COUNT.0.5", "STAR.12", "ONE.12", "COUNT.SELF", "FOO", "BODY.SELF.OTHER"]
)
def test_parse_rejects(vocab, text):
    with pytest.raises(GlyphError):
        vocab.parse(text)


@pytest.mark.parametrize(
    "text", ["BODY.OTHER", "SELF", "COUNT.137", "COUNT", "COUNT.4.171", "COUNT.12.106.0", "_.12", "_.WATER", "_"]
)
def test_word_str_round_trips(vocab, text):
    assert str(vocab.parse(text)) == text


def test_gloss(vocab):
    assert vocab.gloss(Word("BODY", "OTHER")) == "your world"
    assert vocab.gloss(Word("COUNT", 137)) == "137"
    assert vocab.gloss(Word("COUNT", None)) == "0"
    assert vocab.gloss(Word("COUNT", (4, 171))) == "2219"
    assert vocab.gloss(Word("OPEN", "COUNT")) == "how many?"
    assert vocab.gloss(Word("LIGHT", "BEFORE"), role="relation") == "see [past]"
    assert vocab.gloss(Word("ONE", None), role="relation") == "is, equals"
    assert vocab.gloss(Word("LIGHT", "VOICE")).endswith("(not in vocabulary)")
    assert vocab.gloss(Word()) == "—"


def test_add_and_remove(vocab):
    vocab.add(Word("BODY", "STAR"), "a star-world", "Worlds")
    assert vocab.lookup(Word("BODY", "STAR")).gloss == "a star-world"
    with pytest.raises(GlyphError, match="already in the vocabulary"):
        vocab.add(Word("BODY", "STAR"), "again")
    with pytest.raises(GlyphError, match="already used"):
        vocab.add(Word("TIME", "STAR"), "a star-world")
    vocab.add(Word("TIME", "STAR"), "a star-world", force=True)
    assert vocab.validate() == ['meaning "a star-world" used by BODY.STAR and TIME.STAR']
    vocab.remove(Word("TIME", "STAR"))
    with pytest.raises(GlyphError):
        vocab.remove(Word("TIME", "STAR"))


def test_add_rejects_numbers_and_kindless(vocab):
    for w in (Word("COUNT", 5), Word("COUNT", None), Word(None, "WATER")):
        with pytest.raises(GlyphError):
            vocab.add(w, "x")


def test_bundled_vocabulary_is_read_only(vocab):
    with pytest.raises(GlyphError, match="glyph init"):
        vocab.save()


def test_save_and_load(vocab, tmp_path):
    path = tmp_path / "v.json"
    vocab.save(path)
    again = Vocabulary.load(path)
    assert again.to_json() == vocab.to_json()
    assert again.path == path


def test_validate_rejects_count_words(vocab):
    data = vocab.to_json()
    data["words"].append({"kind": "COUNT", "which": 3, "gloss": "three", "domain": "x", "note": ""})
    assert any("built in" in e for e in Vocabulary.from_json(data).validate())


def test_no_number_draws_like_a_word(vocab):
    """The reason for COUNT: no COUNT.n looks like any vocabulary word."""
    from glyph_cli.drawing import band_rows

    words = {tuple(band_rows(vocab, e.word.positions, "#")) for e in vocab.entries}
    assert all(tuple(band_rows(vocab, ["COUNT", n], "#")) not in words for n in range(1, 512))


def test_validate_catches_duplicate_shapes(vocab):
    data = vocab.to_json()
    data["parts"]["AFTER"]["shape"] = data["parts"]["BEFORE"]["shape"]
    assert any("same shape" in e for e in Vocabulary.from_json(data).validate())


def test_positions(vocab):
    assert vocab.parse("SELF").positions == ["SELF"]
    assert vocab.parse("BODY.OTHER").positions == ["BODY", "OTHER"]
    assert vocab.parse("COUNT.4.171").positions == ["COUNT", 4, 171]
    assert vocab.parse("_").positions == [None]


def test_load_errors(tmp_path):
    with pytest.raises(GlyphError, match="not found"):
        Vocabulary.load(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    with pytest.raises(GlyphError, match="not a glyph vocabulary"):
        Vocabulary.load(bad)
