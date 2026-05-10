# Contract: HTTP Header Parser

## `class HeaderError(Exception)`

**Signature**

```python
class HeaderError(Exception)
```

**Purpose**

Exception type raised for invalid header input or invalid header operations.

**Preconditions**

None beyond normal `Exception` construction semantics.

**Postconditions / Return Guarantees**

Instances behave as standard Python exceptions.

**Invariants**

`HeaderError` is an `Exception` subclass.

**Side Effects / Exceptions Raised**

None defined by the class itself.

---

## `class Headers`

**Signature**

```python
class Headers
```

**Purpose**

Case-insensitive, ordered header collection with support for repeated header values.

**Constructor**

```python
Headers()
```

**Preconditions**

None.

**Postconditions / Return Guarantees**

Creates an empty header collection.

**Invariants**

- Header names are stored canonically as lowercase strings.
- Header entries preserve insertion order.
- Repeated headers are retained as separate entries.
- `Set-Cookie` is treated specially by `get`: values are not joined.

**Side Effects / Exceptions Raised**

Constructor does not raise custom exceptions.

---

## `Headers.add`

**Signature**

```python
def add(self, name: str, value: str) -> None
```

**Preconditions**

- `name` must be a non-empty string.
- `value` must be a string.

**Postconditions / Return Guarantees**

- Appends `(name.lower(), value)` to the header collection.
- Preserves existing entries.
- Returns `None`.

**Invariants**

- Added names are stored in lowercase form.
- Entry order is append-only.

**Side Effects / Exceptions Raised**

- Mutates the `Headers` instance.
- Raises `HeaderError("empty header name")` if `name` is empty.

---

## `Headers.get`

**Signature**

```python
def get(self, name: str) -> str | None
```

**Preconditions**

`name` must be a string.

**Postconditions / Return Guarantees**

- Header lookup is case-insensitive.
- If no matching header exists, returns `None`.
- For headers other than `Set-Cookie`, returns all matching values joined with `", "`.
- For `Set-Cookie`, returns the first matching value only.

**Invariants**

Does not mutate the header collection.

**Side Effects / Exceptions Raised**

No custom exceptions are raised.

---

## `Headers.get_all`

**Signature**

```python
def get_all(self, name: str) -> list[str]
```

**Preconditions**

`name` must be a string.

**Postconditions / Return Guarantees**

- Header lookup is case-insensitive.
- Returns a list of all matching values in insertion order.
- Returns an empty list if no matching header exists.

**Invariants**

Does not mutate the header collection.

**Side Effects / Exceptions Raised**

No custom exceptions are raised.

---

## `Headers.raw`

**Signature**

```python
def raw(self) -> list[tuple[str, str]]
```

**Preconditions**

None.

**Postconditions / Return Guarantees**

- Returns a shallow copy of the stored header entries.
- Entries are returned as `(lowercase_name, value)` tuples.
- Order matches insertion order.

**Invariants**

Does not mutate the header collection.

**Side Effects / Exceptions Raised**

No custom exceptions are raised.

---

## `parse_headers`

**Signature**

```python
def parse_headers(text: str) -> Headers
```

**Preconditions**

- `text` must be a string containing HTTP header lines.
- Header lines must use the form `Name: Value`.
- Continuation lines must follow an existing header and begin with space or tab.
- Header names must be non-empty after stripping surrounding whitespace.
- Header names must not contain a space character.

**Postconditions / Return Guarantees**

Returns a `Headers` instance populated from `text`.

Parsing guarantees:

- Both LF and CRLF line endings are tolerated.
- A blank line terminates parsing.
- Text after the first blank line is ignored.
- Header names are stripped, lowercased, and stored canonically.
- Header values are stripped of leading and trailing whitespace.
- Folded continuation lines are appended to the previous value with a single separating space.
- Repeated headers are retained as multiple entries.
- Retrieval behavior is provided by the returned `Headers` object.

**Invariants**

- The returned object satisfies all `Headers` invariants.
- Parsed entries preserve source order up to the first empty line.

**Side Effects / Exceptions Raised**

Raises `HeaderError` when:

- `text is None`
- a folded line appears before any header
- a non-empty line has no `:`
- a header name is empty after stripping
- a header name contains a space character
