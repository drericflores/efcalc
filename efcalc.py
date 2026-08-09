#
# GPL3 License Notice
# EfCalc Pro - A Python-based Scientific Calculator
#
# Copyright (C) 2024 Dr. Eric O. Flores – E-mail: <eoftoro@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

import sys
import math
import re
import html
from urllib.parse import quote, unquote

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit,
    QGridLayout, QMenuBar, QAction, QDialog, QTabWidget, QTextBrowser,
    QSpinBox, QHBoxLayout, QWidgetAction, QActionGroup, QMainWindow, QLabel
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QTimer, QUrl

# EfCalc Pro 5.0.0 calculation engine. These imports intentionally replace the
# legacy in-file engine during the controlled migration.
from efcalc_engine import CalcError, Interpreter, Lexer, Parser

# --- Custom Exception for clearer error handling ---
class CalcError(Exception):
    pass

# --- Token Definitions ---
TT_NUMBER = 'NUMBER'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MULTIPLY = 'MULTIPLY'
TT_DIVIDE = 'DIVIDE'
TT_MODULO = 'MODULO'
TT_POWER = 'POWER'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_IDENTIFIER = 'IDENTIFIER'
TT_COMMA = 'COMMA'
TT_EOF = 'EOF'
TT_ASSIGN = 'ASSIGN'
TT_FACT = 'FACT'

class Token:
    def __init__(self, type, value=None, pos_start=None):
        self.type = type
        self.value = value
        self.pos_start = pos_start

    def __repr__(self):
        if self.value is not None:
            return f"Token({self.type}, {self.value})"
        return f"Token({self.type})"

# --- Lexer (Tokenizer) ---
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = -1
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()
        
        # Handle scientific notation
        if self.current_char in ('e', 'E'):
            exponent_str = self.current_char
            self.advance()
            if self.current_char in ('+', '-'):
                exponent_str += self.current_char
                self.advance()
            if not (self.current_char and self.current_char.isdigit()):
                raise CalcError(f"Invalid scientific notation at position {self.pos}")
            while self.current_char is not None and self.current_char.isdigit():
                exponent_str += self.current_char
                self.advance()
            num_str += exponent_str
        
        try:
            if dot_count == 0 and 'e' not in num_str and 'E' not in num_str:
                return Token(TT_NUMBER, int(num_str), pos_start)
            else:
                return Token(TT_NUMBER, float(num_str), pos_start)
        except ValueError:
            raise CalcError(f"Invalid number format: {num_str}")

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()
        return Token(TT_IDENTIFIER, id_str, pos_start)

    def generate_tokens(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char.isdigit() or self.current_char == '.':
                tokens.append(self.make_number())
            elif self.current_char == ':' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                tokens.append(Token(TT_ASSIGN, pos_start=self.pos))
                self.advance()
                self.advance()
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MULTIPLY, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIVIDE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '%':
                tokens.append(Token(TT_MODULO, pos_start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_POWER, pos_start=self.pos))
                self.advance()
            elif self.current_char in '([{':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char in ')]}':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                tokens.append(Token(TT_FACT, pos_start=self.pos))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            elif self.current_char.isalpha():
                tokens.append(self.make_identifier())
            else:
                raise CalcError(f"Illegal character '{self.current_char}' at position {self.pos}")
        tokens.append(Token(TT_EOF))
        return tokens

# --- AST Nodes ---
class ASTNode: 
    pass

class NumberNode(ASTNode):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class BinOpNode(ASTNode):
    def __init__(self, left, op_token, right):
        self.left = left
        self.op_token = op_token
        self.right = right

class UnaryOpNode(ASTNode):
    def __init__(self, op_token, operand):
        self.op_token = op_token
        self.operand = operand

class FunctionCallNode(ASTNode):
    def __init__(self, identifier_token, args):
        self.identifier_token = identifier_token
        self.function_name = identifier_token.value
        self.args = args

class ConstantNode(ASTNode):
    def __init__(self, identifier_token):
        self.identifier_token = identifier_token
        self.name = identifier_token.value

class PostfixOpNode(ASTNode):
    def __init__(self, operand, op_token):
        self.operand = operand
        self.op_token = op_token

# --- Parser ---
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.current_token = None
        self.advance()

    def advance(self):
        self.token_idx += 1
        self.current_token = self.tokens[self.token_idx] if self.token_idx < len(self.tokens) else None

    def parse(self):
        if self.current_token.type == TT_EOF:
            return None
        node = self.expr()
        if self.current_token.type != TT_EOF:
            raise CalcError(f"Invalid syntax: Extra tokens after expression starting with {repr(self.current_token)}")
        return node
    
    def starts_factor(self, token):
        return token and token.type in (TT_NUMBER, TT_IDENTIFIER, TT_LPAREN)

    def factor(self):
        token = self.current_token
        if token.type == TT_PLUS:
            self.advance()
            return UnaryOpNode(token, self.factor())
        elif token.type == TT_MINUS:
            self.advance()
            return UnaryOpNode(token, self.factor())
        elif token.type == TT_NUMBER:
            self.advance()
            node = NumberNode(token)
        elif token.type == TT_LPAREN:
            self.advance()
            expr = self.expr()
            if self.current_token.type == TT_RPAREN:
                self.advance()
                node = expr
            else:
                raise CalcError("Invalid syntax: Expected ')'")
        elif token.type == TT_IDENTIFIER:
            identifier_token = token
            self.advance()
            if self.current_token.type == TT_LPAREN:
                self.advance()
                args = []
                if self.current_token.type != TT_RPAREN:
                    args.append(self.expr())
                    while self.current_token.type == TT_COMMA:
                        self.advance()
                        args.append(self.expr())
                if self.current_token.type == TT_RPAREN:
                    self.advance()
                    node = FunctionCallNode(identifier_token, args)
                else:
                    raise CalcError(f"Invalid syntax: Expected ')' for function call")
            else:
                node = ConstantNode(identifier_token)
        else:
            raise CalcError(f"Invalid syntax: Expected number, identifier, or '(' but got {token.type}")
        
        while self.current_token.type == TT_FACT:
            op_token = self.current_token
            self.advance()
            node = PostfixOpNode(node, op_token)

        return node

    def power(self):
        left = self.factor()
        while self.current_token.type == TT_POWER:
            op_token = self.current_token
            self.advance()
            right = self.power()
            left = BinOpNode(left, op_token, right)
        return left

    def term(self):
        left = self.power()
        while True:
            if self.current_token.type in (TT_MULTIPLY, TT_DIVIDE, TT_MODULO):
                op_token = self.current_token
                self.advance()
                right = self.power()
                left = BinOpNode(left, op_token, right)
            elif self.starts_factor(self.current_token):
                right = self.power()
                left = BinOpNode(left, Token(TT_MULTIPLY, '*'), right)
            else:
                break
        return left

    def expr(self):
        left = self.term()
        while self.current_token.type in (TT_PLUS, TT_MINUS):
            op_token = self.current_token
            self.advance()
            right = self.term()
            left = BinOpNode(left, op_token, right)
        return left

# --- Interpreter (Evaluator) ---
class Interpreter:
    def __init__(self, angle_unit='degrees', ans=0.0):
        self.angle_unit = angle_unit
        self.ans = ans
        self.functions = {
            'sin': self._wrap_trig_func(math.sin),
            'cos': self._wrap_trig_func(math.cos),
            'tan': self._wrap_trig_func(math.tan),
            'asin': self._wrap_inv_trig_func(math.asin),
            'acos': self._wrap_inv_trig_func(math.acos),
            'atan': self._wrap_inv_tan_func(math.atan),
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'asinh': math.asinh,
            'acosh': math.acosh,
            'atanh': math.atanh,
            'log': lambda x: (self._raise_error("log domain: x>0") if x <= 0 else math.log10(x)),
            'ln':  lambda x: (self._raise_error("ln domain: x>0") if x <= 0 else math.log(x)),
            'log_b': self._log_b,
            'sqrt': lambda x: (self._raise_error("sqrt domain: x>=0") if x < 0 else math.sqrt(x)),
            'exp': math.exp,
            'abs': abs,
            'fact': lambda x: (self._raise_error("factorial: n must be a non-negative integer")
                               if not (isinstance(x, (int, float)) and x >= 0 and x == int(x) and math.isfinite(x))
                               else math.factorial(int(x))),
        }
        self.constants = {
            'pi': math.pi,
            'e': math.e,
            'ans': self.ans,
        }

    def _raise_error(self, message):
        raise CalcError(message)

    def _wrap_trig_func(self, func):
        def wrapper(angle_val):
            if self.angle_unit == 'degrees':
                return func(math.radians(angle_val))
            elif self.angle_unit == 'gradians':
                return func(angle_val * math.pi / 200.0)
            return func(angle_val)
        return wrapper

    def _wrap_inv_trig_func(self, func):
        def wrapper(val):
            if not isinstance(val, (int, float)) or abs(val) > 1:
                self._raise_error(f"asin/acos domain: -1 <= x <= 1")
            result_radians = func(val)
            if self.angle_unit == 'degrees':
                return math.degrees(result_radians)
            elif self.angle_unit == 'gradians':
                return result_radians * 200.0 / math.pi
            return result_radians
        return wrapper

    def _wrap_inv_tan_func(self, func):
        def wrapper(val):
            result_radians = func(val)
            if self.angle_unit == 'degrees':
                return math.degrees(result_radians)
            elif self.angle_unit == 'gradians':
                return result_radians * 200.0 / math.pi
            return result_radians
        return wrapper
    
    def _log_b(self, val, base):
        if val <= 0:
            self._raise_error("log_b domain: value > 0")
        if base <= 0 or base == 1:
            self._raise_error("log_b domain: base > 0 and base != 1")
        return math.log(val) / math.log(base)

    def _is_intlike(self, x):
        return isinstance(x, (int, float)) and x == int(x) and math.isfinite(x)
        
    def visit(self, node):
        if isinstance(node, NumberNode):
            return node.value
        elif isinstance(node, BinOpNode):
            return self.visit_bin_op(node)
        elif isinstance(node, UnaryOpNode):
            return self.visit_unary_op(node)
        elif isinstance(node, FunctionCallNode):
            return self.visit_function_call(node)
        elif isinstance(node, ConstantNode):
            return self.visit_constant(node)
        elif isinstance(node, PostfixOpNode):
            return self.visit_postfix_op(node)
        else:
            raise CalcError(f"No visit method for {type(node)}")

    def visit_bin_op(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if node.op_token.type == TT_PLUS:
            return left_val + right_val
        elif node.op_token.type == TT_MINUS:
            return left_val - right_val
        elif node.op_token.type == TT_MULTIPLY:
            return left_val * right_val
        elif node.op_token.type == TT_DIVIDE:
            if right_val == 0:
                self._raise_error("Division by zero")
            return left_val / right_val
        elif node.op_token.type == TT_MODULO:
            if right_val == 0:
                self._raise_error("Modulo by zero")
            if not (self._is_intlike(left_val) and self._is_intlike(right_val)):
                self._raise_error("Modulo operands must be integers.")
            return int(left_val) % int(right_val)
        elif node.op_token.type == TT_POWER:
            # Use _is_intlike to allow integer-valued floats as exponents in real mode
            if left_val < 0 and not self._is_intlike(right_val):
                 self._raise_error("Real mode: base < 0 with non-integer exponent not allowed")
            return left_val ** right_val

    def visit_unary_op(self, node):
        operand_val = self.visit(node.operand)
        if node.op_token.type == TT_MINUS:
            return -operand_val
        elif node.op_token.type == TT_PLUS:
            return operand_val

    def visit_postfix_op(self, node):
        operand_val = self.visit(node.operand)
        if node.op_token.type == TT_FACT:
            return self.functions['fact'](operand_val)
    
    def visit_function_call(self, node):
        func_name = node.function_name
        if func_name not in self.functions:
            self._raise_error(f"Unknown function: {func_name}")

        args_evaluated = [self.visit(arg_node) for arg_node in node.args]
        func = self.functions[func_name]

        if func_name == 'log_b':
            if len(args_evaluated) != 2:
                self._raise_error(f"Function '{func_name}' takes exactly 2 arguments, got {len(args_evaluated)}")
            return func(args_evaluated[0], args_evaluated[1])
        else:
            if len(args_evaluated) != 1:
                self._raise_error(f"Function '{func_name}' takes exactly 1 argument, got {len(args_evaluated)}")
            return func(args_evaluated[0])

    def visit_constant(self, node):
        const_name = node.name
        if const_name in self.constants:
            return self.constants[const_name]
        else:
            raise CalcError(f"Unknown constant: {const_name}")

from efcalc_engine import CalcError, Interpreter, Lexer, Parser


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About EfCalc Pro")
        self.setFixedSize(450, 350)

        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        pane1 = QWidget()
        pane1_layout = QVBoxLayout(pane1)
        pane1_layout.addWidget(QLabel("<b>EfCalc Pro - Version 5.0.0 Development</b>"))
        pane1_layout.addWidget(QLabel("Author: Dr. Eric O. Flores"))
        pane1_layout.addWidget(QLabel("Development started August 9, 2026"))
        pane1_layout.addWidget(QLabel("Email: eoftoro@gmail.com"))
        pane1_layout.addStretch()
        tab_widget.addTab(pane1, "General Info")

        pane3 = QWidget()
        pane3_layout = QVBoxLayout(pane3)
        pane3_layout.addWidget(QLabel("<b>Recent Enhancements:</b>"))
        changes_text = QTextBrowser()
        changes_text.setReadOnly(True)
        changes_text.setHtml("""
            <ul>
                <li>Fixed operator precedence for exponentiation.</li>
                <li>Added robust domain checks for all mathematical functions.</li>
                <li>Scientific notation (e.g., <code>1e3</code>) is now correctly parsed.</li>
                <li>Implicit multiplication (e.g., <code>2pi</code>, <code>3(4+5)</code>) is now handled reliably.</li>
                <li>Implemented postfix factorial <code>5!</code>.</li>
                <li>Refactored button styling to be more robust and theme-compliant.</li>
                <li>Memory operations (<code>M+</code>, <code>M-</code>) now evaluate the current expression.</li>
                <li>The <code>log_b</code> button guides the user to the correct <code>log_b(val, base)</code> syntax.</li>
                <li>The <code>ans</code> variable is a permanent constant storing the last result.</li>
                <li>Improved and standardized error messages.</li>
                <li>Improved real-mode exponent rules: negative bases with integer-like exponents now behave consistently.</li>
                <li>Fixed Undo/Redo integration with the custom undo stack.</li>
            </ul>
        """)
        pane3_layout.addWidget(changes_text)
        tab_widget.addTab(pane3, "Updates")

class ScientificCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('EfCalc Pro')
        self.setGeometry(100, 100, 450, 650)

        self.memory = 0.0
        self.ans = 0.0
        self.alphabet_mode = False
        self.shift_mode = False
        self.is_night_mode = False
        self.angle_unit = 'degrees'
        self.decimal_precision = 8
        self.scientific_notation_enabled = False
        
        self.interpreter = Interpreter(ans=self.ans)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        self.history_display = QTextBrowser()
        self.history_display.setFixedHeight(100)
        self.history_display.setReadOnly(True)
        self.history_display.setOpenExternalLinks(False)
        self.history_display.anchorClicked.connect(self._history_entry_clicked)
        main_layout.addWidget(self.history_display)
        
        self.display = QLineEdit()
        self.display.setFixedHeight(60)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(False)
        self.display.returnPressed.connect(self.calculate_expression)
        main_layout.addWidget(self.display)
        
        self.status_label = QLabel(f"Mode: {self.angle_unit.capitalize()}")
        self.status_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.status_label)
        
        self.button_layout = QGridLayout()
        self.create_calculator_buttons()
        main_layout.addLayout(self.button_layout)
        
        central_widget.setLayout(main_layout)

        self.create_menu_bar()
        self.undo_stack = []
        self.redo_stack = []
        self._push_to_undo_stack(self.display.text())
        self.apply_theme()

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.history_display.clear)
        file_menu.addAction(clear_history_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = menu_bar.addMenu("Edit")
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_text)
        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_text)
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)

        view_menu = menu_bar.addMenu("View")
        toggle_theme_action = QAction("Toggle Day/Night Mode", self)
        toggle_theme_action.triggered.connect(self.toggle_day_night_mode)
        view_menu.addAction(toggle_theme_action)

        angle_mode_submenu = view_menu.addMenu("Angle Mode")
        self.angle_group = QActionGroup(self)

        self.degrees_action = QAction("Degrees", self, checkable=True)
        self.degrees_action.triggered.connect(lambda: self._set_angle_mode('degrees'))
        angle_mode_submenu.addAction(self.degrees_action)
        self.angle_group.addAction(self.degrees_action)

        self.radians_action = QAction("Radians", self, checkable=True)
        self.radians_action.triggered.connect(lambda: self._set_angle_mode('radians'))
        angle_mode_submenu.addAction(self.radians_action)
        self.angle_group.addAction(self.radians_action)

        self.gradians_action = QAction("Gradians", self, checkable=True)
        self.gradians_action.triggered.connect(lambda: self._set_angle_mode('gradians'))
        angle_mode_submenu.addAction(self.gradians_action)
        self.angle_group.addAction(self.gradians_action)

        if self.angle_unit == 'degrees':
            self.degrees_action.setChecked(True)
        elif self.angle_unit == 'radians':
            self.radians_action.setChecked(True)
        elif self.angle_unit == 'gradians':
            self.gradians_action.setChecked(True)

        format_menu = view_menu.addMenu("Output Format")
        self.precision_spinbox = QSpinBox(self)
        self.precision_spinbox.setRange(0, 15)
        self.precision_spinbox.setValue(self.decimal_precision)
        self.precision_spinbox.valueChanged.connect(self.set_decimal_precision)
        precision_action = QWidgetAction(self)
        precision_layout = QHBoxLayout()
        precision_layout.addWidget(QLabel("Decimal Places:"))
        precision_layout.addWidget(self.precision_spinbox)
        precision_widget = QWidget()
        precision_widget.setLayout(precision_layout)
        precision_action.setDefaultWidget(precision_widget)
        format_menu.addAction(precision_action)

        self.toggle_sci_notation_action = QAction("Toggle Scientific Notation", self)
        self.toggle_sci_notation_action.setCheckable(True)
        self.toggle_sci_notation_action.setChecked(self.scientific_notation_enabled)
        self.toggle_sci_notation_action.triggered.connect(self.toggle_scientific_notation)
        format_menu.addAction(self.toggle_sci_notation_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _clear_button_layout(self):
        for i in reversed(range(self.button_layout.count())):
            widget_to_remove = self.button_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

    def create_calculator_buttons(self):
        self._clear_button_layout()
        buttons = {
            '(': (0, 0, "btnLParen"), ')': (0, 1, "btnRParen"), 'CLR': (0, 2, "btnClr"), 'CE': (0, 3, "btnCe"), 'ANS': (0, 4, "btnAns"),
            'sin': (1, 0, "btnSin"), 'cos': (1, 1, "btnCos"), 'tan': (1, 2, "btnTan"), 'asin': (1, 3, "btnAsin"), 'acos': (1, 4, "btnAcos"),
            'sinh': (2, 0, "btnSinh"), 'cosh': (2, 1, "btnCosh"), 'tanh': (2, 2, "btnTanh"), 'asinh': (2, 3, "btnAsinh"), 'acosh': (2, 4, "btnAcosh"),
            'log': (3, 0, "btnLog"), 'ln': (3, 1, "btnLn"), 'log_b': (3, 2, "btnLogb"), 'sqrt': (3, 3, "btnSqrt"), 'fact': (3, 4, "btnFact"),
            'pi': (4, 0, "btnPi"), 'e': (4, 1, "btnE"), 'exp': (4, 2, "btnExp"), 'abs': (4, 3, "btnAbs"), 'Mod': (4, 4, "btnMod"),
            '7': (5, 0, "btn7"), '8': (5, 1, "btn8"), '9': (5, 2, "btn9"), '/': (5, 3, "btnDiv"), 'MR': (5, 4, "btnMr"),
            '4': (6, 0, "btn4"), '5': (6, 1, "btn5"), '6': (6, 2, "btn6"), '*': (6, 3, "btnMul"), 'M+': (6, 4, "btnMplus"),
            '1': (7, 0, "btn1"), '2': (7, 1, "btn2"), '3': (7, 2, "btn3"), '-': (7, 3, "btnSub"), 'M-': (7, 4, "btnMminus"),
            '0': (8, 0, "btn0"), '.': (8, 1, "btnDec"), 'Neg': (8, 2, "btnNeg"), '+': (8, 3, "btnPlus"), '=': (8, 4, "btnEqual"),
            'Alpha': (9, 0, "btnAlpha"), 'Shift': (9, 1, "btnShift"), 'Undo': (9, 2, "btnUndo"), 'Redo': (9, 3, "btnRedo"), 'MC': (9, 4, "btnMc")
        }
        for btn_text, pos in buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            button.setObjectName(pos[2])
            self.button_layout.addWidget(button, pos[0], pos[1])
        self.apply_theme()

    def create_alphabet_buttons(self):
        self._clear_button_layout()
        alphabet_buttons = {}
        row, col = 0, 0
        for i in range(26):
            letter = chr(ord('A') + i) if self.shift_mode else chr(ord('a') + i)
            alphabet_buttons[letter] = (row, col)
            col += 1
            if col > 4:
                col = 0
                row += 1
        for btn_text, pos in alphabet_buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])
        control_buttons = {
            'Calc': (row + 1, 0, "btnCalc"), 'Shift': (row + 1, 1, "btnShift"), 'CLR': (row + 1, 2, "btnClr"), 'CE': (row + 1, 3, "btnCe"),
            'Undo': (row + 2, 0, "btnUndo"), 'Redo': (row + 2, 1, "btnRedo"), '!': (row + 2, 2, "btnFact"),
            '(': (0, 4, "btnLParen"), ')': (1, 4, "btnRParen"), '[': (2, 4, "btnLSq"), ']': (3, 4, "btnRSq"),
            '{': (4, 4, "btnLCurly"), '}': (5, 4, "btnRCurly")
        }
        for btn_text, pos in control_buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.setObjectName(pos[2])
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])
        self.apply_theme()

    def on_button_click(self, text):
        """
        Central dispatcher for button presses.
        Undo/Redo are handled early to avoid polluting the custom undo stack.
        """
        # Handle Undo/Redo FIRST so we don't push/repush states around them
        if text == 'Undo':
            self.undo()
            return
        if text == 'Redo':
            self.redo()
            return

        current_display_text = self.display.text()
        self._push_to_undo_stack(current_display_text)

        try:
            if text == 'CLR':
                self.display.clear()

            elif text == 'CE':
                self.display.setText(current_display_text[:-1])

            elif text == '=':
                self.calculate_expression()

            elif text == 'ANS':
                # FIX: when display only holds last result, replace it with 'ans'
                s = self.display.text().strip()
                formatted_ans = self._format_result(self.ans)
                if s == "" or s == formatted_ans or s == str(self.ans):
                    # Start a fresh expression with 'ans'
                    self.display.setText("ans")
                    self.display.setCursorPosition(len("ans"))
                else:
                    # In the middle of an expression → insert 'ans'
                    self._insert_text("ans")

            elif text in ['M+', 'M-']:
                try:
                    result = self.calculate_expression(set_ans=False)
                    if text == 'M+':
                        self.memory += result
                        self._show_temp_message(f"Mem: {self.memory:.2f}")
                    else:
                        self.memory -= result
                        self._show_temp_message(f"Mem: {self.memory:.2f}")
                except Exception as e:
                    self._show_temp_message(f"Error: {e}")

            elif text == 'MR':
                self._insert_text(self._format_result(self.memory))

            elif text == 'MC':
                self.memory = 0.0
                self._show_temp_message("Memory Cleared")

            elif text == 'Neg':
                # Safer way to handle negative sign
                pos = self.display.cursorPosition()
                s = self.display.text()
                if pos == 0 or (pos > 0 and s[pos - 1] in '+-*/^('):
                    self._insert_text('-')
                else:
                    self._insert_text('*(-1)')

            elif text in ['Alpha', 'Calc']:
                self.toggle_alphabet_mode()

            elif text == 'Shift':
                self.toggle_shift_mode()

            elif text == 'log_b':
                self._insert_text("log_b(,)")
                # Position the cursor between the opening parenthesis and comma.
                self.display.setCursorPosition(self.display.cursorPosition() - 2)

            elif text == 'fact':
                self._insert_text("!")

            elif text in self.interpreter.functions:
                self._insert_text(text + '(')

            elif text in self.interpreter.constants:
                self._insert_text(text)

            elif text == 'Mod':
                self._insert_text('%')

            else:
                self._insert_text(text)

        except Exception as e:
            self.display.setText("Error")
            self._show_temp_message(f"Error: {e}", duration=3000)

        finally:
            # Only push if the text actually changed
            if self.display.text() != current_display_text:
                self._push_to_undo_stack(self.display.text())

    def _insert_text(self, text):
        self.display.insert(text)
        self.display.setFocus()
    
    def _history_entry_clicked(self, url):
        expr = unquote(url.toString())
        self.display.setText(expr)
        self.display.setFocus()
        self._show_temp_message("Loaded from history")

    def _show_temp_message(self, message, duration=1500):
        original_text = self.status_label.text()
        self.status_label.setText(message)
        QTimer.singleShot(duration, lambda: self.status_label.setText(original_text))

    def calculate_expression(self, set_ans=True):
        expression = self.display.text()
        if not expression:
            self._show_temp_message("Enter an expression")
            return

        try:
            lexer = Lexer(expression)
            tokens = lexer.generate_tokens()
            parser = Parser(tokens)
            ast = parser.parse()

            self.interpreter = Interpreter(angle_unit=self.angle_unit, ans=self.ans)
            result = self.interpreter.visit(ast)

            if set_ans:
                self.ans = result
                formatted_result = self._format_result(result)
                safe_href = quote(expression, safe='')
                safe_label = html.escape(f"{expression} = {formatted_result}")
                history_entry = f'<a href="{safe_href}" style="text-decoration:none; color:inherit;">{safe_label}</a>'
                self.display.setText(formatted_result)
                self.history_display.append(history_entry)
                self.history_display.verticalScrollBar().setValue(
                    self.history_display.verticalScrollBar().maximum()
                )
            return result

        except Exception as e:
            self.display.setText("Error")
            self._show_temp_message(f"Calculation Error: {e}", duration=3000)
            raise e

    def toggle_negative(self):
        """
        Legacy negative toggle (currently unused).
        Kept for integrity; the active Neg behavior is in on_button_click('Neg').
        """
        current_text = self.display.text()
        if not current_text:
            self._insert_text('-')
        else:
            self.display.setText(f"-({current_text})")
            
    def toggle_shift_mode(self):
        self.shift_mode = not self.shift_mode
        if self.alphabet_mode:
            self.create_alphabet_buttons()
        self.apply_theme()

    def toggle_alphabet_mode(self):
        self.alphabet_mode = not self.alphabet_mode
        if self.alphabet_mode:
            self.create_alphabet_buttons()
            self._show_temp_message("Alphabet Mode ON")
        else:
            self.create_calculator_buttons()
            self._show_temp_message("Alphabet Mode OFF")
        self.apply_theme()

    def toggle_day_night_mode(self):
        self.is_night_mode = not self.is_night_mode
        self.apply_theme()
        self._show_temp_message(f"Theme: {'Night' if self.is_night_mode else 'Day'} Mode")

    def apply_theme(self):
        is_night = self.is_night_mode
        if is_night:
            p = {
                "bg": "#282c34", "fg": "#abb2bf",
                "disp_bg": "#3e4452", "disp_fg": "#61afef", "disp_border": "#56b6c2",
                "btn_bg": "#4b5263", "btn_fg": "#c678dd", "btn_border": "#61afef",
                "btn_hover": "#5c6370", "btn_press": "#6a7381",
                "eq": "#98c379", "clr": "#e06c75", "alpha": "#56b6c2", "shift": "#61afef",
                "eq_fg": "#282c34"
            }
            stylesheet = f"""
                QMainWindow {{
                    background-color: {p['bg']};
                    color: {p['fg']};
                }}
                QLineEdit {{
                    background-color: {p['disp_bg']};
                    color: {p['disp_fg']};
                    border: 2px solid {p['disp_border']};
                    border-radius: 10px;
                    padding: 5px;
                    font-size: 24pt;
                }}
                QTextBrowser {{
                    background-color: {p['disp_bg']};
                    color: {p['fg']};
                    border: 1px solid {p['disp_border']};
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 10pt;
                }}
                QPushButton {{
                    background-color: {p['btn_bg']};
                    color: {p['btn_fg']};
                    border: 1px solid {p['btn_border']};
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 11pt;
                }}
                QPushButton:hover {{
                    background-color: {p['btn_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {p['btn_press']};
                }}
                #btnEqual {{
                    background-color: {p['eq']};
                    color: {p['eq_fg']};
                    font-weight: bold;
                }}
                #btnClr, #btnCe {{
                    background-color: {p['clr']};
                    color: white;
                }}
                #btnAlpha, #btnCalc {{
                    background-color: {p['alpha']};
                    color: {'#282c34'};
                }}
                #btnShift {{
                    background-color: {p['shift']};
                    color: black;
                }}
                QLabel {{
                    color: {p['fg'] if is_night else 'gray'};
                }}
            """
        else:
            p = {
                "bg": "#f0f0f0", "fg": "black",
                "disp_bg": "#E0FFFF", "disp_fg": "black", "disp_border": "#00BFFF",
                "btn_bg": "#e0e0e0", "btn_fg": "black", "btn_border": "#c0c0c0",
                "btn_hover": "#d0d0d0", "btn_press": "#c0c0c0",
                "eq": "#4CAF50", "clr": "#FF6347",
                "alpha": "lightgreen", "shift": "lightblue",
                "eq_fg": "white"
            }
            stylesheet = f"""
                QMainWindow {{
                    background-color: {p['bg']};
                    color: {p['fg']};
                }}
                QLineEdit {{
                    background-color: {p['disp_bg']};
                    color: {p['disp_fg']};
                    border: 2px solid {p['disp_border']};
                    border-radius: 10px;
                    padding: 5px;
                    font-size: 24pt;
                }}
                QTextBrowser {{
                    background-color: {p['disp_bg']};
                    color: {p['fg']};
                    border: 1px solid {p['disp_border']};
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 10pt;
                }}
                QPushButton {{
                    background-color: {p['btn_bg']};
                    color: {p['btn_fg']};
                    border: 1px solid {p['btn_border']};
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 11pt;
                }}
                QPushButton:hover {{
                    background-color: {p['btn_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {p['btn_press']};
                }}
                #btnEqual {{
                    background-color: {p['eq']};
                    color: {p['eq_fg']};
                    font-weight: bold;
                }}
                #btnClr, #btnCe {{
                    background-color: {p['clr']};
                    color: white;
                }}
                #btnAlpha, #btnCalc {{
                    background-color: {p['alpha']};
                    color: {p['fg']};
                }}
                #btnShift {{
                    background-color: {p['shift']};
                    color: black;
                }}
                QLabel {{
                    color: {p['fg'] if is_night else 'gray'};
                }}
            """
        self.setStyleSheet(stylesheet)
        
        # Highlight Shift in alphabet mode
        for button in self.findChildren(QPushButton):
            if button.objectName() in ["btnShift"] and self.alphabet_mode:
                button.setStyleSheet(
                    "background-color: yellow; color: black;"
                    if self.shift_mode
                    else "background-color: lightblue; color: black;"
                )

    def _set_angle_mode(self, mode):
        self.angle_unit = mode
        self.status_label.setText(f"Mode: {self.angle_unit.capitalize()}")
        self._show_temp_message(f"Angle Mode: {self.angle_unit.capitalize()}")
        self.degrees_action.setChecked(mode == 'degrees')
        self.radians_action.setChecked(mode == 'radians')
        self.gradians_action.setChecked(mode == 'gradians')

    def set_decimal_precision(self, value):
        self.decimal_precision = value
        self._show_temp_message(f"Precision set to {value} decimal places.")
        try:
            current_value = float(self.display.text().replace(',', ''))
            self.display.setText(self._format_result(current_value))
        except (ValueError, TypeError):
            pass

    def toggle_scientific_notation(self, checked):
        self.scientific_notation_enabled = checked
        self._show_temp_message(f"Scientific Notation: {'ON' if checked else 'OFF'}")
        try:
            current_value = float(self.display.text().replace(',', ''))
            self.display.setText(self._format_result(current_value))
        except (ValueError, TypeError):
            pass

    def _format_result(self, value):
        if not isinstance(value, (int, float)):
            return str(value)
        if not math.isfinite(value):
            return "Overflow" if math.isinf(value) else "NaN"
        if self.scientific_notation_enabled:
            return f"{value:.{self.decimal_precision}e}"
        else:
            formatted = f"{value:.{self.decimal_precision}f}"
            if '.' in formatted:
                formatted = formatted.rstrip('0')
                if formatted.endswith('.'):
                    formatted = formatted[:-1]
            if not formatted:
                formatted = "0"
            # Keep the displayed value directly reusable by the expression
            # parser. Thousands separators are intentionally not inserted.
            return formatted

    def _push_to_undo_stack(self, text):
        if not self.undo_stack or self.undo_stack[-1] != text:
            self.undo_stack.append(text)
            self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            self.display.blockSignals(True)
            self.display.setText(self.undo_stack[-1])
            self.display.blockSignals(False)
        else:
            self._show_temp_message("Nothing to undo")

    def redo(self):
        if self.redo_stack:
            redo_state = self.redo_stack.pop()
            self.undo_stack.append(redo_state)
            self.display.blockSignals(True)
            self.display.setText(redo_state)
            self.display.blockSignals(False)
        else:
            self._show_temp_message("Nothing to redo")
            
    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.display.text())
        self._show_temp_message("Copied to clipboard")

    def paste_text(self):
        clipboard = QApplication.clipboard()
        pasted_text = clipboard.text()
        self.display.setText(self.display.text() + pasted_text)
        self._show_temp_message("Pasted from clipboard")

    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec_())
