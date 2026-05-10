"""HTTP header parser — minimal RFC 7230-compatible header parsing.

Public API:
- parse_headers(text: str) -> Headers
- Headers: dict-like with case-insensitive keys, multi-value support
- get(name) -> str | None  (joins multi-values with ', ')
- get_all(name) -> list[str]
- raw() -> list[tuple[str, str]]

Rules (subset of RFC 7230):
- Headers are 'Name: Value' lines.
- Names are case-insensitive (Content-Type == content-type).
- Lines may be folded (start with whitespace = continuation of previous header).
- Repeated headers are joined as comma-separated, except 'Set-Cookie' which is multi-valued list.
- CRLF or LF line endings tolerated; trailing whitespace stripped.
"""
from __future__ import annotations


class HeaderError(Exception):
    pass


class Headers:
    """Case-insensitive header dict-like, preserving original order and multi-value semantics."""

    SET_COOKIE = "set-cookie"

    def __init__(self):
        self._items: list[tuple[str, str]] = []  # (canonical_lower_key, value)

    def add(self, name: str, value: str) -> None:
        if not name:
            raise HeaderError("empty header name")
        self._items.append((name.lower(), value))

    def get(self, name: str) -> str | None:
        key = name.lower()
        if key == self.SET_COOKIE:
            # Set-Cookie: never join; return first
            for k, v in self._items:
                if k == key:
                    return v
            return None
        values = [v for k, v in self._items if k == key]
        if not values:
            return None
        return ", ".join(values)

    def get_all(self, name: str) -> list[str]:
        key = name.lower()
        return [v for k, v in self._items if k == key]

    def raw(self) -> list[tuple[str, str]]:
        return list(self._items)

    def __contains__(self, name: str) -> bool:
        return name.lower() in {k for k, _ in self._items}

    def __len__(self) -> int:
        return len(self._items)


def _split_lines(text: str) -> list[str]:
    # Tolerate CRLF or LF. Strip \r at end.
    raw = text.split("\n")
    return [ln.rstrip("\r") for ln in raw]


def parse_headers(text: str) -> Headers:
    """Parse a sequence of header lines into a Headers object.

    Empty trailing lines are tolerated and signal end-of-headers (RFC 7230 §3).
    Lines starting with whitespace are folded into the prior header's value.
    """
    if text is None:
        raise HeaderError("input is None")
    headers = Headers()
    lines = _split_lines(text)
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln == "":
            # End of headers section.
            break
        if ln[0] in " \t":
            # Folded continuation of previous header.
            if not headers._items:
                raise HeaderError(f"folded line {i} without prior header")
            prev_key, prev_val = headers._items[-1]
            headers._items[-1] = (prev_key, prev_val + " " + ln.strip())
            i += 1
            continue
        if ":" not in ln:
            raise HeaderError(f"missing ':' on line {i}: {ln!r}")
        name, _, value = ln.partition(":")
        if not name.strip():
            raise HeaderError(f"empty name on line {i}")
        name = name.strip()
        if " " in name:
            raise HeaderError(f"whitespace in header name {name!r}")
        value = value.strip()
        headers.add(name, value)
        i += 1
    return headers
