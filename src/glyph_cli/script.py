"""The script itself: parts, words and the vocabulary that names them.

A *part* is a 3x3 shape with a meaning. A *word* is a **kind** part narrowed by
a **which** part, written ``KIND.WHICH``, or a kind alone. Either half may be empty
(``_``). Numbers are ``COUNT`` followed by base-512 digits, most significant first
(``COUNT.137``, ``COUNT.4.171`` = 2219): COUNT is the only kind whose positions are
read as nine bits, and it never takes a part, so a number can never be drawn like a
word. ``COUNT`` alone is zero.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

#: One lattice position: a part name, a base-512 digit (only in a number) or ``None`` for empty.
Half = str | int | None
#: The which of a word: a part, one digit, several digits (a number above 511) or ``None``.
Which = str | int | tuple[int, ...] | None

BASE = 512
MAX_DIGIT = BASE - 1
MAX_NUMBER = MAX_DIGIT  # kept for compatibility: the largest single digit
EMPTY = "_"
NUMBER = "COUNT"  # the kind whose which is a number


def to_digits(n: int) -> tuple[int, ...]:
    """``2219`` -> ``(4, 171)``: base-512 digits, most significant first."""
    if n < 0:
        raise GlyphError(f"only whole numbers of zero or more: {n}")
    digits = []
    while True:
        n, d = divmod(n, BASE)
        digits.append(d)
        if not n:
            return tuple(reversed(digits))


def from_digits(digits: tuple[int, ...]) -> int:
    n = 0
    for d in digits:
        n = n * BASE + d
    return n


class GlyphError(Exception):
    """A problem the user can fix: a bad word, a bad page, a bad vocabulary."""


@dataclass(frozen=True)
class Part:
    name: str
    shape: tuple[str, str, str]
    thing: str
    relation: str | None = None


@dataclass(frozen=True)
class Word:
    """One word: ``kind`` and ``which``. ``Word(None, None)`` is the empty word.

    A number's which is one digit (``Word("COUNT", 137)``) or a tuple of digits
    (``Word("COUNT", (4, 171))`` = 2219).
    """

    kind: str | None = None
    which: Which = None

    @property
    def is_empty(self) -> bool:
        return self.kind is None and self.which is None

    @property
    def is_number(self) -> bool:
        return isinstance(self.which, (int, tuple))

    @property
    def digits(self) -> tuple[int, ...]:
        """A number's digits; ``()`` for any other which."""
        if isinstance(self.which, tuple):
            return self.which
        return (self.which,) if isinstance(self.which, int) else ()

    @property
    def value(self) -> int | None:
        """The number a COUNT word stands for (``COUNT`` alone is 0); ``None`` for other words."""
        if self.kind == NUMBER or (self.kind is None and self.is_number):
            return from_digits(self.digits) if self.digits else 0
        return None

    @property
    def positions(self) -> list[Half]:
        """The lattice positions the word takes, left to right.

        A one-part word takes one position (3 cells), a pair two, a number one per digit
        after COUNT. The empty word takes one empty position.
        """
        if self.which is None:
            return [self.kind]
        return [self.kind, *self.digits] if self.is_number else [self.kind, self.which]

    @property
    def halves(self) -> tuple[Half, ...]:
        """Deprecated name for :attr:`positions`, kept for 0.2 code."""
        return tuple(self.positions)

    def __str__(self) -> str:
        if self.is_empty:
            return EMPTY
        if self.which is None:
            which = ""
        elif self.is_number:
            which = "." + ".".join(str(d) for d in self.digits)
        else:
            which = f".{self.which}"
        return (self.kind or EMPTY) + which


@dataclass
class Entry:
    """A vocabulary entry: a word with an agreed meaning."""

    word: Word
    gloss: str
    domain: str = "Unsorted"
    note: str = ""

    def to_json(self) -> dict:
        return {
            "kind": self.word.kind,
            "which": list(self.word.which) if isinstance(self.word.which, tuple) else self.word.which,
            "gloss": self.gloss,
            "domain": self.domain,
            "note": self.note,
        }


@dataclass
class Vocabulary:
    parts: dict[str, Part]
    markers: dict[str, str]
    entries: list[Entry] = field(default_factory=list)
    version: int = 1
    path: Path | None = None

    # ---- loading and saving ----

    @classmethod
    def from_json(cls, data: dict, path: Path | None = None) -> Vocabulary:
        try:
            parts = {
                name: Part(name, tuple(p["shape"]), p["thing"], p.get("relation")) for name, p in data["parts"].items()
            }
            entries = [
                Entry(
                    Word(e["kind"], _which_from_json(e["which"])),
                    e["gloss"],
                    e.get("domain", "Unsorted"),
                    e.get("note", ""),
                )
                for e in data["words"]
            ]
            return cls(parts, dict(data.get("markers", {})), entries, data.get("version", 1), path)
        except (KeyError, TypeError) as exc:
            raise GlyphError(f"not a glyph vocabulary file: missing {exc}") from exc

    @classmethod
    def load(cls, path: str | os.PathLike | None = None) -> Vocabulary:
        """Load a vocabulary file, or the bundled one when ``path`` is ``None``."""
        if path is None:
            text = resources.files("glyph_cli").joinpath("data/vocab.json").read_text(encoding="utf-8")
            return cls.from_json(json.loads(text))
        p = Path(path)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise GlyphError(f"vocabulary file not found: {p}") from None
        except json.JSONDecodeError as exc:
            raise GlyphError(f"{p} is not valid JSON: {exc}") from None
        return cls.from_json(data, p)

    def to_json(self) -> dict:
        return {
            "version": self.version,
            "parts": {
                p.name: {"shape": list(p.shape), "thing": p.thing, "relation": p.relation} for p in self.parts.values()
            },
            "markers": self.markers,
            "words": [e.to_json() for e in self.entries],
        }

    def save(self, path: str | os.PathLike | None = None) -> Path:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise GlyphError(
                "the bundled vocabulary is read-only; run `glyph init` to make an editable copy, "
                "then point to it with --vocab or GLYPH_VOCAB"
            )
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(json.dumps(self.to_json(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, target)
        self.path = target
        return target

    # ---- words ----

    def parse(self, text: str) -> Word:
        """``'BODY.OTHER'`` -> ``Word('BODY', 'OTHER')``; ``'COUNT.137'`` -> ``Word('COUNT', 137)``.

        Numbers are base-512 digits after COUNT: ``'COUNT.4.171'`` -> ``Word('COUNT', (4, 171))``.
        A single number above 511 is split into digits for you: ``'COUNT.2219'`` is ``COUNT.4.171``.
        """
        s = text.strip()
        if s in ("", EMPTY):
            return Word()
        k, _, w = s.partition(".")
        kind = None if k in ("", EMPTY) else k.upper()
        which: Which
        if w in ("", EMPTY):
            which = None
        elif all(d.isdigit() for d in w.split(".")):
            digits = tuple(int(d) for d in w.split("."))
            if len(digits) == 1:
                digits = to_digits(digits[0])
            elif any(d > MAX_DIGIT for d in digits):
                raise GlyphError(f"each digit of a number is 0-{MAX_DIGIT} (base {BASE}): {s}")
            elif digits[0] == 0 and kind == NUMBER:
                raise GlyphError(f"a number does not start with a 0 digit: {s}")
            if kind not in (NUMBER, None):
                raise GlyphError(f"a number needs {NUMBER} as its kind, e.g. {NUMBER}.{w} (got {s})")
            which = digits[0] if len(digits) == 1 else digits
            if kind == NUMBER and which == 0:
                which = None  # COUNT alone is zero: COUNT.0 draws exactly like it
        elif "." in w:
            raise GlyphError(f"only numbers take more than two positions: {s}")
        else:
            which = w.upper()
            if kind == NUMBER:
                raise GlyphError(f"{NUMBER} only takes a number as its which, e.g. {NUMBER}.12 (got {s})")
        for half in (kind, which):
            if isinstance(half, str) and half not in self.parts:
                raise GlyphError(f"unknown part: {half} (see `glyph parts`)")
        return Word(kind, which)

    def lookup(self, word: Word) -> Entry | None:
        for e in self.entries:
            if e.word == word:
                return e
        return None

    def thing(self, half: Half) -> str:
        """The meaning of one half on its own."""
        if half is None:
            return EMPTY
        if isinstance(half, int):
            return str(half)
        if isinstance(half, tuple):
            return ".".join(str(d) for d in half)
        return self.parts[half].thing

    def gloss(self, word: Word, role: str = "node") -> str:
        """The best human reading of a word as a ``node`` or as a ``relation``."""
        if word.is_empty:
            return "—"
        if role == "relation":
            base = ""
            if word.kind:
                part = self.parts[word.kind]
                base = part.relation or part.thing
            if word.which is None:
                return base
            plain = self.thing(word.which) if word.is_number else str(word.which)
            marker = self.markers.get(str(word.which)) or plain
            return f"{base} [{marker}]"
        if word.kind == NUMBER:
            return str(word.value)
        entry = self.lookup(word)
        if entry:
            return entry.gloss
        if word.which is None:
            return self.parts[word.kind].thing  # type: ignore[index]
        return f"{self.thing(word.kind)} | {self.thing(word.which)} (not in vocabulary)"

    # ---- editing ----

    def add(self, word: Word, gloss: str, domain: str = "Unsorted", note: str = "", force: bool = False) -> Entry:
        if word.kind is None or word.is_number or word.kind == NUMBER:
            raise GlyphError(f"a vocabulary word needs a kind; numbers ({NUMBER}.n) are built in")
        existing = self.lookup(word)
        if existing:
            raise GlyphError(f'already in the vocabulary: {word} = "{existing.gloss}"')
        same = [e for e in self.entries if e.gloss.lower() == gloss.lower()]
        if same and not force:
            raise GlyphError(f'the meaning "{gloss}" is already used by {same[0].word}; use --force to add anyway')
        entry = Entry(word, gloss, domain, note)
        self.entries.append(entry)
        return entry

    def remove(self, word: Word) -> Entry:
        entry = self.lookup(word)
        if not entry:
            raise GlyphError(f"not in the vocabulary: {word}")
        self.entries.remove(entry)
        return entry

    def search(self, text: str) -> tuple[list[Entry], list[Part]]:
        t = text.lower()
        words = [e for e in self.entries if t in e.gloss.lower() or t in e.note.lower()]
        parts = [p for p in self.parts.values() if t in p.thing.lower() or (p.relation and t in p.relation.lower())]
        return words, parts

    def validate(self) -> list[str]:
        """Return a list of problems; an empty list means the vocabulary is sound."""
        errors: list[str] = []
        shapes: dict[tuple[str, ...], str] = {}
        for p in self.parts.values():
            if len(p.shape) != 3 or any(len(r) != 3 or set(r) - set("#.") for r in p.shape):
                errors.append(f'part {p.name}: shape must be 3 rows of 3 "#"/"."')
            if p.shape in shapes:
                errors.append(f"parts {shapes[p.shape]} and {p.name} have the same shape")
            shapes[p.shape] = p.name
            if not any("#" in r for r in p.shape):
                errors.append(f"part {p.name}: shape is empty")
        seen: dict[Word, str] = {}
        glosses: dict[str, Word] = {}
        for e in self.entries:
            for half in e.word.halves:
                if isinstance(half, str) and half not in self.parts:
                    errors.append(f"{e.word}: unknown part {half}")
            if e.word.kind == NUMBER:
                errors.append(f"{e.word}: {NUMBER} words are numbers and are built in")
            if e.word in seen:
                errors.append(f'{e.word} defined twice ("{seen[e.word]}" and "{e.gloss}")')
            seen[e.word] = e.gloss
            g = e.gloss.lower()
            if g in glosses:
                errors.append(f'meaning "{e.gloss}" used by {glosses[g]} and {e.word}')
            glosses[g] = e.word
        return errors

    def domains(self) -> list[str]:
        out: list[str] = []
        for e in self.entries:
            if e.domain not in out:
                out.append(e.domain)
        return out


def _which_from_json(which: object) -> Which:
    return tuple(which) if isinstance(which, list) else which  # type: ignore[return-value]
