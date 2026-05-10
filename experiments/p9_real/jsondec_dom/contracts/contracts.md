# Contract Document

## Public API

The module explicitly exports:

```python
__all__ = ["JSONDecoder", "JSONDecodeError"]
```

The following non-private callables are also documented because they are public by name: `py_scanstring`, `JSONObject`, and `JSONArray`.

---

## `class JSONDecodeError(ValueError)`

### Signature

```python
class JSONDecodeError(ValueError)
```

### Purpose

Represents a JSON decoding failure with structured position metadata.

### Invariants

Instances expose:

```python
msg: original unformatted error message
doc: JSON document being parsed
pos: character index where parsing failed
lineno: 1-based line number for pos
colno: 1-based column number for pos
```

The string form of the exception is formatted as:

```text
{msg}: line {lineno} column {colno} (char {pos})
```

---

### `JSONDecodeError.__init__`

#### Signature

```python
def __init__(self, msg, doc, pos)
```

#### Preconditions

- `doc` supports string-like `count()` and `rfind()` operations.
- `pos` is an integer index into, or relative to, `doc`.
- `msg` is suitable for string formatting.

#### Postconditions / Return Guarantees

- Initializes the base `ValueError` with a formatted message.
- Sets:
  - `self.msg == msg`
  - `self.doc == doc`
  - `self.pos == pos`
  - `self.lineno == doc.count("\n", 0, pos) + 1`
  - `self.colno == pos - doc.rfind("\n", 0, pos)`
- Returns `None`.

#### Invariants

- `lineno` is 1-based.
- `colno` is computed relative to the last newline before `pos`.

#### Side Effects / Exceptions Raised

- Mutates the exception instance by assigning metadata attributes.
- May propagate exceptions from `doc.count`, `doc.rfind`, or string formatting if incompatible arguments are supplied.

---

### `JSONDecodeError.__reduce__`

#### Signature

```python
def __reduce__(self)
```

#### Preconditions

- The instance has `msg`, `doc`, and `pos` attributes.

#### Postconditions / Return Guarantees

Returns:

```python
(self.__class__, (self.msg, self.doc, self.pos))
```

This supports reconstruction of the exception.

#### Invariants

- The reduction tuple uses the concrete runtime class of the instance.

#### Side Effects / Exceptions Raised

- No intentional side effects.

---

## `py_scanstring`

### Signature

```python
def py_scanstring(
    s,
    end,
    strict=True,
    _b=BACKSLASH,
    _m=STRINGCHUNK.match
)
```

### Purpose

Scans and decodes a JSON string literal body from `s`, beginning immediately after the opening quote.

### Preconditions

- `s` is a string-like object containing JSON string content.
- `end` is the index immediately after the opening double quote.
- `strict` is a boolean controlling whether literal control characters are rejected.
- `_b` maps recognized single-character escape codes to decoded characters.
- `_m` matches chunks of string content and string terminators.

### Postconditions / Return Guarantees

Returns a tuple:

```python
(decoded_string, end_index)
```

Where:

- `decoded_string` is the decoded Python string.
- `end_index` is the index immediately after the closing quote.
- Valid JSON escape sequences are decoded.
- Unicode escapes of the form `\uXXXX` are decoded.
- Valid UTF-16 surrogate pairs are combined into a single code point.
- If `strict` is `False`, literal control characters are included in the result.

#### Recognized Escapes

```python
\"  -> "
\\  -> \
\/  -> /
\b  -> backspace
\f  -> form feed
\n  -> newline
\r  -> carriage return
\t  -> tab
\uXXXX -> Unicode code point
```

### Invariants

- Output chunks are accumulated in order.
- The returned index always points after the terminating double quote when decoding succeeds.
- Escapes are interpreted before appending to the output string.

### Side Effects / Exceptions Raised

Raises `JSONDecodeError` when:

- The string is unterminated.
- A control character is encountered while `strict` is true.
- An escape sequence is not recognized.
- A Unicode escape is not a valid `\uXXXX` sequence.

No intentional external side effects.

---

## `JSONObject`

### Signature

```python
def JSONObject(
    s_and_end,
    strict,
    scan_once,
    object_hook,
    object_pairs_hook,
    memo=None,
    _w=WHITESPACE.match,
    _ws=WHITESPACE_STR
)
```

### Purpose

Parses a JSON object from a string and returns its Python representation plus the ending index.

### Preconditions

- `s_and_end` is a pair `(s, end)`.
- `s` is the JSON source string.
- `end` is the index where object content begins, after the opening `{`.
- `scan_once` parses a JSON value and returns `(value, new_end)`.
- Object property names are JSON strings enclosed in double quotes.
- Object member names and values are separated by `:`.
- Object members are separated by `,`.
- `object_hook`, when provided, is callable.
- `object_pairs_hook`, when provided, is callable.
- `memo`, when provided, supports `setdefault`.

### Postconditions / Return Guarantees

Returns:

```python
(result, end_index)
```

Where:

- `end_index` is the index immediately after the closing `}`.
- Empty objects decode to `{}` unless a hook changes the result.
- Object members are parsed as key/value pairs.
- Whitespace is skipped where permitted.
- Keys are memoized through `memo.setdefault`.

Hook behavior:

- If `object_pairs_hook` is not `None`, it is called with the ordered list of `(key, value)` pairs, and its return value is used.
- Otherwise, pairs are converted to `dict`.
- If `object_hook` is not `None`, it is called with that dict, and its return value is used.
- `object_pairs_hook` takes priority over `object_hook`.

### Invariants

- Parsed key/value pairs are accumulated in source order before final conversion or hook invocation.
- Each property name is parsed using `scanstring`.
- Each value is parsed using `scan_once`.
- The returned index advances past the complete object.

### Side Effects / Exceptions Raised

Raises `JSONDecodeError` when:

- A property name is not enclosed in double quotes.
- A `:` delimiter is missing.
- A value is expected but not present.
- A `,` delimiter is missing between members.

May propagate exceptions from:

- `scanstring`
- `scan_once`
- `object_hook`
- `object_pairs_hook`
- `memo.setdefault`

---

## `JSONArray`

### Signature

```python
def JSONArray(
    s_and_end,
    scan_once,
    _w=WHITESPACE.match,
    _ws=WHITESPACE_STR
)
```

### Purpose

Parses a JSON array from a string and returns its Python list representation plus the ending index.

### Preconditions

- `s_and_end` is a pair `(s, end)`.
- `s` is the JSON source string.
- `end` is the index where array content begins, after the opening `[`.
- `scan_once` parses a JSON value and returns `(value, new_end)`.
- Array elements are separated by `,`.

### Postconditions / Return Guarantees

Returns:

```python
(values, end_index)
```

Where:

- `values` is a list of decoded array elements.
- `end_index` is the index immediately after the closing `]`.
- Empty arrays decode to `[]`.
- Whitespace is skipped where permitted.
- Elements are appended in source order.

### Invariants

- The result is always a list when parsing succeeds.
- Each array element is parsed using `scan_once`.
- The returned index advances past the complete array.

### Side Effects / Exceptions Raised

Raises `JSONDecodeError` when:

- A value is expected but not present.
- A `,` delimiter is missing between elements.

May propagate exceptions from `scan_once`.

---

## `class JSONDecoder(object)`

### Signature

```python
class JSONDecoder(object)
```

### Purpose

Decodes JSON documents into Python values.

### Default JSON-to-Python Mapping

| JSON value | Python value |
|---|---|
| object | `dict` |
| array | `list` |
| string | `str` |
| integer number | `int` |
| real number | `float` |
| `true` | `True` |
| `false` | `False` |
| `null` | `None` |

The decoder also recognizes:

```python
NaN
Infinity
-Infinity
```

as floating-point values by default.

---

### `JSONDecoder.__init__`

#### Signature

```python
def __init__(
    self,
    *,
    object_hook=None,
    parse_float=None,
    parse_int=None,
    parse_constant=None,
    strict=True,
    object_pairs_hook=None
)
```

#### Preconditions

- All arguments are keyword-only.
- `object_hook`, if supplied, is callable.
- `object_pairs_hook`, if supplied, is callable.
- `parse_float`, if supplied, is callable and accepts a JSON float string.
- `parse_int`, if supplied, is callable and accepts a JSON integer string.
- `parse_constant`, if supplied, is callable and accepts one of:
  - `"-Infinity"`
  - `"Infinity"`
  - `"NaN"`

#### Postconditions / Return Guarantees

Initializes the decoder with these attributes:

```python
self.object_hook
self.parse_float
self.parse_int
self.parse_constant
self.strict
self.object_pairs_hook
self.parse_object
self.parse_array
self.parse_string
self.memo
self.scan_once
```

Defaults:

- `parse_float` defaults to `float`.
- `parse_int` defaults to `int`.
- `parse_constant` defaults to `_CONSTANTS.__getitem__`.
- `parse_object` is `JSONObject`.
- `parse_array` is `JSONArray`.
- `parse_string` is `scanstring`.
- `memo` is initialized to `{}`.
- `scan_once` is created by `scanner.make_scanner(self)`.

Returns `None`.

#### Invariants

- `self.strict` controls whether literal control characters are allowed in strings.
- `object_pairs_hook`, when set, has priority over `object_hook`.
- The scanner is configured from the decoder instance.

#### Side Effects / Exceptions Raised

- Mutates the decoder instance by assigning configuration and parser attributes.
- May propagate exceptions from `scanner.make_scanner(self)`.

---

### `JSONDecoder.decode`

#### Signature

```python
def decode(self, s, _w=WHITESPACE.match)
```

#### Preconditions

- `s` is a `str` instance containing a complete JSON document.
- Leading and trailing JSON whitespace are allowed.
- `_w` is a whitespace matcher compatible with `WHITESPACE.match`.

#### Postconditions / Return Guarantees

Returns the Python representation of the JSON document.

Processing guarantees:

- Leading whitespace is skipped before decoding.
- `raw_decode` is used to parse the document.
- Trailing whitespace is skipped after decoding.
- The full input string must be consumed after trailing whitespace.

#### Invariants

- Successful decoding consumes exactly one complete JSON document plus surrounding whitespace.
- The return value is the decoded Python representation, possibly transformed by configured hooks or parse functions.

#### Side Effects / Exceptions Raised

Raises `JSONDecodeError` when:

- No JSON value can be decoded.
- Extra non-whitespace data remains after the JSON document.

May propagate exceptions from:

- `raw_decode`
- configured parse functions
- configured hooks
- the scanner

---

### `JSONDecoder.raw_decode`

#### Signature

```python
def raw_decode(self, s, idx=0)
```

#### Preconditions

- `s` is a `str` beginning with a JSON document at index `idx`.
- `idx` is the index where decoding should begin.
- `self.scan_once` is available and callable.

#### Postconditions / Return Guarantees

Returns:

```python
(obj, end)
```

Where:

- `obj` is the decoded Python representation.
- `end` is the index in `s` where the decoded JSON document ends.
- Characters after `end` are not consumed or validated.

#### Invariants

- Decoding starts exactly at `idx`.
- The method delegates value parsing to `self.scan_once`.

#### Side Effects / Exceptions Raised

Raises `JSONDecodeError` with message `"Expecting value"` when no value can be decoded at `idx`.

May propagate exceptions from:

- `self.scan_once`
- configured parse functions
- configured hooks
