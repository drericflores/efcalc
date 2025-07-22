"""
A Scientific Calculator
(c) 2024 Eric O. Flores
GPL3 License Notice PyCalc Pro - A Python-based Scientific Calculator
Copyright (C) 2024 Dr. Eric O. Flores – E-mail: eoftoro@gmail.com

EfCalc Pro is a Python-based scientific calculator application designed for enhanced
mathematical computations, featuring a graphical user interface (GUI) built with PyQt5.
It aims to be a powerful tool for numerical evaluation of complex mathematical expressions.
"""
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
import cmath  # ENHANCEMENT: Use cmath for complex number support
import re

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit,
    QGridLayout, QMenuBar, QAction, QMessageBox, QMainWindow, QLabel,
    QDialog, QTabWidget, QTextBrowser, QSpinBox, QHBoxLayout, QWidgetAction,
    QActionGroup, QSizePolicy, QStackedWidget
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QUrl

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
TT_LPAREN = 'LPAREN'  # For (, [, {
TT_RPAREN = 'RPAREN'  # For ), ], }
TT_IDENTIFIER = 'IDENTIFIER'
TT_ASSIGN = 'ASSIGN'  # For :=
TT_COMMA = 'COMMA'
TT_EOF = 'EOF'

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
# ENHANCEMENT: The Lexer is upgraded to support complex numbers, all bracket types, and assignment.
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
        
        try:
            # Handle imaginary numbers like '5i'
            if self.current_char in ('i', 'j'):
                self.advance()
                if not num_str:  # Handles standalone 'i' or 'j'
                    return Token(TT_NUMBER, 1j, pos_start)
                return Token(TT_NUMBER, complex(0, float(num_str)), pos_start)
            
            if dot_count == 0:
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
            # FIX: Recognize all bracket types
            elif self.current_char in '([{':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char in ')]}':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
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
class ASTNode: pass
class NumberNode(ASTNode):
    def __init__(self, token): self.token = token; self.value = token.value
class BinOpNode(ASTNode):
    def __init__(self, left, op_token, right): self.left = left; self.op_token = op_token; self.right = right
class UnaryOpNode(ASTNode):
    def __init__(self, op_token, operand): self.op_token = op_token; self.operand = operand
class FunctionCallNode(ASTNode):
    def __init__(self, identifier_token, args): self.identifier_token = identifier_token; self.function_name = identifier_token.value; self.args = args
class VarAccessNode(ASTNode):
    def __init__(self, identifier_token): self.identifier_token = identifier_token; self.name = identifier_token.value
class VarAssignNode(ASTNode):
    def __init__(self, identifier_token, value_node): self.identifier_token = identifier_token; self.name = identifier_token.value; self.value_node = value_node

# --- Parser ---
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens; self.token_idx = -1; self.current_token = None; self.advance()
    def advance(self):
        self.token_idx += 1; self.current_token = self.tokens[self.token_idx] if self.token_idx < len(self.tokens) else None
    def parse(self):
        if self.current_token.type == TT_EOF: return None
        node = self.expr()
        if self.current_token.type != TT_EOF:
            raise CalcError(f"Syntax Error: Unexpected token {self.current_token.type} at position {self.current_token.pos_start}")
        return node
    def factor(self):
        token = self.current_token
        if token.type in (TT_PLUS, TT_MINUS): self.advance(); return UnaryOpNode(token, self.factor())
        elif token.type == TT_NUMBER: self.advance(); return NumberNode(token)
        elif token.type == TT_LPAREN:
            self.advance(); expr_node = self.expr()
            if self.current_token.type == TT_RPAREN: self.advance(); return expr_node
            else: raise CalcError(f"Syntax Error: Expected closing bracket at pos {self.current_token.pos_start}")
        elif token.type == TT_IDENTIFIER:
            identifier_token = token; self.advance()
            if self.current_token.type == TT_LPAREN:
                self.advance(); args = []
                if self.current_token.type != TT_RPAREN:
                    args.append(self.expr())
                    while self.current_token.type == TT_COMMA: self.advance(); args.append(self.expr())
                if self.current_token.type == TT_RPAREN: self.advance(); return FunctionCallNode(identifier_token, args)
                else: raise CalcError(f"Syntax Error: Expected ')' or ',' for function at pos {self.current_token.pos_start}")
            else: return VarAccessNode(identifier_token)
        else: raise CalcError(f"Syntax Error: Invalid factor starting with {token.type} at pos {token.pos_start}")
    
    def power(self):
        left = self.factor()
        # FIX: More robust implicit multiplication for functions and parentheses
        # e.g., sin(90)(cos(30)) or 5(5)
        while self.current_token.type in (TT_LPAREN, TT_IDENTIFIER, TT_NUMBER):
            op_token = Token(TT_MULTIPLY, '*', self.current_token.pos_start)
            right = self.factor()
            left = BinOpNode(left, op_token, right)
        
        if self.current_token.type == TT_POWER:
            op_token = self.current_token
            self.advance()
            # Power is right-associative
            right = self.expr() # Use expr to handle chains like 2^3^4
            return BinOpNode(left, op_token, right)
            
        return left

    def term(self):
        left = self.power()
        while self.current_token.type in (TT_MULTIPLY, TT_DIVIDE, TT_MODULO):
            op_token = self.current_token
            self.advance()
            right = self.power()
            left = BinOpNode(left, op_token, right)
        return left

    def expr(self):
        if self.current_token.type == TT_IDENTIFIER and self.token_idx + 1 < len(self.tokens) and self.tokens[self.token_idx + 1].type == TT_ASSIGN:
            var_token = self.current_token; self.advance(); self.advance()
            value_node = self.expr()
            return VarAssignNode(var_token, value_node)
        left = self.term()
        while self.current_token.type in (TT_PLUS, TT_MINUS):
            op_token = self.current_token; self.advance(); right = self.term(); left = BinOpNode(left, op_token, right)
        return left

# --- Interpreter ---
class Interpreter:
    def __init__(self, angle_unit='degrees', symbol_table=None):
        self.angle_unit = angle_unit
        self.symbol_table = symbol_table if symbol_table is not None else {}
        self.functions = {
            'sin': self._wrap_trig_func(cmath.sin), 'cos': self._wrap_trig_func(cmath.cos), 'tan': self._wrap_trig_func(cmath.tan),
            'asin': self._wrap_inv_trig_func(cmath.asin), 'acos': self._wrap_inv_trig_func(cmath.acos), 'atan': self._wrap_inv_trig_func(cmath.atan),
            'sinh': cmath.sinh, 'cosh': cmath.cosh, 'tanh': cmath.tanh,
            'asinh': cmath.asinh, 'acosh': cmath.acosh, 'atanh': cmath.atanh,
            'log': lambda x: cmath.log10(x), 'ln': lambda x: cmath.log(x), 'log_b': lambda val, base: cmath.log(val, base),
            'sqrt': cmath.sqrt, 'exp': cmath.exp, 'abs': abs,
            'fact': lambda x: math.factorial(int(x.real)) if x.imag == 0 and x.real >= 0 and x.real == int(x.real) else self._raise_error("Factorial for non-negative real integers only"),
            'real': lambda z: z.real, 'imag': lambda z: z.imag, 'conj': lambda z: z.conjugate(),
        }
        self.constants = {'pi': math.pi, 'e': math.e, 'i': 1j, 'j': 1j}
    def _raise_error(self, message): raise CalcError(message)
    def _wrap_trig_func(self, func):
        def wrapper(angle_val):
            if isinstance(angle_val, complex) or self.angle_unit == 'radians': return func(angle_val)
            if self.angle_unit == 'degrees': return func(math.radians(angle_val))
            elif self.angle_unit == 'gradians': return func(angle_val * math.pi / 200.0)
        return wrapper
    def _wrap_inv_trig_func(self, func):
        def wrapper(val):
            result_radians = func(val)
            if isinstance(result_radians, complex) or self.angle_unit == 'radians': return result_radians
            if self.angle_unit == 'degrees': return math.degrees(result_radians)
            elif self.angle_unit == 'gradians': return result_radians * 200.0 / math.pi
        return wrapper
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'; method = getattr(self, method_name, self.no_visit_method); return method(node)
    def no_visit_method(self, node): self._raise_error(f"No visit method for {type(node).__name__}")
    def visit_NumberNode(self, node): return node.value
    def visit_BinOpNode(self, node):
        left_val = self.visit(node.left); right_val = self.visit(node.right)
        try:
            if node.op_token.type == TT_PLUS: return left_val + right_val
            elif node.op_token.type == TT_MINUS: return left_val - right_val
            elif node.op_token.type == TT_MULTIPLY: return left_val * right_val
            elif node.op_token.type == TT_DIVIDE:
                if right_val == 0: self._raise_error("Division by zero")
                return left_val / right_val
            elif node.op_token.type == TT_MODULO:
                if right_val == 0: self._raise_error("Modulo by zero")
                return left_val % right_val
            elif node.op_token.type == TT_POWER: return left_val ** right_val
        except (ZeroDivisionError, TypeError) as e: self._raise_error(str(e))
    def visit_UnaryOpNode(self, node):
        operand_val = self.visit(node.operand)
        if node.op_token.type == TT_MINUS: return -operand_val
        elif node.op_token.type == TT_PLUS: return +operand_val
    def visit_FunctionCallNode(self, node):
        func_name = node.function_name
        if func_name not in self.functions: self._raise_error(f"Unknown function: {func_name}")
        args_evaluated = [self.visit(arg_node) for arg_node in node.args]; func = self.functions[func_name]
        try: return func(*args_evaluated)
        except TypeError: self._raise_error(f"Wrong number of arguments for {func_name}")
        except Exception as e: self._raise_error(f"Error in function {func_name}: {e}")
    def visit_VarAccessNode(self, node):
        var_name = node.name
        if var_name in self.constants: return self.constants[var_name]
        elif var_name in self.symbol_table: return self.symbol_table[var_name]
        else: self._raise_error(f"Unknown variable or constant: '{var_name}'")
    def visit_VarAssignNode(self, node):
        var_name = node.name
        if var_name in self.constants or var_name in self.functions: self._raise_error(f"Cannot assign to built-in name: {var_name}")
        value = self.visit(node.value_node); self.symbol_table[var_name] = value; return value

# --- About Dialog and Main GUI Window ---
# The rest of the GUI code is largely the same, but with enhancements integrated.
# I will not repeat the class definition for AboutDialog as it is unchanged.

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
        pane1_layout.addWidget(QLabel("<b>EfCalc Pro - Version 6.0 (Stable)</b>"))
        pane1_layout.addWidget(QLabel("Author: Dr. Eric O. Flores"))
        pane1_layout.addWidget(QLabel("Revised July 22, 2025"))
        pane1_layout.addWidget(QLabel("Email: eoftoro@gmail.com"))
        pane1_layout.addStretch()
        tab_widget.addTab(pane1, "General Info")
        pane3 = QWidget()
        pane3_layout = QVBoxLayout(pane3)
        pane3_layout.addWidget(QLabel("<b>Enhancements in this Version:</b>"))
        changes_text = QTextBrowser()
        changes_text.setReadOnly(True)
        changes_text.setHtml("""
            <ul>
                <li><b>Parser Fixed:</b> Correctly handles complex implicit multiplication like <code>5(4+3)</code> and <code>sin(pi)(cos(0))</code>.</li>
                <li><b>Complex Math Enabled:</b> Full support for <code>cmath</code> functions. <code>sqrt(-1)</code> now works correctly.</li>
                <li><b>All Brackets Supported:</b> <code>()</code>, <code>[]</code>, and <code>{}</code> can be used interchangeably for grouping.</li>
                <li>User-defined variables (e.g., <code>x := 5</code>) are supported.</li>
                <li>Keyboard input is enabled.</li>
                <li>The UI is responsive and resizable.</li>
                <li>Memory functions (M+, M-) correctly evaluate the current expression.</li>
            </ul>
        """)
        pane3_layout.addWidget(changes_text)
        tab_widget.addTab(pane3, "Enhancements")


class ScientificCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('EfCalc Pro'); self.resize(500, 720)
        self.memory = 0.0; self.ans = 0.0; self.symbol_table = {}; self.alphabet_mode = False; self.shift_mode = False; self.is_night_mode = False; self.angle_unit = 'degrees'; self.decimal_precision = 8; self.scientific_notation_enabled = False
        self.interpreter = Interpreter()

        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        self.history_display = QTextBrowser(); self.history_display.setFixedHeight(120); self.history_display.setReadOnly(True); self.history_display.setOpenExternalLinks(False); self.history_display.anchorClicked.connect(self._history_entry_clicked); main_layout.addWidget(self.history_display)
        self.display = QLineEdit(); self.display.setFixedHeight(60); self.display.setAlignment(Qt.AlignRight); self.display.setReadOnly(False); self.display.returnPressed.connect(self.calculate_expression); self.display.textChanged.connect(self._push_to_undo_stack_on_change); main_layout.addWidget(self.display)
        self.status_label = QLabel(f"Mode: {self.angle_unit.capitalize()}"); self.status_label.setAlignment(Qt.AlignRight); main_layout.addWidget(self.status_label)
        self.stacked_widget = QStackedWidget(); self.calculator_page = QWidget(); self.alphabet_page = QWidget(); self.button_layout = QGridLayout(self.calculator_page); self.alphabet_layout = QGridLayout(self.alphabet_page); self.stacked_widget.addWidget(self.calculator_page); self.stacked_widget.addWidget(self.alphabet_page)
        self.create_calculator_buttons(); self.create_alphabet_buttons()
        main_layout.addWidget(self.stacked_widget)
        central_widget.setLayout(main_layout)
        self.create_menu_bar()
        self.undo_stack = []; self.redo_stack = []; self._push_to_undo_stack(self.display.text())
        self.apply_theme()

    def create_menu_bar(self):
        menu_bar = self.menuBar(); file_menu = menu_bar.addMenu("File")
        clear_history_action = QAction("Clear History", self); clear_history_action.triggered.connect(self.history_display.clear); file_menu.addAction(clear_history_action)
        clear_vars_action = QAction("Clear All Variables", self); clear_vars_action.triggered.connect(self.clear_variables); file_menu.addAction(clear_vars_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self); quit_action.triggered.connect(self.close); file_menu.addAction(quit_action)
        edit_menu = menu_bar.addMenu("Edit")
        copy_action = QAction("Copy", self); copy_action.setShortcut(QKeySequence.Copy); copy_action.triggered.connect(self.copy_text); edit_menu.addAction(copy_action)
        paste_action = QAction("Paste", self); paste_action.setShortcut(QKeySequence.Paste); paste_action.triggered.connect(self.paste_text); edit_menu.addAction(paste_action)
        undo_action = QAction("Undo", self); undo_action.setShortcut(QKeySequence.Undo); undo_action.triggered.connect(self.undo); edit_menu.addAction(undo_action)
        redo_action = QAction("Redo", self); redo_action.setShortcut(QKeySequence.Redo); redo_action.triggered.connect(self.redo); edit_menu.addAction(redo_action)
        view_menu = menu_bar.addMenu("View")
        toggle_theme_action = QAction("Toggle Day/Night Mode", self); toggle_theme_action.triggered.connect(self.toggle_day_night_mode); view_menu.addAction(toggle_theme_action)
        angle_mode_submenu = view_menu.addMenu("Angle Mode"); self.angle_group = QActionGroup(self)
        self.degrees_action = QAction("Degrees", self, checkable=True); self.degrees_action.triggered.connect(lambda: self._set_angle_mode('degrees')); self.angle_group.addAction(self.degrees_action); angle_mode_submenu.addAction(self.degrees_action)
        self.radians_action = QAction("Radians", self, checkable=True); self.radians_action.triggered.connect(lambda: self._set_angle_mode('radians')); self.angle_group.addAction(self.radians_action); angle_mode_submenu.addAction(self.radians_action)
        self.gradians_action = QAction("Gradians", self, checkable=True); self.gradians_action.triggered.connect(lambda: self._set_angle_mode('gradians')); self.angle_group.addAction(self.gradians_action); angle_mode_submenu.addAction(self.gradians_action)
        self.degrees_action.setChecked(True)
        format_menu = view_menu.addMenu("Output Format")
        self.precision_spinbox = QSpinBox(self); self.precision_spinbox.setRange(0, 15); self.precision_spinbox.setValue(self.decimal_precision); self.precision_spinbox.valueChanged.connect(self.set_decimal_precision)
        precision_action = QWidgetAction(self); precision_layout = QHBoxLayout(); precision_layout.addWidget(QLabel("Decimal Places:")); precision_layout.addWidget(self.precision_spinbox); precision_widget = QWidget(); precision_widget.setLayout(precision_layout); precision_action.setDefaultWidget(precision_widget); format_menu.addAction(precision_action)
        self.toggle_sci_notation_action = QAction("Toggle Scientific Notation", self, checkable=True); self.toggle_sci_notation_action.setChecked(self.scientific_notation_enabled); self.toggle_sci_notation_action.triggered.connect(self.toggle_scientific_notation); format_menu.addAction(self.toggle_sci_notation_action)
        help_menu = menu_bar.addMenu("Help"); about_action = QAction("About", self); about_action.triggered.connect(self.show_about_dialog); help_menu.addAction(about_action)

    def _create_button(self, text, layout, pos):
        button = QPushButton(text); button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.clicked.connect(lambda ch, t=text: self.on_button_click(t)); layout.addWidget(button, pos[0], pos[1]); return button

    def create_calculator_buttons(self):
        buttons = {
            '(': (0, 0), ')': (0, 1), '[': (0, 2), ']': (0, 3), '{':(0,4), '}':(1,4),
            'sin': (1, 0), 'cos': (1, 1), 'tan': (1, 2), 'ANS': (1, 3), 
            'asin': (2, 0), 'acos': (2, 1), 'atan': (2, 2), 'log_b': (2, 3), 'fact': (2, 4),
            'log': (3, 0), 'ln': (3, 1), 'sqrt': (3, 2), 'abs': (3, 3), 'Mod': (3, 4),
            'pi': (4, 0), 'e': (4, 1), 'i': (4, 2), ':=': (4, 3), '^': (4, 4),
            '7': (5, 0), '8': (5, 1), '9': (5, 2), '/': (5, 3), 'MR': (5, 4),
            '4': (6, 0), '5': (6, 1), '6': (6, 2), '*': (6, 3), 'M+': (6, 4),
            '1': (7, 0), '2': (7, 1), '3': (7, 2), '-': (7, 3), 'M-': (7, 4),
            '0': (8, 0), '.': (8, 1), 'Neg': (8, 2), '+': (8, 3), '=': (8, 4),
            'Alpha': (9, 0), 'CLR':(9,1), 'CE':(9,2),'Undo':(9,3),'Redo':(9,4)
        }
        tooltips = {'log_b': 'Log w/ custom base', 'fact': 'Factorial', ':=': 'Assign variable', 'MR': 'Memory Recall', 'MC': 'Memory Clear', 'M+': 'Add to Memory', 'M-': 'Subtract from Memory', 'ANS': 'Last Answer', 'i': 'Imaginary unit'}
        for btn_text, pos in buttons.items():
            button = self._create_button(btn_text, self.button_layout, pos)
            if btn_text in tooltips: button.setToolTip(tooltips[btn_text])

    def create_alphabet_buttons(self):
        for i in reversed(range(self.alphabet_layout.count())):
            widget = self.alphabet_layout.itemAt(i).widget()
            if widget: widget.deleteLater()
        row, col = 0, 0
        for i in range(26):
            letter = chr(ord('A') + i) if self.shift_mode else chr(ord('a') + i)
            self._create_button(letter, self.alphabet_layout, (row, col)); col += 1
            if col > 4: col = 0; row += 1
        control_buttons = { 'Calc': (row, 0), 'Shift': (row, 1), 'CLR': (row, 2), 'CE': (row, 3), '_': (row,4)}
        for btn_text, pos in control_buttons.items(): self._create_button(btn_text, self.alphabet_layout, pos)

    def on_button_click(self, text):
        action_map = {'CLR': self.display.clear, 'CE': lambda: self.display.setText(self.display.text()[:-1]), '=': self.calculate_expression, 'ANS': lambda: self._insert_text(self._format_result(self.ans)), 'M+': self.memory_add, 'M-': self.memory_subtract, 'MR': lambda: self._insert_text(self._format_result(self.memory)), 'MC': self.memory_clear, 'Neg': self.toggle_negative, 'Alpha': self.toggle_alphabet_mode, 'Shift': self.toggle_shift_mode, 'Undo': self.undo, 'Redo': self.redo, 'Calc': self.toggle_alphabet_mode}
        if text in action_map: action_map[text]()
        else:
            insert_text = text + '(' if text in self.interpreter.functions else text
            self._insert_text(insert_text)

    def _insert_text(self, text): self.display.insert(text); self.display.setFocus()
    def _evaluate_expression(self, expression):
        if not expression: return None
        self.interpreter = Interpreter(angle_unit=self.angle_unit, symbol_table=self.symbol_table)
        tokens = Lexer(expression).generate_tokens(); ast = Parser(tokens).parse(); return self.interpreter.visit(ast)
    def memory_add(self):
        try:
            value = self._evaluate_expression(self.display.text())
            if isinstance(value, (int, float, complex)): self.memory += value; self._show_temp_message(f"Mem: {self._format_result(self.memory)}")
        except Exception as e: self._show_temp_message(f"M+ Error: {e}", 3000)
    def memory_subtract(self):
        try:
            value = self._evaluate_expression(self.display.text())
            if isinstance(value, (int, float, complex)): self.memory -= value; self._show_temp_message(f"Mem: {self._format_result(self.memory)}")
        except Exception as e: self._show_temp_message(f"M- Error: {e}", 3000)
    def memory_clear(self): self.memory = 0.0; self._show_temp_message("Memory Cleared")
    def calculate_expression(self):
        expression = self.display.text()
        if not expression: return
        try:
            result = self._evaluate_expression(expression)
            if result is None: return
            self.ans = result; formatted_result = self._format_result(result)
            history_link_style = "style=\\\"text-decoration:none; color:inherit;\\\""
            clean_expr = expression.replace('"', '&quot;')
            history_entry = f"<a href=\\\"{clean_expr}\\\" {history_link_style}>{expression} = {formatted_result}</a>"
            self.display.setText(formatted_result)
            self.history_display.append(history_entry)
            self.history_display.verticalScrollBar().setValue(self.history_display.verticalScrollBar().maximum())
        except Exception as e: self.display.setText("Error"); self._show_temp_message(f"Error: {e}", duration=4000)
    def toggle_negative(self):
        current_text = self.display.text()
        if not current_text: self._insert_text('-')
        else: self.display.setText(f"-({current_text})")
    def toggle_shift_mode(self): self.shift_mode = not self.shift_mode; self.create_alphabet_buttons(); self.apply_theme()
    def toggle_alphabet_mode(self):
        self.alphabet_mode = not self.alphabet_mode; new_index = 1 if self.alphabet_mode else 0; self.stacked_widget.setCurrentIndex(new_index); self._show_temp_message(f"Alphabet Mode {'ON' if self.alphabet_mode else 'OFF'}")
    def apply_theme(self):
        is_night = self.is_night_mode
        p = {"bg": "#282c34", "fg": "#abb2bf", "disp_bg": "#3e4452", "disp_fg": "#61afef", "disp_border": "#56b6c2", "btn_bg": "#4b5263", "btn_fg": "#c678dd", "btn_border": "#61afef", "btn_hover": "#5c6370", "btn_press": "#6a7381", "eq": "#98c379", "clr": "#e06c75", "alpha": "#56b6c2", "shift": "#61afef", "eq_fg": "#282c34"} if is_night else {"bg": "#f0f0f0", "fg": "black", "disp_bg": "#E0FFFF", "disp_fg": "black", "disp_border": "#00BFFF", "btn_bg": "#e0e0e0", "btn_fg": "black", "btn_border": "#c0c0c0", "btn_hover": "#d0d0d0", "btn_press": "#c0c0c0", "eq": "#4CAF50", "clr": "#FF6347", "alpha": "lightgreen", "shift": "lightblue", "eq_fg": "white"}
        stylesheet = f"""QMainWindow {{ background-color: {p['bg']}; color: {p['fg']}; }} QLineEdit {{ background-color: {p['disp_bg']}; color: {p['disp_fg']}; border: 2px solid {p['disp_border']}; border-radius: 10px; padding: 5px; font-size: 22pt;}} QTextBrowser {{ background-color: {p['disp_bg']}; color: {p['fg']}; border: 1px solid {p['disp_border']}; border-radius: 5px; padding: 5px; font-size: 10pt;}} QPushButton {{ background-color: {p['btn_bg']}; color: {p['btn_fg']}; border: 1px solid {p['btn_border']}; border-radius: 5px; padding: 8px; font-size: 11pt; }} QPushButton:hover {{ background-color: {p['btn_hover']}; }} QPushButton:pressed {{ background-color: {p['btn_press']}; }} QPushButton[text="="] {{ background-color: {p['eq']}; color: {p['eq_fg']}; font-weight: bold; }} QPushButton[text="CLR"], QPushButton[text="CE"] {{ background-color: {p['clr']}; color: white; }} QPushButton[text="Alpha"], QPushButton[text="Calc"] {{ background-color: {p['alpha']}; color: {p['fg'] if p['alpha']=='lightgreen' else '#282c34'}; }} QPushButton[text="Shift"] {{ background-color: {p['shift']}; color: {'black' if p['shift']=='lightblue' else '#282c34'}; }} QLabel {{ color: {p['fg'] if is_night else 'gray'}; }}"""
        self.setStyleSheet(stylesheet)
    def toggle_day_night_mode(self): self.is_night_mode = not self.is_night_mode; self.apply_theme(); self._show_temp_message(f"Theme: {'Night' if self.is_night_mode else 'Day'} Mode")
    def _set_angle_mode(self, mode): self.angle_unit = mode; self.status_label.setText(f"Mode: {mode.capitalize()}"); self._show_temp_message(f"Angle Mode: {mode.capitalize()}"); self.degrees_action.setChecked(mode == 'degrees'); self.radians_action.setChecked(mode == 'radians'); self.gradians_action.setChecked(mode == 'gradians')
    def set_decimal_precision(self, value): self.decimal_precision = value; self._show_temp_message(f"Precision set to {value} decimal places")
    def toggle_scientific_notation(self, checked): self.scientific_notation_enabled = checked; self._show_temp_message(f"Scientific Notation: {'ON' if checked else 'OFF'}")
    def _format_result(self, value):
        if value is None: return ""
        if isinstance(value, complex):
            real = value.real; imag = value.imag
            if abs(real) < 1e-12: real = 0
            if abs(imag) < 1e-12: imag = 0
            if imag == 0: return self._format_result(real)
            if real == 0: return f"{'-' if imag < 0 else ''}{self._format_result(abs(imag))}i"
            return f"{self._format_result(real)} {'-' if imag < 0 else '+'} {self._format_result(abs(imag))}i"
        if isinstance(value, (int, float)):
            if self.scientific_notation_enabled: return f"{value:.{self.decimal_precision}e}"
            else:
                formatted = f"{value:.{self.decimal_precision}f}"
                if '.' in formatted: formatted = formatted.rstrip('0').rstrip('.')
                if not formatted: formatted = "0"
                parts = formatted.split('.'); parts[0] = "{:,}".format(int(parts[0])); return '.'.join(parts)
        return str(value)
    def _push_to_undo_stack_on_change(self, text): self._push_to_undo_stack(text)
    def _push_to_undo_stack(self, text):
        if not self.undo_stack or self.undo_stack[-1] != text: self.undo_stack.append(text); self.redo_stack.clear()
    def undo(self):
        if len(self.undo_stack) > 1: self.redo_stack.append(self.undo_stack.pop()); new_text = self.undo_stack[-1]; self.display.blockSignals(True); self.display.setText(new_text); self.display.blockSignals(False)
        else: self._show_temp_message("Nothing to undo")
    def redo(self):
        if self.redo_stack: new_text = self.redo_stack.pop(); self.undo_stack.append(new_text); self.display.blockSignals(True); self.display.setText(new_text); self.display.blockSignals(False)
        else: self._show_temp_message("Nothing to redo")
    def clear_variables(self): self.symbol_table.clear(); self._show_temp_message("All user variables cleared")
    def _history_entry_clicked(self, url): self.display.setText(url.toString()); self.display.setFocus(); self._show_temp_message("Loaded from history")
    def copy_text(self): QApplication.clipboard().setText(self.display.text()); self._show_temp_message("Copied to clipboard")
    def paste_text(self): self._insert_text(QApplication.clipboard().text()); self._show_temp_message("Pasted from clipboard")
    def show_about_dialog(self): AboutDialog(self).exec_()
    def _show_temp_message(self, message, duration=2000):
        original_text = self.status_label.text(); self.status_label.setText(message); QTimer.singleShot(duration, lambda: self.status_label.setText(original_text))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec_())
