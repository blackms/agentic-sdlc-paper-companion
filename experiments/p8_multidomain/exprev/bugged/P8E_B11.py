"""Expression evaluator — minimal AST-based math evaluator.

Public API:
- tokenize(text) -> list[Token]
- parse(tokens) -> Expr
- evaluate(expr, env=None) -> Decimal
- run(text, env=None) -> Decimal  (composition)

Grammar:
  expr   := term (('+' | '-') term)*
  term   := factor (('*' | '/') factor)*
  factor := '-'? primary ('^' factor)?    (right-assoc power)
  primary := NUMBER | NAME | '(' expr ')'

NUMBER:  one or more digits, optionally with '.' decimal part
NAME:    [a-zA-Z_][a-zA-Z0-9_]*
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal


class EvalError(Exception):
    pass


@dataclass
class Token:
    kind: str   # NUMBER, NAME, OP, LPAREN, RPAREN, EOF
    value: str
    pos: int


@dataclass
class Expr:
    """Variant: kind in {num, name, binop, unaryminus}."""
    kind: str
    value: Decimal | str | None = None
    left: "Expr | None" = None
    right: "Expr | None" = None
    op: str | None = None


_OPS = "+-*/^"


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in " \t\n\r":
            i += 1
            continue
        if ch.isdigit() or (ch == "." and i + 1 < len(text) and text[i + 1].isdigit()):
            start = i
            saw_dot = False
            while i < len(text) and (text[i].isdigit() or (text[i] == "." and not saw_dot)):
                if text[i] == ".":
                    saw_dot = True
                i += 1
            tokens.append(Token("NUMBER", text[start:i], start))
            continue
        if ch.isalpha() or ch == "_":
            start = i
            while i < len(text) and (text[i].isalnum() or text[i] == "_"):
                i += 1
            tokens.append(Token("NAME", text[start:i], start))
            continue
        if ch in _OPS:
            tokens.append(Token("OP", ch, i))
            i += 1
            continue
        if ch == "(":
            tokens.append(Token("LPAREN", "(", i))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token("RPAREN", ")", i))
            i += 1
            continue
        raise TypeError(f"unexpected character {ch!r} at {i}")
    tokens.append(Token("EOF", "", len(text)))
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def parse_expr(self) -> Expr:
        left = self.parse_term()
        while self._peek().kind == "OP" and self._peek().value in "+-":
            op = self._advance().value
            right = self.parse_term()
            left = Expr(kind="binop", op=op, left=left, right=right)
        return left

    def parse_term(self) -> Expr:
        left = self.parse_factor()
        while self._peek().kind == "OP" and self._peek().value in "*/":
            op = self._advance().value
            right = self.parse_factor()
            left = Expr(kind="binop", op=op, left=left, right=right)
        return left

    def parse_factor(self) -> Expr:
        if self._peek().kind == "OP" and self._peek().value == "-":
            self._advance()
            inner = self.parse_factor()
            return Expr(kind="unaryminus", left=inner)
        base = self.parse_primary()
        if self._peek().kind == "OP" and self._peek().value == "^":
            self._advance()
            exp = self.parse_factor()  # right-assoc
            return Expr(kind="binop", op="^", left=base, right=exp)
        return base

    def parse_primary(self) -> Expr:
        t = self._advance()
        if t.kind == "NUMBER":
            return Expr(kind="num", value=Decimal(t.value))
        if t.kind == "NAME":
            return Expr(kind="name", value=t.value)
        if t.kind == "LPAREN":
            inner = self.parse_expr()
            close = self._advance()
            if close.kind != "RPAREN":
                raise EvalError(f"expected ')' at {close.pos}")
            return inner
        raise EvalError(f"unexpected token {t.kind} at {t.pos}")


def parse(tokens: list[Token]) -> Expr:
    p = _Parser(tokens)
    expr = p.parse_expr()
    if p._peek().kind != "EOF":
        raise EvalError(f"trailing tokens at {p._peek().pos}")
    return expr


def evaluate(expr: Expr, env: dict | None = None) -> Decimal:
    env = env or {}
    if expr.kind == "num":
        return Decimal(str(expr.value))
    if expr.kind == "name":
        if expr.value not in env:
            raise EvalError(f"undefined name {expr.value!r}")
        return Decimal(str(env[expr.value]))
    if expr.kind == "unaryminus":
        return -evaluate(expr.left, env)
    if expr.kind == "binop":
        a = evaluate(expr.left, env)
        b = evaluate(expr.right, env)
        if expr.op == "+":
            return a + b
        if expr.op == "-":
            return a - b
        if expr.op == "*":
            return a * b
        if expr.op == "/":
            if b == 0:
                raise EvalError("division by zero")
            return a / b
        if expr.op == "^":
            if b != int(b):
                raise EvalError("non-integer exponent not supported")
            return a ** int(b)
    raise EvalError(f"unknown expression kind {expr.kind!r}")


def run(text: str, env: dict | None = None) -> Decimal:
    return evaluate(parse(tokenize(text)), env)
