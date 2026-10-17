"""Comprobación estática, planificación del grafo y evaluación pura."""
from dataclasses import dataclass
import operator

from .syntax import BOOL, INT, TEXT, CauceError, Type, parse


BUILTINS = {"len", "sum", "range", "text"}


def value_type(value, token=None):
    if type(value) is bool:
        return BOOL
    if type(value) is int:
        return INT
    if type(value) is str:
        return TEXT
    raise CauceError("Valor externo no representable en Cauce", token)


def matches(value, expected):
    if expected.name == "List":
        return type(value) is list and all(matches(x, expected.element) for x in value)
    return type(value) is {"Int": int, "Bool": bool, "Text": str}[expected.name]


def walk(expr):
    yield expr
    for arg in expr.args:
        yield from walk(arg)


@dataclass
class Plan:
    declarations: list
    bindings: dict
    functions: dict
    types: dict
    order: list


class Checker:
    def __init__(self, declarations):
        self.declarations = declarations
        self.bindings, self.functions, self.types = {}, {}, {}
        self.visiting, self.order = [], []
        names = set(BUILTINS)
        for decl in declarations:
            if not decl.name:
                continue
            if decl.name in names:
                raise CauceError(f"Nombre duplicado o reservado: {decl.name}", decl.token)
            names.add(decl.name)
            target = self.functions if decl.kind == "fn" else self.bindings
            target[decl.name] = decl

    @staticmethod
    def equal(actual, expected, token):
        if actual != expected:
            raise CauceError(f"Se esperaba {expected}; se obtuvo {actual}", token)

    def binding(self, name, token):
        if name in self.types:
            return self.types[name]
        if name not in self.bindings:
            raise CauceError(f"Celda o entrada desconocida: {name}", token)
        if name in self.visiting:
            cycle = self.visiting[self.visiting.index(name):] + [name]
            raise CauceError("Ciclo de celdas: " + " -> ".join(cycle), token)
        decl = self.bindings[name]
        self.visiting.append(name)
        if decl.kind == "input":
            # Defaults are data, never hidden dependencies or function calls.
            for expr in walk(decl.expr):
                if expr.kind not in ("literal", "list") and not (
                    expr.kind == "unary" and expr.value == "-" and expr.args[0].kind == "literal"
                ):
                    raise CauceError("El valor inicial de input debe ser literal", expr.token)
        actual = self.infer(decl.expr, None, decl.annotation)
        if decl.annotation:
            self.equal(actual, decl.annotation, decl.token)
        self.types[name] = actual
        self.visiting.pop()
        self.order.append(name)
        return actual

    def infer(self, expr, local=None, expected=None):
        kind, args, token = expr.kind, expr.args, expr.token
        if kind == "literal":
            return value_type(expr.value, token)
        if kind == "name":
            if local is not None:
                if expr.value not in local:
                    raise CauceError(f"Una función solo puede leer sus parámetros: {expr.value}", token)
                return local[expr.value]
            return self.binding(expr.value, token)
        if kind == "list":
            element = expected.element if expected and expected.name == "List" else None
            if not args and element is None:
                raise CauceError("Una lista vacía necesita un tipo esperado, por ejemplo cell xs: [Int] = []", token)
            for item in args:
                actual = self.infer(item, local, element)
                if element is None:
                    element = actual
                self.equal(actual, element, item.token)
            return Type("List", element)
        if kind == "unary":
            wanted = BOOL if expr.value == "not" else INT
            self.equal(self.infer(args[0], local, wanted), wanted, token)
            return wanted
        if kind == "if":
            self.equal(self.infer(args[0], local), BOOL, args[0].token)
            yes = self.infer(args[1], local, expected)
            no = self.infer(args[2], local, expected or yes)
            self.equal(no, yes, token)
            return yes
        if kind == "binary":
            left = self.infer(args[0], local)
            right = self.infer(args[1], local, left)
            self.equal(right, left, token)
            op = expr.value
            if op in ("and", "or"):
                self.equal(left, BOOL, token)
                return BOOL
            if op in ("==", "!="):
                return BOOL
            if op == "+" and left == TEXT:
                return TEXT
            self.equal(left, INT, token)
            return BOOL if op in ("<", "<=", ">", ">=") else INT
        if kind == "call":
            name = expr.value
            if name in self.functions:
                fn = self.functions[name]
                if len(args) != len(fn.params):
                    raise CauceError(f"{name} espera {len(fn.params)} argumentos; recibió {len(args)}", token)
                for arg, (_, wanted) in zip(args, fn.params):
                    self.equal(self.infer(arg, local, wanted), wanted, arg.token)
                return fn.annotation
            if name not in BUILTINS:
                raise CauceError(f"Función desconocida: {name}", token)
            if len(args) != 1:
                raise CauceError(f"{name} espera un argumento", token)
            wanted = Type("List", INT) if name == "sum" else INT if name == "range" else None
            actual = self.infer(args[0], local, wanted)
            if wanted:
                self.equal(actual, wanted, token)
            if name == "len" and actual != TEXT and actual.name != "List":
                raise CauceError("len espera Text o una lista", token)
            return Type("List", INT) if name == "range" else TEXT if name == "text" else INT
        raise AssertionError(kind)

    def build(self):
        done, active = set(), []

        def visit(name):
            if name in active:
                raise CauceError("Ciclo de funciones: " + " -> ".join(active + [name]), self.functions[name].token)
            if name in done:
                return
            active.append(name)
            fn = self.functions[name]
            local = dict(fn.params)
            if len(local) != len(fn.params):
                raise CauceError(f"Parámetro duplicado en {name}", fn.token)
            if set(local) & (BUILTINS | set(self.functions)):
                raise CauceError("Un parámetro no puede ocultar el nombre de una función", fn.token)
            for node in walk(fn.expr):
                if node.kind == "call" and node.value in self.functions:
                    visit(node.value)
            self.equal(self.infer(fn.expr, local, fn.annotation), fn.annotation, fn.token)
            active.pop()
            done.add(name)

        for name in self.functions:
            visit(name)
        for name, decl in self.bindings.items():
            self.binding(name, decl.token)
        for decl in self.declarations:
            if decl.kind in ("require", "emit"):
                actual = self.infer(decl.expr)
                if decl.kind == "require":
                    self.equal(actual, BOOL, decl.token)
        return Plan(self.declarations, self.bindings, self.functions, self.types, self.order)


def check(source):
    """Parse and type-check the entire source without evaluating expressions."""
    try:
        return Checker(parse(source)).build()
    except RecursionError:
        raise CauceError("Programa demasiado profundo para este intérprete") from None


def format_value(value):
    if type(value) is str:
        return value
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is list:
        import json
        return json.dumps(value, ensure_ascii=False)
    return str(value)


OPERATORS = {"+": operator.add, "-": operator.sub, "*": operator.mul,
             "//": operator.floordiv, "%": operator.mod, "==": operator.eq,
             "!=": operator.ne, "<": operator.lt, "<=": operator.le,
             ">": operator.gt, ">=": operator.ge}


class Evaluator:
    def __init__(self, plan):
        self.plan = plan
        self.values = {}

    def eval(self, expr, local=None):
        args, kind = expr.args, expr.kind
        try:
            if kind == "literal":
                return expr.value
            if kind == "name":
                return (self.values if local is None else local)[expr.value]
            if kind == "list":
                return [self.eval(arg, local) for arg in args]
            if kind == "if":
                return self.eval(args[1] if self.eval(args[0], local) else args[2], local)
            if kind == "unary":
                value = self.eval(args[0], local)
                return not value if expr.value == "not" else -value
            if kind == "binary":
                left = self.eval(args[0], local)
                if expr.value == "and":
                    return left and self.eval(args[1], local)
                if expr.value == "or":
                    return left or self.eval(args[1], local)
                return OPERATORS[expr.value](left, self.eval(args[1], local))
            if kind == "call":
                values = [self.eval(arg, local) for arg in args]
                name = expr.value
                if name in self.plan.functions:
                    fn = self.plan.functions[name]
                    return self.eval(fn.expr, dict(zip((p[0] for p in fn.params), values)))
                value = values[0]
                if name == "len":
                    return len(value)
                if name == "sum":
                    return sum(value)
                if name == "text":
                    return format_value(value)
                if name == "range":
                    if not 0 <= value <= 100_000:
                        raise CauceError("range requiere un tamaño entre 0 y 100000", expr.token)
                    return list(range(value))
            raise AssertionError(kind)
        except ZeroDivisionError:
            raise CauceError("División entre cero", expr.token) from None
        except (ValueError, OverflowError):
            raise CauceError("Valor fuera de los límites del anfitrión", expr.token) from None

    def execute(self, inputs):
        for name, value in inputs.items():
            decl = self.plan.bindings.get(name)
            if decl is None or decl.kind != "input":
                raise CauceError(f"No existe la entrada: {name}")
            if not matches(value, decl.annotation):
                raise CauceError(f"La entrada {name} requiere {decl.annotation}", decl.token)
        for name in self.plan.order:
            decl = self.plan.bindings[name]
            self.values[name] = inputs[name] if name in inputs else self.eval(decl.expr)
        for decl in self.plan.declarations:
            if decl.kind == "require" and not self.eval(decl.expr):
                raise CauceError("Condición incumplida: " + decl.message, decl.token)
        # Prepare every value and its representation before exposing any output.
        output = []
        for decl in self.plan.declarations:
            if decl.kind == "emit":
                try:
                    output.append(format_value(self.eval(decl.expr)))
                except (ValueError, OverflowError):
                    raise CauceError("Salida fuera de los límites del anfitrión", decl.token) from None
        return output


def run(source, inputs=None):
    """Return all formatted emissions, or raise CauceError without partial output."""
    try:
        return Evaluator(check(source)).execute({} if inputs is None else inputs)
    except (RecursionError, MemoryError):
        raise CauceError("Se alcanzó un límite de recursos del intérprete") from None
