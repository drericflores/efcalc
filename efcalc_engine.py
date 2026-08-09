"""Safe expression engine for EfCalc Pro 5.0.0."""

import math
from dataclasses import dataclass


class CalcError(Exception):
    """A user-facing calculation or syntax error."""


NUMBER, IDENT, PLUS, MINUS, MUL, DIV, MOD, POWER = (
    "NUMBER", "IDENT", "PLUS", "MINUS", "MUL", "DIV", "MOD", "POWER"
)
LPAREN, RPAREN, COMMA, FACT, EOF = "LPAREN", "RPAREN", "COMMA", "FACT", "EOF"


@dataclass(frozen=True)
class Token:
    kind: str
    value: object = None
    position: int = 0


class Lexer:
    SYMBOLS = {
        "+": PLUS, "-": MINUS, "*": MUL, "/": DIV, "%": MOD,
        "^": POWER, "(": LPAREN, ")": RPAREN, "[": LPAREN,
        "]": RPAREN, "{": LPAREN, "}": RPAREN, ",": COMMA, "!": FACT,
    }

    def __init__(self, text):
        self.text = text
        self.position = 0

    def generate_tokens(self):
        tokens = []
        while self.position < len(self.text):
            char = self.text[self.position]
            if char.isspace():
                self.position += 1
            elif char.isdigit() or char == ".":
                tokens.append(self._number())
            elif char.isalpha() or char == "_":
                tokens.append(self._identifier())
            elif char in self.SYMBOLS:
                tokens.append(Token(self.SYMBOLS[char], char, self.position))
                self.position += 1
            else:
                raise CalcError(f"Illegal character '{char}' at position {self.position}")
        tokens.append(Token(EOF, position=self.position))
        return tokens

    def _number(self):
        start = self.position
        digits = 0
        dots = 0
        while self.position < len(self.text):
            char = self.text[self.position]
            if char.isdigit():
                digits += 1
            elif char == "." and dots == 0:
                dots += 1
            else:
                break
            self.position += 1
        if digits == 0:
            raise CalcError(f"Invalid number at position {start}")
        if self.position < len(self.text) and self.text[self.position] in "eE":
            self.position += 1
            if self.position < len(self.text) and self.text[self.position] in "+-":
                self.position += 1
            exponent_start = self.position
            while self.position < len(self.text) and self.text[self.position].isdigit():
                self.position += 1
            if self.position == exponent_start:
                raise CalcError(f"Invalid scientific notation at position {start}")
        value_text = self.text[start:self.position]
        try:
            value = float(value_text) if any(c in value_text for c in ".eE") else int(value_text)
        except ValueError as error:
            raise CalcError(f"Invalid number: {value_text}") from error
        return Token(NUMBER, value, start)

    def _identifier(self):
        start = self.position
        while self.position < len(self.text):
            char = self.text[self.position]
            if not (char.isalnum() or char == "_"):
                break
            self.position += 1
        return Token(IDENT, self.text[start:self.position].lower(), start)


@dataclass
class NumberNode:
    value: object


@dataclass
class ConstantNode:
    name: str


@dataclass
class UnaryNode:
    operator: str
    operand: object


@dataclass
class BinaryNode:
    left: object
    operator: str
    right: object


@dataclass
class FunctionNode:
    name: str
    arguments: list


@dataclass
class FactorialNode:
    operand: object


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    @property
    def current(self):
        return self.tokens[self.index]

    def advance(self):
        token = self.current
        self.index += 1
        return token

    def parse(self):
        if self.current.kind == EOF:
            raise CalcError("Enter an expression")
        node = self.expression()
        if self.current.kind != EOF:
            raise CalcError(f"Unexpected token '{self.current.value}' at position {self.current.position}")
        return node

    def expression(self):
        node = self.term()
        while self.current.kind in (PLUS, MINUS):
            operator = self.advance().kind
            node = BinaryNode(node, operator, self.term())
        return node

    def term(self):
        node = self.unary()
        while True:
            if self.current.kind in (MUL, DIV, MOD):
                operator = self.advance().kind
                node = BinaryNode(node, operator, self.unary())
            elif self.current.kind in (NUMBER, IDENT, LPAREN):
                node = BinaryNode(node, MUL, self.unary())
            else:
                return node

    def unary(self):
        if self.current.kind in (PLUS, MINUS):
            operator = self.advance().kind
            return UnaryNode(operator, self.unary())
        return self.power()

    def power(self):
        node = self.postfix()
        if self.current.kind == POWER:
            self.advance()
            node = BinaryNode(node, POWER, self.unary())
        return node

    def postfix(self):
        node = self.primary()
        while self.current.kind == FACT:
            self.advance()
            node = FactorialNode(node)
        return node

    def primary(self):
        token = self.current
        if token.kind == NUMBER:
            self.advance()
            return NumberNode(token.value)
        if token.kind == LPAREN:
            self.advance()
            node = self.expression()
            if self.current.kind != RPAREN:
                raise CalcError("Expected a closing parenthesis")
            self.advance()
            return node
        if token.kind == IDENT:
            name = self.advance().value
            if self.current.kind != LPAREN:
                return ConstantNode(name)
            self.advance()
            arguments = []
            if self.current.kind != RPAREN:
                arguments.append(self.expression())
                while self.current.kind == COMMA:
                    self.advance()
                    arguments.append(self.expression())
            if self.current.kind != RPAREN:
                raise CalcError(f"Expected ')' after function '{name}'")
            self.advance()
            return FunctionNode(name, arguments)
        raise CalcError(f"Expected a number, constant, function, or '(' at position {token.position}")


class Interpreter:
    def __init__(
        self, angle_unit="degrees", ans=0.0, variables=None,
        user_functions=None,
    ):
        if angle_unit not in ("degrees", "radians", "gradians"):
            raise ValueError(f"Unsupported angle unit: {angle_unit}")
        self.angle_unit = angle_unit
        # The GUI uses membership in this collection to decide whether a
        # calculator button should insert a function call. Keep this public
        # compatibility API while the interface is migrated away from the
        # legacy in-file engine.
        self.functions = frozenset({
            "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
            "log", "ln", "log_b", "sqrt", "exp", "abs", "fact",
        })
        self.constants = {"pi": math.pi, "e": math.e, "ans": ans}
        self.variables = {
            str(name).lower(): value for name, value in (variables or {}).items()
        }
        self.user_functions = {
            str(name).lower(): function
            for name, function in (user_functions or {}).items()
        }

    def visit(self, node):
        if isinstance(node, NumberNode):
            return node.value
        if isinstance(node, ConstantNode):
            if node.name in self.constants:
                return self.constants[node.name]
            if node.name in self.variables:
                return self.variables[node.name]
            raise CalcError(f"Unknown constant or variable: {node.name}")
        if isinstance(node, UnaryNode):
            value = self.visit(node.operand)
            return -value if node.operator == MINUS else value
        if isinstance(node, BinaryNode):
            return self._binary(node)
        if isinstance(node, FunctionNode):
            return self._function(node)
        if isinstance(node, FactorialNode):
            value = self.visit(node.operand)
            if not self._integer_like(value) or value < 0:
                raise CalcError("Factorial requires a non-negative integer")
            return math.factorial(int(value))
        raise CalcError("Internal calculation error")

    def _binary(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        if node.operator == PLUS:
            return left + right
        if node.operator == MINUS:
            return left - right
        if node.operator == MUL:
            return left * right
        if node.operator == DIV:
            if right == 0:
                raise CalcError("Division by zero")
            return left / right
        if node.operator == MOD:
            if right == 0:
                raise CalcError("Modulo by zero")
            if not (self._integer_like(left) and self._integer_like(right)):
                raise CalcError("Modulo operands must be integers")
            return int(left) % int(right)
        if left < 0 and not self._integer_like(right):
            raise CalcError("A negative base requires an integer exponent in real mode")
        try:
            return left ** right
        except OverflowError as error:
            raise CalcError("Result is too large") from error

    def _function(self, node):
        values = [self.visit(argument) for argument in node.arguments]
        if node.name in self.user_functions:
            try:
                return self.user_functions[node.name](*values)
            except CalcError:
                raise
            except TypeError as error:
                raise CalcError(
                    f"Invalid arguments for formula '{node.name}'"
                ) from error
        expected = 2 if node.name == "log_b" else 1
        if len(values) != expected:
            raise CalcError(f"Function '{node.name}' requires {expected} argument(s)")
        functions = {
            "sin": lambda x: math.sin(self._to_radians(x)),
            "cos": lambda x: math.cos(self._to_radians(x)),
            "tan": lambda x: math.tan(self._to_radians(x)),
            "asin": lambda x: self._from_radians(self._inverse(math.asin, x)),
            "acos": lambda x: self._from_radians(self._inverse(math.acos, x)),
            "atan": lambda x: self._from_radians(math.atan(x)),
            "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
            "asinh": math.asinh, "acosh": math.acosh, "atanh": math.atanh,
            "log": lambda x: self._positive(math.log10, x, "log"),
            "ln": lambda x: self._positive(math.log, x, "ln"),
            "sqrt": self._sqrt, "exp": math.exp, "abs": abs,
            "fact": self._factorial, "log_b": self._log_base,
        }
        if node.name not in functions:
            raise CalcError(f"Unknown function: {node.name}")
        try:
            return functions[node.name](*values)
        except CalcError:
            raise
        except (ValueError, OverflowError) as error:
            raise CalcError(f"{node.name} domain or range error") from error

    @staticmethod
    def _integer_like(value):
        return isinstance(value, (int, float)) and math.isfinite(value) and value == int(value)

    def _to_radians(self, value):
        if self.angle_unit == "degrees":
            return math.radians(value)
        if self.angle_unit == "gradians":
            return value * math.pi / 200
        return value

    def _from_radians(self, value):
        if self.angle_unit == "degrees":
            return math.degrees(value)
        if self.angle_unit == "gradians":
            return value * 200 / math.pi
        return value

    @staticmethod
    def _inverse(function, value):
        if not -1 <= value <= 1:
            raise CalcError("Inverse sine/cosine requires -1 <= x <= 1")
        return function(value)

    @staticmethod
    def _positive(function, value, name):
        if value <= 0:
            raise CalcError(f"{name} requires x > 0")
        return function(value)

    @staticmethod
    def _sqrt(value):
        if value < 0:
            raise CalcError("sqrt requires x >= 0")
        return math.sqrt(value)

    def _factorial(self, value):
        if not self._integer_like(value) or value < 0:
            raise CalcError("Factorial requires a non-negative integer")
        return math.factorial(int(value))

    @staticmethod
    def _log_base(value, base):
        if value <= 0 or base <= 0 or base == 1:
            raise CalcError("log_b requires value > 0, base > 0, and base != 1")
        return math.log(value, base)


def evaluate(
    expression, angle_unit="degrees", ans=0.0, variables=None,
    user_functions=None,
):
    """Evaluate one EfCalc expression without importing the GUI."""
    tokens = Lexer(expression).generate_tokens()
    tree = Parser(tokens).parse()
    return Interpreter(
        angle_unit=angle_unit, ans=ans, variables=variables,
        user_functions=user_functions,
    ).visit(tree)
