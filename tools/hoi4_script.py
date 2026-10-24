"""Small lossless Clausewitz reader for auditing and surgical source edits.

Keeps repeated keys, list atoms, comparison operators and character spans.
"""
from dataclasses import dataclass
from bisect import bisect_left
from pathlib import Path
import re

TOKEN = re.compile(r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>=!?]+|[^\s{}<>=!?#"\ufeff]+')


@dataclass
class Entry:
    key: str
    op: str
    value: object
    start: int
    end: int
    line: int


@dataclass
class Block:
    items: list

    def entries(self, key=None):
        return [x for x in self.items if isinstance(x, Entry) and (key is None or x.key == key)]

    def get(self, key, default=None):
        matches = self.entries(key)
        return matches[-1].value if matches else default

    def atoms(self):
        return [x for x in self.items if isinstance(x, str)]

    def mapping(self):
        return {e.key: e.value for e in self.entries()}


def unquote(value):
    return value[1:-1] if value.startswith('"') else value


def parse(text):
    tokens = [m for m in TOKEN.finditer(text) if not m.group().startswith('#')]
    newlines = [m.start() for m in re.finditer('\n', text)]
    pos = 0

    def block(nested=False):
        nonlocal pos
        items = []
        while pos < len(tokens):
            t = tokens[pos]
            if t.group() == '}':
                if not nested:
                    raise ValueError(f"Extra closing brace at line {bisect_left(newlines, t.start()) + 1}")
                pos += 1
                return Block(items), t.end()
            if t.group() == '{':
                pos += 1
                anonymous, _ = block(True)
                items.append(anonymous)
                continue
            key = unquote(t.group())
            pos += 1
            if pos >= len(tokens) or tokens[pos].group() not in ('=', '<', '>', '<=', '>=', '!=', '?='):
                items.append(key)
                continue
            op = tokens[pos].group()
            pos += 1
            if pos >= len(tokens):
                raise ValueError(f"Missing value for {key}")
            val = tokens[pos]
            pos += 1
            if val.group() == '{':
                value, end = block(True)
            elif val.group() == '}':
                raise ValueError(f"Missing value for {key}")
            else:
                value, end = unquote(val.group()), val.end()
            items.append(Entry(key, op, value, t.start(), end, bisect_left(newlines, t.start()) + 1))
        if nested:
            raise ValueError('Unclosed block')
        return Block(items), len(text)

    return block()[0]


def walk(block, ancestors=()):
    for e in block.entries():
        yield e, ancestors
        if isinstance(e.value, Block):
            yield from walk(e.value, ancestors + (e,))


def read(path):
    return parse(Path(path).read_text(encoding='utf-8-sig'))


def overlay_files(root, vanilla, relative):
    files = {p.name.lower(): p for p in (vanilla / relative).glob('*.txt')}
    files.update({p.name.lower(): p for p in (root / relative).glob('*.txt')})
    return [files[k] for k in sorted(files)]


def replace_spans(text, replacements):
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text
