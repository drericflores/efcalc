
#"""
A Scientific Calculator
(c) 2024 Eric O. Flores
Version 4.3
GPL3 License Notice PyCalc Pro - A Python-based Scientific Calculator
Copyright (C) 2024 Dr. Eric O. Flores – E-mail: eoftoro@gmail.com

EfCalc Pro is a Python-based scientific calculator application designed for enhanced
mathematical computations, featuring a graphical user interface (GUI) built with PyQt5.
It aims to be a powerful tool for numerical evaluation of complex mathematical expressions.
"""
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

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit,
    QGridLayout, QMenuBar, QAction, QMessageBox, QMainWindow, QLabel,
    QDialog, QTabWidget, QTextBrowser, QSpinBox, QHBoxLayout, QWidgetAction,
    QActionGroup
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer

# --- Token Definitions ---
TT_NUMBER = 'NUMBER'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MULTIPLY = 'MULTIPLY'
TT_DIVIDE = 'DIVIDE'
TT_MODULO = 'MODULO'
TT_POWER = 'POWER' # For ^
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_LBRACKET = 'LBRACKET' # New token for [
TT_RBRACKET = 'RBRACKET' # New token for ]
TT_LBRACE = 'LBRACE'     # New token for {
TT_RBRACE = 'RBRACE'     # New token for }
TT_IDENTIFIER = 'IDENTIFIER' # For function names like sin, cos, log
TT_COMMA = 'COMMA' # For log_b(value, base)
TT_EOF = 'EOF' # End of File/Input

class Token:
    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def __repr__(self):
        if self.value:
            return f"Token({self.type}, {self.value})"
        return f"Token({self.type})"

# --- Tokenizer (Lexer) ---
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
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()
        try:
            return Token(TT_NUMBER, float(num_str))
        except ValueError:
            raise Exception(f"Invalid number format: {num_str}")


    def make_identifier(self):
        id_str = ''
        # Allow alphanumeric and underscore for identifiers
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()
        return Token(TT_IDENTIFIER, id_str)

    def generate_tokens(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char.isdigit() or self.current_char == '.':
                tokens.append(self.make_number())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MULTIPLY))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIVIDE))
                self.advance()
            elif self.current_char == '%':
                tokens.append(Token(TT_MODULO))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_POWER))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN))
                self.advance()
            elif self.current_char == '[': # New token recognition for [
                tokens.append(Token(TT_LBRACKET))
                self.advance()
            elif self.current_char == ']': # New token recognition for ]
                tokens.append(Token(TT_RBRACKET))
                self.advance()
            elif self.current_char == '{': # New token recognition for {
                tokens.append(Token(TT_LBRACE))
                self.advance()
            elif self.current_char == '}': # New token recognition for }
                tokens.append(Token(TT_RBRACE))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA))
                self.advance()
            elif self.current_char.isalpha():
                tokens.append(self.make_identifier())
            else:
                raise Exception(f"Illegal character: '{self.current_char}' at position {self.pos}")
        tokens.append(Token(TT_EOF))
        return tokens

# --- AST Nodes ---
class ASTNode:
    pass

class NumberNode(ASTNode):
    def __init__(self, token):
        self.token = token
        self.value = token.value

    def __repr__(self):
        return f"Number({self.value})"

class BinOpNode(ASTNode):
    def __init__(self, left, op_token, right):
        self.left = left
        self.op_token = op_token
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op_token.type} {self.right})"

class UnaryOpNode(ASTNode):
    def __init__(self, op_token, operand):
        self.op_token = op_token
        self.operand = operand

    def __repr__(self):
        return f"({self.op_token.type} {self.operand})"

class FunctionCallNode(ASTNode):
    def __init__(self, identifier_token, args):
        self.identifier_token = identifier_token
        self.function_name = identifier_token.value
        self.args = args

    def __repr__(self):
        return f"Call({self.function_name}, {self.args})"

class ConstantNode(ASTNode):
    def __init__(self, identifier_token):
        self.identifier_token = identifier_token
        self.name = identifier_token.value

    def __repr__(self):
        return f"Constant({self.name})"

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
            raise Exception(f"Invalid syntax: Extra tokens after expression starting with {self.current_token.type}")
        return node

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
            return NumberNode(token)
        elif token.type == TT_LPAREN:
            self.advance()
            expr = self.expr()
            if self.current_token.type == TT_RPAREN:
                self.advance()
                return expr
            else:
                raise Exception("Invalid syntax: Expected ')'")
        elif token.type == TT_LBRACKET: # New parsing rule for [ ]
            self.advance()
            expr = self.expr()
            if self.current_token.type == TT_RBRACKET:
                self.advance()
                return expr
            else:
                raise Exception("Invalid syntax: Expected ']'")
        elif token.type == TT_LBRACE: # New parsing rule for { }
            self.advance()
            expr = self.expr()
            if self.current_token.type == TT_RBRACE:
                self.advance()
                return expr
            else:
                raise Exception("Invalid syntax: Expected '}'")
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
                    return FunctionCallNode(identifier_token, args)
                else:
                    raise Exception("Invalid syntax: Expected ')' for function call")
            else:
                return ConstantNode(identifier_token)
        else:
            raise Exception(f"Invalid syntax: Expected number, identifier, or grouping symbol ('(', '[', '{{') but got {token.type}")

    def term(self):
        left = self.factor()

        # Handle implicit multiplication and standard multiplication/division/modulo
        while True:
            # Explicit multiplication, division, modulo
            if self.current_token.type in (TT_MULTIPLY, TT_DIVIDE, TT_MODULO):
                op_token = self.current_token
                self.advance()
                right = self.factor()
                left = BinOpNode(left, op_token, right)
            # Implicit multiplication for: (number/constant/function_call) followed by (number/identifier/parenthesis/bracket/brace)
            elif (isinstance(left, (NumberNode, ConstantNode, FunctionCallNode)) and
                  self.current_token.type in (TT_NUMBER, TT_IDENTIFIER, TT_LPAREN, TT_LBRACKET, TT_LBRACE)):
                op_token = Token(TT_MULTIPLY, '*') # Create a synthetic multiplication token
                right = self.factor() # The next factor is implicitly multiplied
                left = BinOpNode(left, op_token, right)
            else:
                break # No more term-level operations or implicit multiplications

        return left

    def power(self):
        left = self.term()
        while self.current_token.type == TT_POWER:
            op_token = self.current_token
            self.advance()
            right = self.power()
            left = BinOpNode(left, op_token, right)
        return left

    def expr(self):
        left = self.power()
        while self.current_token.type in (TT_PLUS, TT_MINUS):
            op_token = self.current_token
            self.advance()
            right = self.power()
            left = BinOpNode(left, op_token, right)
        return left

# --- Interpreter (Evaluator) ---
class Interpreter:
    def __init__(self, angle_unit='degrees'):
        self.angle_unit = angle_unit
        self.functions = {
            'sin': self._wrap_trig_func(math.sin),
            'cos': self._wrap_trig_func(math.cos),
            'tan': self._wrap_trig_func(math.tan),
            'asin': self._wrap_inv_trig_func(math.asin),
            'acos': self._wrap_inv_trig_func(math.acos),
            'atan': self._wrap_inv_trig_func(math.atan),
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'asinh': math.asinh,
            'acosh': math.acosh,
            'atanh': math.atanh,
            'log': lambda x: math.log10(x),
            'ln': lambda x: math.log(x),
            'log_b': lambda val, base: math.log(val, base),
            'sqrt': math.sqrt,
            'exp': math.exp,
            'abs': abs,
            'fact': lambda x: math.factorial(int(x)) if x >= 0 and x == int(x) else self._raise_error("Factorial only for non-negative integers")
        }
        self.constants = {
            'pi': math.pi,
            'e': math.e,
        }

    def _raise_error(self, message):
        raise ValueError(message)

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
            result_radians = func(val)
            if self.angle_unit == 'degrees':
                return math.degrees(result_radians)
            elif self.angle_unit == 'gradians':
                return result_radians * 200.0 / math.pi
            return result_radians
        return wrapper

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
        else:
            raise Exception(f"No visit method for {type(node)}")

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
            return left_val % right_val
        elif node.op_token.type == TT_POWER:
            return left_val ** right_val

    def visit_unary_op(self, node):
        operand_val = self.visit(node.operand)
        if node.op_token.type == TT_MINUS:
            return -operand_val
        elif node.op_token.type == TT_PLUS:
            return operand_val

    def visit_function_call(self, node):
        func_name = node.function_name
        if func_name not in self.functions:
            self._raise_error(f"Unknown function: {func_name}")

        args_evaluated = [self.visit(arg_node) for arg_node in node.args]

        if func_name == 'log_b':
            if len(args_evaluated) != 2:
                self._raise_error(f"{func_name}() takes 2 arguments ({len(args_evaluated)} given)")
            return self.functions[func_name](args_evaluated[0], args_evaluated[1])
        else:
            if len(args_evaluated) != 1:
                self._raise_error(f"{func_name}() takes 1 argument ({len(args_evaluated)} given)")
            return self.functions[func_name](args_evaluated[0])

    def visit_constant(self, node):
        const_name = node.name
        if const_name not in self.constants:
            self._raise_error(f"Unknown constant: {const_name}")
        return self.constants[const_name]

# Define a custom About dialog with tabs
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About EfCalc Pro")
        self.setFixedSize(400, 300) # Fixed size for the dialog

        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Pane 1: General Information
        pane1 = QWidget()
        pane1_layout = QVBoxLayout(pane1)
        pane1_layout.addWidget(QLabel("<b>EfCalc Pro - Version 4.3 (Enhanced)</b>"))
        pane1_layout.addWidget(QLabel("Author: Dr. Eric O. Flores"))
        pane1_layout.addWidget(QLabel("Revised July 22, 2025")) # Updated date
        pane1_layout.addWidget(QLabel("Email: eoftoro@gmail.com"))
        pane1_layout.addStretch() # Push content to the top
        tab_widget.addTab(pane1, "General Info")

        # Pane 2: Technologies Used
        pane2 = QWidget()
        pane2_layout = QVBoxLayout(pane2)
        pane2_layout.addWidget(QLabel("<b>Technologies Used:</b>"))
        pane2_layout.addWidget(QLabel("Programming Language: Python"))
        pane2_layout.addWidget(QLabel("GUI Technology: PyQt5"))
        pane2_layout.addStretch()
        tab_widget.addTab(pane2, "Technologies")

        # Pane 3: Changes and Updates
        pane3 = QWidget()
        pane3_layout = QVBoxLayout(pane3)
        pane3_layout.addWidget(QLabel("<b>Recent Enhancements:</b>"))
        changes_text = QTextBrowser() # Using QTextBrowser for formatted text
        changes_text.setReadOnly(True)
        changes_text.setHtml("""
            <ul>
                <li>Enhanced security by avoiding direct <code>eval()</code> for general expressions (now uses custom parser).</li>
                <li>Improved scientific function handling with degrees/radians/gradians toggle.</li>
                <li>More robust memory operations (MR, MC).</li>
                <li>Refined UI/UX with modern styling and day/night theme.</li>
                <li>Added more scientific functions (asin, acos, atan, sinh, cosh, tanh, asinh, acosh, atanh, log_b, fact).</li>
                <li>Improved Undo/Redo functionality with better state tracking.</li>
                <li>Added a calculation history log.</li>
                <li>Implemented configurable decimal precision for results.</li>
                <li>Added toggle for scientific notation in results.</li>
                <li>Added thousands separators for better readability of large numbers.</li>
                <li><b>Angle mode selection now uses a dedicated submenu for Degrees, Radians, and Gradians.</b></li>
                <li><b>Introduced full-fledged expression parser for complex math and implicit multiplication.</b></li>
                <li><b>Added support for square brackets `[]` and curly braces `{}` as grouping symbols.</b></li>
            </ul>
        """)
        pane3_layout.addWidget(changes_text)
        tab_widget.addTab(pane3, "Updates")


class ScientificCalculator(QMainWindow):
    """
    EfCalc Pro: A Python-based Scientific Calculator with enhanced features.
    Features include basic arithmetic, scientific functions, memory operations,
    degrees/radians/gradians toggle, alphabet mode, history log, and a day/night theme.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle('EfCalc Pro')
        self.setGeometry(100, 100, 450, 650) # Adjusted size for history and new buttons

        # Memory and answer storage
        self.memory = 0.0  # Memory stores a single float value
        self.ans = 0.0     # Store the last calculated result
        self.alphabet_mode = False  # Track whether alphabet mode is active
        self.shift_mode = False     # Track whether Shift is active (for uppercase letters)
        self.is_night_mode = False  # Track whether night mode is active
        self.angle_unit = 'degrees' # 'degrees', 'radians', or 'gradians'

        # Output formatting settings
        self.decimal_precision = 8 # Default decimal places
        self.scientific_notation_enabled = False

        # Central widget for the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # History Display
        self.history_display = QTextBrowser()
        self.history_display.setFixedHeight(100)
        self.history_display.setReadOnly(True)
        self.history_display.setStyleSheet("""
            QTextBrowser {
                background-color: #F0F8FF; /* Alice Blue */
                color: #4682B4; /* Steel Blue */
                font-size: 10pt;
                border: 1px solid #ADD8E6; /* Light Blue */
                border-radius: 5px;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.history_display)

        # Display for input/output
        self.display = QLineEdit()
        self.display.setFixedHeight(60) # Slightly taller display
        self.display.setAlignment(Qt.AlignRight) # Align text to the right
        self.display.setReadOnly(True) # Make display read-only for direct user input
        self.display.setStyleSheet("""
            QLineEdit {
                background-color: #E0FFFF; /* Light Cyan */
                color: black;
                font-size: 24pt;
                border: 2px solid #00BFFF; /* Deep Sky Blue */
                border-radius: 10px;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.display)

        # Status label for angle mode and other messages
        self.status_label = QLabel(f"Mode: {self.angle_unit.capitalize()}")
        self.status_label.setAlignment(Qt.AlignRight)
        self.status_label.setStyleSheet("font-size: 10pt; color: gray;")
        main_layout.addWidget(self.status_label)

        # Create the button layout grid and initialize the calculator buttons
        self.button_layout = QGridLayout()
        self.create_calculator_buttons()

        # Add button layout to the main layout
        main_layout.addLayout(self.button_layout)

        # Set the layout for the central widget
        central_widget.setLayout(main_layout)

        # Create the menu bar
        self.create_menu_bar()

        # Track display history for Undo and Redo
        self.undo_stack = []
        self.redo_stack = []
        self._push_to_undo_stack(self.display.text()) # Push initial empty state

        # Apply initial styling
        self.apply_theme()

    def create_menu_bar(self):
        """Creates the application's menu bar with File, Edit, View, and Help menus."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.history_display.clear)
        file_menu.addAction(clear_history_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
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

        # View menu (for Day/Night Mode, Angle Mode, and Output Formatting)
        view_menu = menu_bar.addMenu("View")
        toggle_theme_action = QAction("Toggle Day/Night Mode", self)
        toggle_theme_action.triggered.connect(self.toggle_day_night_mode)
        view_menu.addAction(toggle_theme_action)

        # Angle Mode Submenu (Replaces the single toggle action)
        angle_mode_submenu = view_menu.addMenu("Angle Mode")
        self.angle_group = QActionGroup(self) # Create an action group for exclusive selection

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

        # Set initial checked state based on self.angle_unit
        if self.angle_unit == 'degrees':
            self.degrees_action.setChecked(True)
        elif self.angle_unit == 'radians':
            self.radians_action.setChecked(True)
        elif self.angle_unit == 'gradians':
            self.gradians_action.setChecked(True)

        # Output Formatting Submenu
        format_menu = view_menu.addMenu("Output Format")
        self.precision_spinbox = QSpinBox(self)
        self.precision_spinbox.setRange(0, 15) # 0 to 15 decimal places
        self.precision_spinbox.setValue(self.decimal_precision)
        self.precision_spinbox.valueChanged.connect(self.set_decimal_precision)
        precision_action = QWidgetAction(self) # Use QWidgetAction to embed spinbox
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

        # Help menu
        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _clear_button_layout(self):
        """Helper to clear all widgets from the button layout."""
        for i in reversed(range(self.button_layout.count())):
            widget_to_remove = self.button_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

    def create_calculator_buttons(self):
        """Creates the standard calculator buttons and adds them to the layout."""
        self._clear_button_layout()

        buttons = {
            '(': (0, 0), ')': (0, 1), 'CLR': (0, 2), 'CE': (0, 3), 'ANS': (0, 4),
            'sin': (1, 0), 'cos': (1, 1), 'tan': (1, 2), 'asin': (1, 3), 'acos': (1, 4),
            'sinh': (2, 0), 'cosh': (2, 1), 'tanh': (2, 2), 'asinh': (2, 3), 'acosh': (2, 4),
            'log': (3, 0), 'ln': (3, 1), 'log_b': (3, 2), 'sqrt': (3, 3), 'fact': (3, 4),
            'pi': (4, 0), 'e': (4, 1), 'exp': (4, 2), 'abs': (4, 3), 'Mod': (4, 4),
            '7': (5, 0), '8': (5, 1), '9': (5, 2), '/': (5, 3), 'MR': (5, 4),
            '4': (6, 0), '5': (6, 1), '6': (6, 2), '*': (6, 3), 'M+': (6, 4),
            '1': (7, 0), '2': (7, 1), '3': (7, 2), '-': (7, 3), 'M-': (7, 4),
            '0': (8, 0), '.': (8, 1), 'Neg': (8, 2), '+': (8, 3), '=': (8, 4),
            'Alpha': (9, 0), 'Shift': (9, 1), 'Undo': (9, 2), 'Redo': (9, 3), 'MC': (9, 4)
        }

        for btn_text, pos in buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])

            if btn_text in ['=', 'EXE']:
                button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            elif btn_text in ['CLR', 'CE']:
                button.setStyleSheet("background-color: #FF6347; color: white;")
            elif btn_text == 'Alpha':
                button.setStyleSheet("background-color: lightgreen;")
            else:
                button.setStyleSheet("")

        self.apply_theme()

    def create_alphabet_buttons(self):
        """Creates alphabet buttons (a-z, A-Z depending on shift mode) and adds them to the layout."""
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
            'Calc': (row + 1, 0),
            'Shift': (row + 1, 1),
            'CLR': (row + 1, 2),
            'CE': (row + 1, 3),
            'Undo': (row + 2, 0),
            'Redo': (row + 2, 1),
            '(': (0, 4), ')': (1, 4),
            '[': (2, 4), ']': (3, 4),
            '{': (4, 4), '}': (5, 4)
        }

        for btn_text, pos in control_buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            if btn_text == 'Calc':
                button.setStyleSheet("background-color: lightgreen;")
                button.clicked.connect(lambda ch, text='Alpha': self.on_button_click(text))
            elif btn_text == 'Shift':
                button.setStyleSheet("background-color: lightblue;" if self.shift_mode else "")
                button.clicked.connect(lambda ch, text='Shift': self.on_button_click(text))
            elif btn_text in ['CLR', 'CE']:
                button.setStyleSheet("background-color: #FF6347; color: white;")
                button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            elif btn_text in ['Undo', 'Redo']:
                button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            else:
                button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])

        self.apply_theme()

    def on_button_click(self, text):
        """Handles button clicks and updates the display."""
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
                self.display.setText(current_display_text + self._format_result(self.ans))
            elif text == 'M+':
                try:
                    # Evaluate the entire current expression to get the value to add/subtract
                    lexer = Lexer(current_display_text)
                    tokens = lexer.generate_tokens()
                    parser = Parser(tokens)
                    ast = parser.parse()
                    interpreter = Interpreter(angle_unit=self.angle_unit)
                    value_for_memory = interpreter.visit(ast)
                    self.memory += value_for_memory
                    self._show_temp_message(f"Mem: {self.memory:.2f}")
                    self.display.clear()
                except Exception as e:
                    self._show_temp_message(f"Error for M+: {e}")
            elif text == 'M-':
                try:
                    lexer = Lexer(current_display_text)
                    tokens = lexer.generate_tokens()
                    parser = Parser(tokens)
                    ast = parser.parse()
                    interpreter = Interpreter(angle_unit=self.angle_unit)
                    value_for_memory = interpreter.visit(ast)
                    self.memory -= value_for_memory
                    self._show_temp_message(f"Mem: {self.memory:.2f}")
                    self.display.clear()
                except Exception as e:
                    self._show_temp_message(f"Error for M-: {e}")
            elif text == 'MR':
                self.display.setText(current_display_text + self._format_result(self.memory))
            elif text == 'MC':
                self.memory = 0.0
                self._show_temp_message("Memory Cleared")
            elif text == 'Neg':
                current_text_for_neg = self.display.text()
                # Attempt to find a simple number at the end to negate it
                match = re.search(r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)$', current_text_for_neg)
                if match:
                    number_part = match.group(1)
                    negated_number = str(-float(number_part))
                    self.display.setText(current_text_for_neg[:-len(number_part)] + negated_number)
                else:
                    if current_text_for_neg.startswith('-'):
                        self.display.setText(current_text_for_neg[1:])
                    else:
                        self.display.setText('-' + current_text_for_neg)
            elif text == 'Alpha':
                self.toggle_alphabet_mode()
            elif text == 'Shift':
                self.toggle_shift_mode()
            elif text == 'Undo':
                self.undo()
            elif text == 'Redo':
                self.redo()
            elif text in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                          'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh',
                          'log', 'ln', 'log_b', 'sqrt', 'exp', 'abs', 'fact']:
                self.display.setText(current_display_text + text + '(')
            elif text == 'pi' or text == 'e':
                self.display.setText(current_display_text + text)
            elif text == '^':
                self.display.setText(current_display_text + '^')
            elif text == 'Mod':
                self.display.setText(current_display_text + '%')
            else:
                self.display.setText(current_display_text + text)

        except Exception as e:
            self.display.setText("Error")
            self._show_temp_message(f"Error: {e}", duration=3000)
        finally:
            if self.display.text() != current_display_text:
                self._push_to_undo_stack(self.display.text())

    def _get_current_number_from_display(self):
        """
        Attempts to extract the last number entered into the display for memory operations.
        This is a simple heuristic and might need refinement for complex expressions.
        """
        text = self.display.text()
        match = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$', text)
        if match:
            try:
                return float(match[-1])
            except ValueError:
                return 0.0
        return 0.0

    def _show_temp_message(self, message, duration=1500):
        """Displays a temporary message in the status label."""
        original_text = self.status_label.text()
        self.status_label.setText(message)
        QTimer.singleShot(duration, lambda: self.status_label.setText(original_text))

    def calculate_expression(self):
        """
        Calculates the mathematical expression in the display using the custom
        tokenizer, parser, and interpreter.
        """
        expression = self.display.text()

        if not expression:
            self._show_temp_message("Enter an expression")
            return

        try:
            lexer = Lexer(expression)
            tokens = lexer.generate_tokens()
            parser = Parser(tokens)
            ast = parser.parse()
            interpreter = Interpreter(angle_unit=self.angle_unit)

            result = interpreter.visit(ast)

            self.ans = result
            formatted_result = self._format_result(result)
            self.display.setText(formatted_result)
            self.history_display.append(f"{expression} = {formatted_result}")
            self.history_display.verticalScrollBar().setValue(self.history_display.verticalScrollBar().maximum())

        except (ZeroDivisionError, ValueError, AttributeError, TypeError, IndexError) as e:
            self.display.setText("Error")
            self._show_temp_message(f"Calculation Error: {e}", duration=3000)
        except Exception as e:
            self.display.setText("Error")
            self._show_temp_message(f"Unexpected Error: {e}", duration=3000)

    # The calculate_scientific method is no longer needed as the full parser
    # handles all scientific function evaluations within the main calculate_expression.
    # def calculate_scientific(self, func_name):
    #     pass # This method is now redundant and can be removed or left as a placeholder

    def toggle_negative(self):
        current_text = self.display.text()
        if not current_text:
            return

        if current_text.startswith('-'):
            self.display.setText(current_text[1:])
        else:
            self.display.setText('-' + current_text)

    def toggle_shift_mode(self):
        """Toggle between lowercase and uppercase in alphabet mode."""
        self.shift_mode = not self.shift_mode
        if self.alphabet_mode:
            self.create_alphabet_buttons()
        self.apply_theme()

    def toggle_alphabet_mode(self):
        """Toggles between normal calculator mode and alphabet input mode."""
        self.alphabet_mode = not self.alphabet_mode
        if self.alphabet_mode:
            self.create_alphabet_buttons()
            self._show_temp_message("Alphabet Mode ON")
        else:
            self.create_calculator_buttons()
            self._show_temp_message("Alphabet Mode OFF")
        self.apply_theme()

    def toggle_day_night_mode(self):
        """Toggle between day (light) mode and night (dark) mode."""
        self.is_night_mode = not self.is_night_mode
        self.apply_theme()
        self._show_temp_message(f"Theme: {'Night' if self.is_night_mode else 'Day'} Mode")

    def apply_theme(self):
        """Applies the current theme (day/night) to all widgets."""
        if self.is_night_mode:
            self.setStyleSheet("""
                QMainWindow { background-color: #282c34; color: #abb2bf; }
                QLineEdit {
                    background-color: #3e4452;
                    color: #61afef;
                    border: 2px solid #56b6c2;
                }
                QTextBrowser {
                    background-color: #3e4452;
                    color: #abb2bf;
                    border: 1px solid #56b6c2;
                }
                QPushButton {
                    background-color: #4b5263;
                    color: #c678dd;
                    border: 1px solid #61afef;
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #5c6370;
                }
                QPushButton:pressed {
                    background-color: #6a7381;
                }
                QPushButton[text="="], QPushButton[text="EXE"] {
                    background-color: #98c379;
                    color: #282c34;
                    font-weight: bold;
                }
                QPushButton[text="CLR"], QPushButton[text="CE"] {
                    background-color: #e06c75;
                    color: white;
                }
                QPushButton[text="Alpha"] {
                    background-color: #56b6c2;
                    color: #282c34;
                }
                QPushButton[text="Shift"] {
                    background-color: #61afef;
                    color: #282c34;
                }
                QLabel {
                    color: #abb2bf;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #f0f0f0; color: black; }
                QLineEdit {
                    background-color: #E0FFFF;
                    color: black;
                    border: 2px solid #00BFFF;
                }
                QTextBrowser {
                    background-color: #F0F8FF;
                    color: #4682B4;
                    border: 1px solid #ADD8E6;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: black;
                    border: 1px solid #c0c0c0;
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                }
                QPushButton[text="="], QPushButton[text="EXE"] {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                }
                QPushButton[text="CLR"], QPushButton[text="CE"] {
                    background-color: #FF6347;
                    color: white;
                }
                QPushButton[text="Alpha"] {
                    background-color: lightgreen;
                }
                QPushButton[text="Shift"] {
                    background-color: lightblue;
                }
                QLabel {
                    color: gray;
                }
            """)

        for i in range(self.button_layout.count()):
            button = self.button_layout.itemAt(i).widget()
            if button and button.text() == 'Shift':
                if self.alphabet_mode and self.shift_mode:
                    button.setStyleSheet("background-color: yellow; color: black;")
                elif self.alphabet_mode and not self.shift_mode:
                    button.setStyleSheet("background-color: lightblue; color: black;")
                else:
                    button.setStyleSheet("")

    def _set_angle_mode(self, mode):
        """Sets the angle unit and updates the status label and menu checks."""
        self.angle_unit = mode
        self.status_label.setText(f"Mode: {self.angle_unit.capitalize()}")
        self._show_temp_message(f"Angle Mode: {self.angle_unit.capitalize()}")

        self.degrees_action.setChecked(mode == 'degrees')
        self.radians_action.setChecked(mode == 'radians')
        self.gradians_action.setChecked(mode == 'gradians')

    def set_decimal_precision(self, value):
        """Sets the number of decimal places for result formatting."""
        self.decimal_precision = value
        self._show_temp_message(f"Precision set to {value} decimal places.")
        try:
            current_value = float(self.display.text().replace(',', ''))
            self.display.setText(self._format_result(current_value))
        except ValueError:
            pass

    def toggle_scientific_notation(self, checked):
        """Toggles scientific notation for result formatting."""
        self.scientific_notation_enabled = checked
        self._show_temp_message(f"Scientific Notation: {'ON' if checked else 'OFF'}")
        try:
            current_value = float(self.display.text().replace(',', ''))
            self.display.setText(self._format_result(current_value))
        except ValueError:
            pass

    def _format_result(self, value):
        """Formats a numerical result based on current precision and scientific notation settings."""
        if isinstance(value, (int, float)):
            if self.scientific_notation_enabled:
                formatted = f"{value:.{self.decimal_precision}e}"
            else:
                formatted = f"{value:.{self.decimal_precision}f}"
                if '.' in formatted:
                    formatted = formatted.rstrip('0')
                    if formatted.endswith('.'):
                        formatted = formatted.rstrip('.')
                if not formatted:
                    formatted = "0"

            if not self.scientific_notation_enabled:
                if '.' in formatted:
                    parts = formatted.split('.')
                    whole_part = parts[0]
                    decimal_part = parts[1]
                    try:
                        whole_part_formatted = "{:,}".format(int(whole_part))
                    except ValueError:
                        whole_part_formatted = whole_part
                    formatted = f"{whole_part_formatted}.{decimal_part}"
                else:
                    try:
                        formatted = "{:,}".format(int(value))
                    except ValueError:
                        formatted = str(value)
            return formatted
        return str(value)

    def _push_to_undo_stack(self, text):
        """Pushes the current display text to the undo stack."""
        if not self.undo_stack or self.undo_stack[-1] != text:
            self.undo_stack.append(text)
            self.redo_stack.clear()

    def undo(self):
        """Undoes the last action on the display."""
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            self.display.setText(self.undo_stack[-1])
        elif len(self.undo_stack) == 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            self.display.clear()
        else:
            self._show_temp_message("Nothing to undo")

    def redo(self):
        """Redoes the last undone action on the display."""
        if self.redo_stack:
            redo_state = self.redo_stack.pop()
            self.undo_stack.append(redo_state)
            self.display.setText(redo_state)
        else:
            self._show_temp_message("Nothing to redo")

    def copy_text(self):
        """Copies current display text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.display.text())
        self._show_temp_message("Copied to clipboard")

    def paste_text(self):
        """Pastes text from clipboard to display."""
        clipboard = QApplication.clipboard()
        pasted_text = clipboard.text()
        self.display.setText(self.display.text() + pasted_text)
        self._show_temp_message("Pasted from clipboard")

    def show_about_dialog(self):
        """Displays the 'About' dialog."""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec_())
