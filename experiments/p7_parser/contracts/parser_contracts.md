# Contract: Minimal JSON Parser

## Public Class: `ParseError`

### Signature

```python
class ParseError(Exception):
    def __init__(self, msg: str, position: int)
```

### Preconditions

- `msg` is a string describing the parse condition.
- `position` is an integer position in the input text.

### Postconditions / Guarantees

- Constructs an exception whose message is formatted as:

```text
{msg} at position {position}
```

- Stores the provided position on the instance as:

```python
self.position == position
```

### Invariants

- Every `ParseError` instance has a `.position` attribute.
- `ParseError` is an `Exception`.

### Side Effects / Exceptions Raised

- No external side effects.
- `__init__` does not explicitly raise parser-specific exceptions.

---

## Public Function: `parse`

### Signature

```python
def parse(text: str)
```

### Preconditions

- `text` is a string containing JSON-like input.
- Leading whitespace is permitted.
- Trailing whitespace after the top-level value is permitted.
- The top-level input must contain exactly one parseable value, ignoring trailing whitespace.

### Postconditions / Return Guarantees

Returns the parsed Python representation of the input:

- JSON object -> `dict`
- JSON array -> `list`
- JSON string -> `str`
- JSON boolean -> `bool`
- JSON `null` -> `None`
- JSON number -> `decimal.Decimal`

Recognized whitespace characters are:

```text
space, tab, newline, carriage return
```

Recognized string escapes include:

```text
\", \\, \/, \n, \t, \r, \b, \f, \uXXXX
```

### Invariants

- The input string is not modified.
- Parsed numbers are returned as `Decimal`, not `int` or `float`.
- Parsing consumes one complete top-level value.
- After parsing, only trailing whitespace may remain.

### Side Effects / Exceptions Raised

- No external side effects.
- Raises `ParseError` if:
  - input ends before a value is found,
  - an unexpected character is encountered,
  - an object key is not a string,
  - required separators such as `:`, `,`, `}`, or `]` are missing,
  - a string is unterminated,
  - a string escape is invalid or incomplete,
  - a boolean, null, or number token is malformed,
  - non-whitespace content remains after the top-level value.

---

## Public Function: `parse_strict`

### Signature

```python
def parse_strict(text: str)
```

### Preconditions

- `text` is a string containing JSON-like input.
- Leading whitespace is permitted.
- Trailing whitespace after the top-level value is not permitted.
- Trailing commas in arrays and objects are not permitted.
- The top-level input must contain exactly one parseable value.

### Postconditions / Return Guarantees

Returns the parsed Python representation of the input:

- JSON object -> `dict`
- JSON array -> `list`
- JSON string -> `str`
- JSON boolean -> `bool`
- JSON `null` -> `None`
- JSON number -> `decimal.Decimal`

### Invariants

- The input string is not modified.
- Parsed numbers are returned as `Decimal`.
- Parsing must finish exactly at the end of `text`.
- Strict mode is applied to array and object comma handling.

### Side Effects / Exceptions Raised

- No external side effects.
- Raises `ParseError` if:
  - input ends before a value is found,
  - an unexpected character is encountered,
  - an object key is not a string,
  - required separators such as `:`, `,`, `}`, or `]` are missing,
  - a string is unterminated,
  - a string escape is invalid or incomplete,
  - a boolean, null, or number token is malformed,
  - a trailing comma appears before `}` or `]`,
  - any content, including whitespace, remains after the top-level value.
