from pathlib import Path

import pytest

from glyph_cli import Vocabulary

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


@pytest.fixture
def vocab() -> Vocabulary:
    return Vocabulary.load()


@pytest.fixture
def vocab_file(tmp_path, vocab) -> Path:
    path = tmp_path / "vocab.json"
    vocab.save(path)
    return path
