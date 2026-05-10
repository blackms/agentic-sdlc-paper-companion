# Contract: Expression Evaluator Module

## `class EvalError(Exception)`

**Signature**

```python
class EvalError(Exception)
```

**Purpose**

Exception type used to report evaluator, tokenizer, parser, and expression evaluation errors.

**Preconditions**

None beyond standard `Exception` construction rules.

**Postconditions / Guarantees**

- Instances behave as standard Python exceptions.
- Raised by public API functions for specified expression-processing errors.

**Invariants**

- `EvalError` is a subclass of `Exception`.

**Side Effects**

- None on construction.
- May be raised by `tokenize`, `parse`, `evaluate`, and `run`.

---

## `@dataclass class Token`

**Signature**

```python
@dataclass
class Token:
    kind: str
    value: str
    pos: int
```

**Purpose**

Represents a lexical token produced by `tokenize`.

**Fields**

- `kind`: token category. Expected values are `"NUMBER"`, `"NAME"`, `"OP"`, `"LPAREN"`, `"RPAREN"`, or `"EOF"`.
- `value`: source text value for the token.
- `pos`: zero-based character offset in the original input.

**Preconditions**

- Callers constructing `Token` directly should provide:
  - `kind` as a string token category.
  - `value` as the token’s string value.
  - `pos` as an integer source position.

**Postconditions / Guarantees**

- Construction stores the provided field values.
- Dataclass-generated equality, representation, and initialization behavior are available.

**Invariants**

- Tokens produced by `tokenize` always end with one `"EOF"` token.
- Tokens produced by `tokenize` use:
  - `"NUMBER"` for decimal-like numeric literals.
  - `"NAME"` for identifiers.
  - `"OP"` for `+`, `-`, `*`, `/`, `^`.
  - `"LPAREN"` for `"("`.
  - `"RPAREN"` for `")"`.
  - `"EOF"` for end of input.

**Side Effects**

- None.

---

## `@dataclass class Expr`

**Signature**

```python
@dataclass
class Expr:
    kind: str
    value: Decimal | str | None = None
    left: Expr | None = None
    right: Expr | None = None
    op: str | None = None
```

**Purpose**

Represents an expression tree node.

**Fields**

- `kind`: expression variant. Documented variants are `"num"`, `"name"`, `"binop"`, and `"unaryminus"`.
- `value`: numeric value, name value, or `None`.
- `left`: left child expression, if applicable.
- `right`: right child expression, if applicable.
- `op`: binary operator string, if applicable.

**Preconditions**

- Callers constructing `Expr` directly should provide fields consistent with the intended `kind`.

**Postconditions / Guarantees**

- Construction stores the provided field values.
- Dataclass-generated equality, representation, and initialization behavior are available.

**Invariants**

For expression trees produced by `parse`:

- `"num"` nodes store a `Decimal` in `value`.
- `"name"` nodes store a string identifier in `value`.
- `"unaryminus"` nodes store the operand expression in `left`.
- `"binop"` nodes store:
  - operator in `op`.
  - left operand in `left`.
  - right operand in `right`.

**Side Effects**

- None.

---

## `tokenize(text)`

**Signature**

```python
def tokenize(text: str) -> list[Token]
```

**Purpose**

Converts source text into a token list.

**Preconditions**

- `text` is a string.
- Supported syntax characters are:
  - whitespace: space, tab, newline, carriage return.
  - digits.
  - decimal point when beginning or continuing a number.
  - letters and underscore for names.
  - operators: `+`, `-`, `*`, `/`, `^`.
  - parentheses: `(` and `)`.

**Postconditions / Return Guarantees**

- Returns a `list[Token]`.
- Whitespace is skipped and does not produce tokens.
- Numeric literals produce `"NUMBER"` tokens.
- Identifiers produce `"NAME"` tokens.
- Operators produce `"OP"` tokens.
- Parentheses produce `"LPAREN"` and `"RPAREN"` tokens.
- The returned list always ends with:

```python
Token("EOF", "", len(text))
```

- Each token’s `pos` is the zero-based character index where that token begins in `text`.

**Invariants**

- Token order matches source order.
- The EOF token is last.
- Operator token values are one of `+`, `-`, `*`, `/`, `^`.

**Side Effects / Exceptions**

- Raises `EvalError` if an unsupported character is encountered:

```python
EvalError("unexpected character ...")
```

---

## `parse(tokens)`

**Signature**

```python
def parse(tokens: list[Token]) -> Expr
```

**Purpose**

Parses a token stream into an expression tree.

**Preconditions**

- `tokens` is a list of `Token` objects.
- The token stream follows the tokenizer/parser token conventions.
- The token stream contains an `"EOF"` token after the expression.
- The accepted grammar is:

```text
expr    := term (('+' | '-') term)*
term    := factor (('*' | '/') factor)*
factor  := '-'? primary ('^' factor)?
primary := NUMBER | NAME | '(' expr ')'
```

**Postconditions / Return Guarantees**

- Returns an `Expr` tree representing the parsed expression.
- Addition and subtraction are parsed left-associatively.
- Multiplication and division are parsed left-associatively.
- Power expressions are parsed right-associatively.
- Unary minus is represented as an `"unaryminus"` expression.
- Parenthesized expressions return the parsed inner expression.

**Invariants**

- Returned expression nodes use the `Expr` variants:
  - `"num"`
  - `"name"`
  - `"binop"`
  - `"unaryminus"`
- Binary operator nodes use one of:
  - `"+"`
  - `"-"`
  - `"*"`
  - `"/"`
  - `"^"`

**Side Effects / Exceptions**

- Raises `EvalError` if a closing parenthesis is expected but not found.
- Raises `EvalError` if an unexpected token appears where a primary expression is required.
- Raises `EvalError` if tokens remain after the parsed expression before EOF.

---

## `evaluate(expr, env=None)`

**Signature**

```python
def evaluate(expr: Expr, env: dict | None = None) -> Decimal
```

**Purpose**

Evaluates an expression tree to a `Decimal`.

**Preconditions**

- `expr` is an `Expr`.
- `expr.kind` is one of:
  - `"num"`
  - `"name"`
  - `"unaryminus"`
  - `"binop"`
- For `"name"` expressions, `env` contains a value for the expression name.
- Environment values are convertible to `Decimal` through `str(value)`.
- Binary operators are one of `+`, `-`, `*`, `/`, `^`.
- Power exponents are integer-valued.

**Postconditions / Return Guarantees**

- Returns a `Decimal`.
- Numeric expressions return `Decimal(str(expr.value))`.
- Name expressions return `Decimal(str(env[name]))`.
- Unary minus returns the negated evaluation of its operand.
- Binary operations return:
  - `a + b` for `"+"`
  - `a - b` for `"-"`
  - `a * b` for `"*"`
  - `a / b` for `"/"`
  - `a ** int(b)` for `"^"`

**Invariants**

- Evaluation is recursive over the expression tree.
- If `env` is `None`, an empty environment is used.
- The input `expr` tree is not modified.

**Side Effects / Exceptions**

- Raises `EvalError` for an undefined name.
- Raises `EvalError` for division by zero.
- Raises `EvalError` for non-integer exponent values.
- Raises `EvalError` for unknown expression kinds.

---

## `run(text, env=None)`

**Signature**

```python
def run(text: str, env: dict | None = None) -> Decimal
```

**Purpose**

Tokenizes, parses, and evaluates an expression string.

**Preconditions**

- `text` is a string accepted by `tokenize` and `parse`.
- `env`, if provided, supplies values required by any names in the expression.
- Environment values are convertible to `Decimal` through `str(value)`.

**Postconditions / Return Guarantees**

- Returns the same result as:

```python
evaluate(parse(tokenize(text)), env)
```

- The return value is a `Decimal`.

**Invariants**

- `run` performs composition only:
  1. tokenize input text
  2. parse tokens
  3. evaluate expression

**Side Effects / Exceptions**

- Propagates `EvalError` raised by `tokenize`, `parse`, or `evaluate`.
- Does not modify `text`.
- Does not mutate the supplied `env` mapping.
