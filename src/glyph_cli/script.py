"""The script itself: parts, words and the vocabulary that names them.

A *part* is a 3x3 shape with a meaning. A *word* is two lattice positions,
a **kind** on the left and a **which** on the right, written ``KIND.WHICH``.
Either half may be empty (``_``). When the kind is ``ONE`` the which may be a
number from 0 to 511, drawn as nine bits.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

#: A half of a word: a part name, a number (only after ``ONE``) or ``None`` for empty.
Half = str | int | None

MAX_NUMBER = 511
EMPTY = "_"


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
    """One word: ``kind`` and ``which``. ``Word(None, None)`` is the empty word."""

    kind: str | None = None
    which: Half = None

    @property
    def is_empty(self) -> bool:
        return self.kind is None and self.which is None

    @property
    def is_number(self) -> bool:
        return isinstance(self.which, int)

    @property
    def halves(self) -> tuple[Half, Half]:
        return (self.kind, self.which)

    def __str__(self) -> str:
        if self.is_empty:
            return EMPTY
        which = "" if self.which is None else f".{self.which}"
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
            "which": self.word.which,
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
                Entry(Word(e["kind"], e["which"]), e["gloss"], e.get("domain", "Unsorted"), e.get("note", ""))
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
        """``'BODY.OTHER'`` -> ``Word('BODY', 'OTHER')``; ``'ONE.137'`` -> ``Word('ONE', 137)``."""
        s = text.strip()
        if s in ("", EMPTY):
            return Word()
        k, _, w = s.partition(".")
        kind = None if k in ("", EMPTY) else k.upper()
        which: Half
        if w in ("", EMPTY):
            which = None
        elif w.isdigit():
            which = int(w)
            if which > MAX_NUMBER:
                raise GlyphError(f"number out of range 0-{MAX_NUMBER}: {which}")
            if kind not in ("ONE", None):
                raise GlyphError(f"a number needs ONE as its kind, e.g. ONE.{which} (got {s})")
        else:
            which = w.upper()
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
            marker = self.markers.get(str(word.which), str(word.which))
            return f"{base} [{marker}]"
        if word.kind == "ONE" and word.is_number:
            return str(word.which)
        entry = self.lookup(word)
        if entry:
            return entry.gloss
        if word.which is None:
            return self.parts[word.kind].thing  # type: ignore[index]
        return f"{self.thing(word.kind)} | {self.thing(word.which)} (not in vocabulary)"

    # ---- editing ----

    def add(self, word: Word, gloss: str, domain: str = "Unsorted", note: str = "", force: bool = False) -> Entry:
        if word.kind is None or word.is_number:
            raise GlyphError("a vocabulary word needs a kind; numbers are built in")
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
            if e.word in seen:
                errors.append(f'{e.word} defined twice ("{seen[e.word]}" and "{e.gloss}")')
            seen[e.word] = e.gloss
            g = e.gloss.lower()
            if g in glosses:
                errors.append(f'meaning "{e.gloss}" used by {glosses[g]} and {e.word}')
            glosses[g] = e.word
        return errors

    def number_twin(self, n: int) -> Entry | None:
        """The ONE.PART word that is drawn exactly like the number ONE.n, if there is one.

        A number's nine bits can spell a part's shape (495 is SELF), so ONE.495 and
        ONE.SELF ("one of us") look the same on the page.
        """
        for p in self.parts.values():
            if int("".join(p.shape).replace("#", "1").replace(".", "0"), 2) == n:
                return self.lookup(Word("ONE", p.name))
        return None

    def domains(self) -> list[str]:
        out: list[str] = []
        for e in self.entries:
            if e.domain not in out:
                out.append(e.domain)
        return out
