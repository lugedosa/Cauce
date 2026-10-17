"""Lexer, AST y parser recursivo; no utiliza eval ni exec de Python."""
from dataclasses import dataclass
import json
import re


class CauceError(Exception):
    def __init__(self, message, token=None):
        self.message = message
        self.token = token
        super().__init__(message)

    def __str__(self):
        prefix = f"{self.token.line}:{self.token.column}: " if self.token else ""
        return prefix + self.message


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    line: int
    column: int


KEYWORDS = set("input cell fn require emit if then else and or not true false Int Bool Text".split())
PATTERN = re.compile(
    r'(?P<space>\s+)|(?P<comment>\#[^\n]*)|(?P<int>[0-9]+)|'
    r'(?P<string>"(?:[^"\\\r\n]|\\[^\r\n])*")|'
    r'(?P<name>[A-Za-z_][A-Za-z_0-9]*)|'
    r'(?P<op>->|==|!=|<=|>=|//|[+*%<>=:;,()\[\]{}\-])'
)


def lex(source):
    tokens = []
    offset, line, column = 0, 1, 1
    while offset < len(source):
        match = PATTERN.match(source, offset)
        if not match:
            raise CauceError(f"Carácter inesperado {source[offset]!r}", Token("", "", line, column))
        text = match.group()
        kind = match.lastgroup
        if kind not in ("space", "comment"):
            kind = text if kind == "op" or text in KEYWORDS else kind
            tokens.append(Token(kind, text, line, column))
        if "\n" in text:
            line += text.count("\n")
            column = len(text.rsplit("\n", 1)[1]) + 1
        else:
            column += len(text)
        offset = match.end()
    tokens.append(Token("eof", "", line, column))
    return tokens


@dataclass(frozen=True)
class Type:
    name: str
    element: object = None

    def __str__(self):
        return f"[{self.element}]" if self.name == "List" else self.name


INT, BOOL, TEXT = Type("Int"), Type("Bool"), Type("Text")


@dataclass(frozen=True)
class Expr:
    kind: str
    value: object
    args: tuple
    token: Token


@dataclass(frozen=True)
class Decl:
    kind: str
    name: str
    annotation: object
    params: tuple
    expr: Expr
    token: Token
    message: str = ""


class Parser:
    PRECEDENCE = {"or": 1, "and": 2, "==": 3, "!=": 3,
                  "<": 4, "<=": 4, ">": 4, ">=": 4,
                  "+": 5, "-": 5, "*": 6, "//": 6, "%": 6}

    def __init__(self, source):
        self.tokens = lex(source)
        self.position = 0

    @property
    def current(self):
        return self.tokens[self.position]

    def accept(self, kind):
        if self.current.kind == kind:
            token = self.current
            self.position += 1
            return token
        return None

    def expect(self, kind):
        token = self.accept(kind)
        if token is None:
            raise CauceError(f"Se esperaba {kind!r}; se encontró {self.current.text!r}", self.current)
        return token

    def type(self):
        if self.accept("["):
            element = self.type()
            self.expect("]")
            return Type("List", element)
        token = self.current
        for name, value in (("Int", INT), ("Bool", BOOL), ("Text", TEXT)):
            if self.accept(name):
                return value
        raise CauceError("Se esperaba Int, Bool, Text o [Tipo]", token)

    def parse(self):
        declarations = []
        while self.current.kind != "eof":
            token = self.current
            kind = token.kind
            if kind not in ("input", "cell", "fn", "require", "emit"):
                raise CauceError("Se esperaba input, cell, fn, require o emit", token)
            self.position += 1
            name, annotation, params, message = "", None, [], ""
            if kind in ("input", "cell", "fn"):
                name = self.expect("name").text
                if kind == "fn":
                    self.expect("(")
                    if self.current.kind != ")":
                        while True:
                            param = self.expect("name")
                            self.expect(":")
                            params.append((param.text, self.type()))
                            if not self.accept(","):
                                break
                    self.expect(")")
                    self.expect("->")
                    annotation = self.type()
                elif kind == "input":
                    self.expect(":")
                    annotation = self.type()
                elif self.accept(":"):
                    annotation = self.type()
                self.expect("=")
            expr = self.expression()
            if kind == "require":
                self.expect(",")
                message = self.string(self.expect("string"))
            self.expect(";")
            declarations.append(Decl(kind, name, annotation, tuple(params), expr, token, message))
        return declarations

    @staticmethod
    def string(token):
        try:
            return json.loads(token.text)
        except ValueError:
            raise CauceError("Cadena inválida; usa escapes JSON", token) from None

    def expression(self, minimum=0):
        token = self.current
        if self.accept("if"):
            condition = self.expression()
            self.expect("then")
            yes = self.expression()
            self.expect("else")
            left = Expr("if", None, (condition, yes, self.expression()), token)
        elif self.current.kind in ("-", "not"):
            self.position += 1
            left = Expr("unary", token.kind, (self.expression(7),), token)
        elif self.accept("int"):
            try:
                value = int(token.text)
            except ValueError:
                raise CauceError("Literal entero demasiado grande", token) from None
            left = Expr("literal", value, (), token)
        elif self.accept("string"):
            left = Expr("literal", self.string(token), (), token)
        elif self.current.kind in ("true", "false"):
            self.position += 1
            left = Expr("literal", token.kind == "true", (), token)
        elif self.accept("["):
            items = []
            if self.current.kind != "]":
                while True:
                    items.append(self.expression())
                    if not self.accept(","):
                        break
            self.expect("]")
            left = Expr("list", None, tuple(items), token)
        elif self.accept("("):
            left = self.expression()
            self.expect(")")
        elif self.accept("name"):
            if self.accept("("):
                args = []
                if self.current.kind != ")":
                    while True:
                        args.append(self.expression())
                        if not self.accept(","):
                            break
                self.expect(")")
                left = Expr("call", token.text, tuple(args), token)
            else:
                left = Expr("name", token.text, (), token)
        else:
            raise CauceError("Se esperaba una expresión", token)
        while self.current.kind in self.PRECEDENCE and self.PRECEDENCE[self.current.kind] >= minimum:
            operator = self.current
            self.position += 1
            right = self.expression(self.PRECEDENCE[operator.kind] + 1)
            left = Expr("binary", operator.kind, (left, right), operator)
        return left


def parse(source):
    return Parser(source).parse()
