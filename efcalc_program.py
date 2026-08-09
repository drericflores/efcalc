"""Safe line-oriented programming language for EfCalc Pro."""

import re
from dataclasses import dataclass, field

from efcalc_engine import CalcError, evaluate


class ProgramError(Exception):
    def __init__(self, line_number, message):
        super().__init__(f"Line {line_number}: {message}")
        self.line_number = line_number
        self.message = message


class ProgramStopped(Exception):
    """Raised when the operator requests a controlled program stop."""


@dataclass
class ProgramResult:
    variables: dict = field(default_factory=dict)
    output: list = field(default_factory=list)
    last_result: object = 0.0
    statements_executed: int = 0
    formulas: dict = field(default_factory=dict)


@dataclass(frozen=True)
class FormulaDefinition:
    name: str
    parameters: tuple
    expression: str
    line_number: int


class ProgramInterpreter:
    """Execute EfCalc programs without Python eval or arbitrary code access."""

    ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:=\s*(.+)$")
    FORMULA = re.compile(
        r"^formula\s+([A-Za-z_][A-Za-z0-9_]*)\s*"
        r"\(([^)]*)\)\s*:=\s*(.+)$",
        re.IGNORECASE,
    )
    COMPARISON = re.compile(r"^(.+?)\s*(<=|>=|==|!=|<|>)\s*(.+)$")
    RESERVED = frozenset({
        "pi", "e", "ans", "sin", "cos", "tan", "asin", "acos", "atan",
        "sinh", "cosh", "tanh", "asinh", "acosh", "atanh", "log", "ln",
        "log_b", "sqrt", "exp", "abs", "fact", "print", "if", "else",
        "repeat", "end", "formula",
    })
    MAX_REPEAT = 10_000
    MAX_STATEMENTS = 100_000
    MAX_FORMULA_DEPTH = 100

    def __init__(
        self, angle_unit="degrees", initial_variables=None, ans=0.0,
        stop_requested=None, progress_callback=None, initial_formulas=None,
    ):
        self.angle_unit = angle_unit
        self.variables = {
            str(name).lower(): value for name, value in (initial_variables or {}).items()
        }
        self.ans = ans
        self.formulas = dict(initial_formulas or {})
        self.stop_requested = stop_requested or (lambda: False)
        self.progress_callback = progress_callback
        self._formula_depth = 0

    def run(self, source):
        lines = self._prepare_lines(source)
        result = ProgramResult(
            variables=dict(self.variables),
            last_result=self.ans,
            formulas=dict(self.formulas),
        )
        self._validate_blocks(lines)
        self._execute_range(lines, 0, len(lines), result)
        self.variables = dict(result.variables)
        self.formulas = dict(result.formulas)
        self.ans = result.last_result
        return result

    def evaluate_expression(self, expression):
        """Evaluate one expression against the current program session."""
        result = ProgramResult(
            variables=dict(self.variables),
            last_result=self.ans,
            formulas=dict(self.formulas),
        )
        value = self._evaluate(expression, result)
        self.ans = value
        return value

    @staticmethod
    def _strip_comment(line):
        return line.split("#", 1)[0]

    def _prepare_lines(self, source):
        prepared = []
        for line_number, original in enumerate(source.splitlines(), start=1):
            text = self._strip_comment(original).strip()
            if text:
                prepared.append((line_number, text))
        return prepared

    def _validate_blocks(self, lines):
        stack = []
        for index, (line_number, text) in enumerate(lines):
            keyword = self._keyword(text)
            if keyword in ("if", "repeat"):
                stack.append((keyword, line_number, index))
            elif keyword == "else":
                if not stack or stack[-1][0] != "if":
                    raise ProgramError(line_number, "else requires a matching if")
            elif keyword == "end":
                if not stack:
                    raise ProgramError(line_number, "end has no matching block")
                stack.pop()
        if stack:
            keyword, line_number, _index = stack[-1]
            raise ProgramError(line_number, f"{keyword} block requires end")

    @staticmethod
    def _keyword(text):
        lowered = text.lower().rstrip(":").strip()
        if lowered == "else":
            return "else"
        if lowered == "end":
            return "end"
        if lowered.startswith("if "):
            return "if"
        if lowered.startswith("repeat "):
            return "repeat"
        return None

    def _execute_range(self, lines, start, stop, result):
        index = start
        while index < stop:
            line_number, text = lines[index]
            self._check_limits(result, line_number)
            keyword = self._keyword(text)
            try:
                if keyword == "if":
                    else_index, end_index = self._find_block(lines, index, "if")
                    condition_text = text[2:].strip().rstrip(":").strip()
                    if not condition_text:
                        raise CalcError("if requires a condition")
                    if self._condition(condition_text, result):
                        branch_stop = else_index if else_index is not None else end_index
                        self._execute_range(lines, index + 1, branch_stop, result)
                    elif else_index is not None:
                        self._execute_range(lines, else_index + 1, end_index, result)
                    index = end_index + 1
                    continue
                if keyword == "repeat":
                    _else_index, end_index = self._find_block(lines, index, "repeat")
                    count_text = text[6:].strip().rstrip(":").strip()
                    count = self._evaluate(count_text, result)
                    if not self._integer_like(count) or count < 0:
                        raise CalcError("repeat requires a non-negative integer")
                    if count > self.MAX_REPEAT:
                        raise CalcError(f"repeat limit is {self.MAX_REPEAT}")
                    for _iteration in range(int(count)):
                        self._execute_range(lines, index + 1, end_index, result)
                    index = end_index + 1
                    continue
                if keyword in ("else", "end"):
                    return
                self._execute_statement(text, result, line_number)
                index += 1
            except ProgramStopped:
                raise
            except ProgramError:
                raise
            except CalcError as error:
                raise ProgramError(line_number, str(error)) from error
            except (ValueError, OverflowError) as error:
                raise ProgramError(line_number, str(error)) from error

    def _find_block(self, lines, start, block_type):
        depth = 0
        else_index = None
        for index in range(start + 1, len(lines)):
            line_number, text = lines[index]
            keyword = self._keyword(text)
            if keyword in ("if", "repeat"):
                depth += 1
            elif keyword == "end":
                if depth == 0:
                    return else_index, index
                depth -= 1
            elif keyword == "else" and depth == 0:
                if block_type != "if":
                    raise ProgramError(line_number, "repeat does not support else")
                if else_index is not None:
                    raise ProgramError(line_number, "if block has more than one else")
                else_index = index
        line_number = lines[start][0]
        raise ProgramError(line_number, f"{block_type} block requires end")

    def _execute_statement(self, line, result, line_number):
        formula = self.FORMULA.match(line)
        if formula:
            name, parameter_text, expression = formula.groups()
            self._define_formula(
                name, parameter_text, expression, result,
                line_number=line_number,
            )
            return
        assignment = self.ASSIGNMENT.match(line)
        if assignment:
            name, expression = assignment.groups()
            normalized = name.lower()
            if normalized in self.RESERVED:
                raise CalcError(f"'{name}' is reserved and cannot be assigned")
            value = self._evaluate(expression, result)
            result.variables[normalized] = value
            result.last_result = value
            return
        if line.lower().startswith("print(") and line.endswith(")"):
            expression = line[6:-1].strip()
            if not expression:
                raise CalcError("print requires an expression")
            value = self._evaluate(expression, result)
            result.output.append(self._format(value))
            result.last_result = value
            return
        value = self._evaluate(line, result)
        result.output.append(self._format(value))
        result.last_result = value

    def _condition(self, condition, result):
        comparison = self.COMPARISON.match(condition)
        if not comparison:
            return bool(self._evaluate(condition, result))
        left_text, operator, right_text = comparison.groups()
        left = self._evaluate(left_text, result)
        right = self._evaluate(right_text, result)
        operations = {
            "<": lambda: left < right,
            "<=": lambda: left <= right,
            ">": lambda: left > right,
            ">=": lambda: left >= right,
            "==": lambda: left == right,
            "!=": lambda: left != right,
        }
        return operations[operator]()

    def _evaluate(self, expression, result):
        callbacks = {
            name: self._formula_callback(definition, result)
            for name, definition in result.formulas.items()
        }
        return evaluate(
            expression,
            angle_unit=self.angle_unit,
            ans=result.last_result,
            variables=result.variables,
            user_functions=callbacks,
        )

    def _define_formula(
        self, name, parameter_text, expression, result, line_number,
    ):
        normalized = name.lower()
        if normalized in self.RESERVED:
            raise CalcError(f"'{name}' is reserved and cannot name a formula")
        parameters = []
        if parameter_text.strip():
            for parameter in parameter_text.split(","):
                parameter = parameter.strip().lower()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", parameter):
                    raise CalcError(f"Invalid formula parameter: {parameter}")
                if parameter in self.RESERVED:
                    raise CalcError(f"Reserved formula parameter: {parameter}")
                if parameter in parameters:
                    raise CalcError(f"Duplicate formula parameter: {parameter}")
                parameters.append(parameter)
        result.formulas[normalized] = FormulaDefinition(
            normalized, tuple(parameters), expression.strip(), line_number,
        )

    def _formula_callback(self, definition, result):
        def call_formula(*arguments):
            if len(arguments) != len(definition.parameters):
                raise CalcError(
                    f"Formula '{definition.name}' requires "
                    f"{len(definition.parameters)} argument(s)"
                )
            if self._formula_depth >= self.MAX_FORMULA_DEPTH:
                raise CalcError("Formula recursion limit exceeded")
            local_variables = dict(result.variables)
            local_variables.update(zip(definition.parameters, arguments))
            self._formula_depth += 1
            try:
                callbacks = {
                    name: self._formula_callback(item, result)
                    for name, item in result.formulas.items()
                }
                return evaluate(
                    definition.expression,
                    angle_unit=self.angle_unit,
                    ans=result.last_result,
                    variables=local_variables,
                    user_functions=callbacks,
                )
            finally:
                self._formula_depth -= 1
        return call_formula

    def _check_limits(self, result, line_number):
        if self.stop_requested():
            raise ProgramStopped("Program stopped by operator")
        result.statements_executed += 1
        if result.statements_executed > self.MAX_STATEMENTS:
            raise ProgramError(line_number, "program statement limit exceeded")
        if self.progress_callback:
            self.progress_callback(line_number)

    @staticmethod
    def _integer_like(value):
        return isinstance(value, (int, float)) and value == int(value)

    @staticmethod
    def _format(value):
        if isinstance(value, float):
            return f"{value:.12g}"
        return str(value)
