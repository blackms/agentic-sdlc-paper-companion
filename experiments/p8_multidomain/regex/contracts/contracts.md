# Contract Document

## `class RegexError(Exception)`

**Signature**

```python
class RegexError(Exception)
```

**Preconditions**

- Used to signal invalid regex pattern syntax during compilation.

**Postconditions / Return Guarantees**

- Instances behave as standard Python exceptions.
- Carries any message passed through normal `Exception` construction.

**Invariants**

- Subclass of `Exception`.

**Side Effects / Exceptions Raised**

- No side effects from the class definition itself.
- Raised by `compile()` / compiler parsing logic for invalid patterns.

---

## `class State`

**Signature**

```python
@dataclass(eq=False)
class State:
    sid: int
    is_final: bool = False
    transitions: list[tuple[str | None, "State"]] = field(default_factory=list)
```

### `State.__init__`

**Signature**

```python
State(sid: int, is_final: bool = False, transitions: list[tuple[str | None, State]] = ...)
```

**Preconditions**

- `sid` is intended to be an integer state identifier.
- `is_final` is intended to be a boolean.
- `transitions` is intended to contain `(symbol, target)` pairs where:
  - `symbol is None` represents an epsilon transition.
  - `symbol == "."` represents a wildcard transition.
  - Any other string symbol represents a literal match.
  - `target` is a `State`.

**Postconditions / Return Guarantees**

- Creates a `State` instance with the supplied fields.
- If `transitions` is omitted, a new empty list is created for that instance.

**Invariants**

- Equality is identity-based because `eq=False`.
- `transitions` is mutable.
- `is_final` marks whether the state is accepting.

**Side Effects / Exceptions Raised**

- No explicit exceptions are raised by the class body beyond normal dataclass initialization behavior.

### `State.__hash__`

**Signature**

```python
def __hash__(self) -> int
```

**Preconditions**

- `self` is a `State` instance.

**Postconditions / Return Guarantees**

- Returns `id(self)`.
- Enables `State` instances to be used in sets and as dictionary keys.

**Invariants**

- Hash value is based on object identity.

**Side Effects / Exceptions Raised**

- No side effects.
- Raises no explicit exceptions.

---

## `class NFA`

**Signature**

```python
@dataclass
class NFA:
    start: State
    final: State
    n_states: int = 0
```

### `NFA.__init__`

**Signature**

```python
NFA(start: State, final: State, n_states: int = 0)
```

**Preconditions**

- `start` is intended to be the starting `State`.
- `final` is intended to be the accepting `State`.
- `n_states` is intended to be the number of states allocated during compilation.

**Postconditions / Return Guarantees**

- Creates an NFA container with `start`, `final`, and `n_states`.

**Invariants**

- `start` references the entry state for matching.
- `final` references the designated final state.
- NFAs produced by `compile()` have `final.is_final == True`.

**Side Effects / Exceptions Raised**

- No explicit exceptions are raised by the class body beyond normal dataclass initialization behavior.

---

## `compile`

**Signature**

```python
def compile(pattern: str) -> NFA
```

**Preconditions**

- `pattern` is a regex pattern string.
- Supported syntax:
  - Literal characters.
  - `.` wildcard matching any single character.
  - `*` for zero or more repetitions of the preceding atom.
  - `+` for one or more repetitions of the preceding atom.
  - `?` for zero or one occurrence of the preceding atom.
  - `|` alternation.
  - `(` and `)` grouping.
  - Backslash escapes for metacharacters and other characters.

**Postconditions / Return Guarantees**

- Returns an `NFA`.
- The returned NFA has:
  - `start` set to the compiled start state.
  - `final` set to the compiled final state.
  - `final.is_final == True`.
  - `n_states` equal to the compiler’s allocated state count.
- Empty concatenation produces an epsilon-only fragment.
- The empty pattern compiles to an NFA whose start/final state is accepting.

**Invariants**

- The compiled NFA uses epsilon transitions represented by `symbol is None`.
- Literal and wildcard transitions are stored in each state’s `transitions` list.
- State identifiers are allocated incrementally during compilation.

**Side Effects / Exceptions Raised**

- Raises `RegexError` for invalid pattern syntax, including:
  - Unexpected end of pattern.
  - Trailing backslash.
  - Unexpected unescaped metacharacters.
  - Missing closing parenthesis.
  - Trailing unparsed pattern content.
- Mutates the generated final state by setting `is_final = True`.
- Allocates new `State` objects.

---

## `match`

**Signature**

```python
def match(nfa: NFA, text: str) -> bool
```

**Preconditions**

- `nfa` is an `NFA`, typically produced by `compile()`.
- `text` is the input string to test.

**Postconditions / Return Guarantees**

- Returns `True` if the NFA accepts the entire `text`.
- Returns `False` if the NFA cannot consume the full input and end in a final state.
- Matching uses runtime subset construction with epsilon closure.
- A wildcard transition with symbol `"."` matches any single input character.
- Literal transitions match only equal characters.
- Epsilon transitions consume no input.

**Invariants**

- Matching begins from the epsilon closure of `{nfa.start}`.
- After each input character, the active state set is advanced and epsilon-closed.
- Acceptance is determined by whether any current state has `is_final == True`.

**Side Effects / Exceptions Raised**

- No intentional mutation of the NFA or text.
- Raises no explicit custom exceptions.
- Normal Python exceptions may occur if `nfa` does not provide the expected `start` state structure.
