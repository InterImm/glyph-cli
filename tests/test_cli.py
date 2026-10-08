import json
import sys

import pytest
from conftest import EXAMPLES, ROOT

from glyph_cli import Vocabulary, __version__
from glyph_cli.cli import main


def run(capsys, *args):
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert __version__ in capsys.readouterr().out


def test_parts(capsys):
    code, out, _ = run(capsys, "parts")
    assert code == 0 and "SELF" in out and "asked: does it?" in out
    code, out, _ = run(capsys, "parts", "--json")
    assert len(json.loads(out)["parts"]) == 16


def test_list(capsys):
    code, out, _ = run(capsys, "list", "--domain", "sky")
    assert code == 0 and "pulsar" in out and "we" not in out.split()
    code, out, _ = run(capsys, "list", "--json")
    assert {"word": "BODY.OTHER", "gloss": "your world"}.items() <= next(
        e for e in json.loads(out) if e["word"] == "BODY.OTHER"
    ).items()
    assert run(capsys, "list", "--domain", "nope")[0] == 1


def test_check(capsys):
    assert run(capsys, "check", "BODY.OTHER")[0] == 0
    assert run(capsys, "check", "COUNT.137")[0] == 0
    code, out, _ = run(capsys, "check", "LIGHT.VOICE")
    assert code == 1 and "not in the vocabulary" in out
    code, _, err = run(capsys, "check", "WIND")
    assert code == 2 and "unknown part" in err


def test_find_and_show(capsys):
    code, out, _ = run(capsys, "find", "wind")
    assert code == 0 and "AIR.PATH" in out
    assert run(capsys, "find", "zzz")[0] == 1
    code, out, _ = run(capsys, "show", "BODY.OTHER", "--symbol", "×")
    assert code == 0 and out.splitlines()[0] == "×××.×××" and "your world" in out


def test_render_graph_decode(capsys, tmp_path):
    src = str(EXAMPLES / "third-voice.txt")
    code, drawing, _ = run(capsys, "render", src)
    assert code == 0 and len(drawing.splitlines()) == 11 and len(drawing.splitlines()[0]) == 21
    drawn = tmp_path / "drawing.txt"
    drawn.write_text(drawing, encoding="utf-8")
    code, out, _ = run(capsys, "decode", str(drawn))
    assert out == "+: BODY.OTHER | ONE | BODY.AIR\n×: _ | _ | _.WATER\n*: _ | _ | _.AIR\n"
    code, out, _ = run(capsys, "graph", src, "--json")
    assert json.loads(out)["edges"][0]["replies"][1]["responses"][0]["to"] == "×"
    code, out, _ = run(capsys, "graph", src, "--dot")
    assert out.startswith("digraph")
    svg = tmp_path / "page.svg"
    code, _, err = run(capsys, "render", src, "--svg", "-o", str(svg))
    assert code == 0 and svg.read_text().startswith("<svg")


def test_number(capsys):
    code, out, _ = run(capsys, "number", "2219")
    assert code == 0 and out.startswith("2219 = COUNT.4.171  (4×512^1 + 171×512^0)")
    assert run(capsys, "number", "137")[1].splitlines()[1:] == [".....+.", "......+", "+++...+"]
    assert run(capsys, "number", "--", "-1")[0] == 2


def test_render_per_line_and_zero_warning(capsys, tmp_path):
    src = tmp_path / "p.txt"
    src.write_text("+: SELF | LIGHT | ONE\n\n+: SELF | VOICE | COUNT.1.0\n")
    code, out, err = run(capsys, "render", str(src), "--per-line", "1")
    assert code == 0 and len(out.splitlines()) == 3 + 3 + 3
    assert "triplet 2" in err and "triplet 1" not in err


def test_errors_exit_2(capsys, tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("+: SELF | ONE\n")
    code, _, err = run(capsys, "render", str(bad))
    assert code == 2 and err.startswith("glyph: error: line 1")
    assert run(capsys, "render", str(tmp_path / "missing.txt"))[0] == 2


def test_editing_needs_an_editable_vocabulary(capsys, monkeypatch):
    monkeypatch.delenv("GLYPH_VOCAB", raising=False)
    code, _, err = run(capsys, "add", "BODY.STAR", "a star-world")
    assert code == 2 and "glyph init" in err


def test_init_add_remove(capsys, tmp_path, monkeypatch):
    path = tmp_path / "vocab.json"
    assert run(capsys, "init", str(path))[0] == 0
    assert run(capsys, "init", str(path))[0] == 2  # refuses to overwrite
    monkeypatch.setenv("GLYPH_VOCAB", str(path))
    code, out, _ = run(capsys, "add", "BODY.STAR", "a star-world", "--domain", "Worlds", "--note", "hypothetical")
    assert code == 0
    assert Vocabulary.load(path).lookup(Vocabulary.load(path).parse("BODY.STAR")).note == "hypothetical"
    assert run(capsys, "check", "BODY.STAR")[0] == 0
    assert run(capsys, "--vocab", str(path), "remove", "BODY.STAR")[0] == 0
    assert run(capsys, "check", "BODY.STAR")[0] == 1
    assert run(capsys, "validate")[0] == 0


def test_validate_reports_problems(capsys, tmp_path, vocab):
    data = vocab.to_json()
    data["words"].append(dict(data["words"][0]))
    path = tmp_path / "v.json"
    path.write_text(json.dumps(data))
    code, out, _ = run(capsys, "--vocab", str(path), "validate")
    assert code == 1 and "defined twice" in out


def test_generated_docs_are_current(vocab):
    sys.path.insert(0, str(ROOT / "scripts"))
    import gen_docs

    for path, text in gen_docs.outputs().items():
        if path.name == "cli.md" and sys.version_info[:2] != (3, 13):
            continue  # argparse's help layout differs between Python versions; CI checks it on 3.13
        assert path.read_text(encoding="utf-8") == text, f"{path.name} is stale: run python scripts/gen_docs.py"
