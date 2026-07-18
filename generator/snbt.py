from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


class SNBTParseError(ValueError):
    pass


@dataclass(slots=True)
class Token:
    kind: str
    value: str
    pos: int


_TOKEN_RE = re.compile(
    r"""\s*(?:(?P<string>"(?:\\.|[^"\\])*")|(?P<number>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?[bBsSlLfFdD]?)|(?P<ident>[A-Za-z0-9_+\-./]+)|(?P<punct>[{}\[\],;:]))"""
)


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        if not match:
            if text[pos:].strip() == "":
                break
            raise SNBTParseError(f"Unexpected character at offset {pos}: {text[pos:pos+20]!r}")
        kind = next(name for name, value in match.groupdict().items() if value is not None)
        tokens.append(Token(kind, match.group(kind), pos))
        pos = match.end()
    return tokens


class SNBTParser:
    def __init__(self, text: str):
        self.tokens = tokenize(text)
        self.index = 0

    def parse(self) -> Any:
        value = self._value()
        if self.index != len(self.tokens):
            token = self.tokens[self.index]
            raise SNBTParseError(f"Unexpected token {token.value!r} at offset {token.pos}")
        return value

    def _peek(self, value: str | None = None) -> Token | None:
        if self.index >= len(self.tokens):
            return None
        token = self.tokens[self.index]
        return token if value is None or token.value == value else None

    def _take(self, value: str | None = None) -> Token:
        token = self._peek(value)
        if token is None:
            expected = value or "token"
            actual = self.tokens[self.index].value if self.index < len(self.tokens) else "EOF"
            raise SNBTParseError(f"Expected {expected}, got {actual}")
        self.index += 1
        return token

    def _value(self) -> Any:
        token = self._peek()
        if token is None:
            raise SNBTParseError("Unexpected end of input")
        if token.value == "{":
            return self._compound()
        if token.value == "[":
            return self._list_or_array()
        self.index += 1
        if token.kind == "string":
            return bytes(token.value[1:-1], "utf-8").decode("unicode_escape")
        if token.kind == "number":
            return self._number(token.value)
        if token.value == "true":
            return True
        if token.value == "false":
            return False
        return token.value

    def _key(self) -> str:
        token = self._take()
        if token.kind == "string":
            return bytes(token.value[1:-1], "utf-8").decode("unicode_escape")
        return token.value

    def _compound(self) -> dict[str, Any]:
        self._take("{")
        result: dict[str, Any] = {}
        while not self._peek("}"):
            key = self._key()
            self._take(":")
            result[key] = self._value()
            if self._peek(","):
                self._take(",")
        self._take("}")
        return result

    def _list_or_array(self) -> list[Any]:
        self._take("[")
        if self._peek() and self._peek().kind == "ident" and self._peek().value in {"B", "I", "L"}:
            self._take()
            self._take(";")
        result: list[Any] = []
        while not self._peek("]"):
            result.append(self._value())
            if self._peek(","):
                self._take(",")
        self._take("]")
        return result

    @staticmethod
    def _number(value: str) -> int | float:
        suffix = value[-1].lower() if value[-1].isalpha() else ""
        core = value[:-1] if suffix else value
        if suffix in {"f", "d"} or "." in core or "e" in core.lower():
            return float(core)
        return int(core)


def loads(text: str) -> Any:
    return SNBTParser(text).parse()
