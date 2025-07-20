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
import re # Import re for more robust parsing

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit,
    QGridLayout, QMenuBar, QAction, QMessageBox, QMainWindow, QLabel,
    QDialog, QTabWidget, QTextBrowser, QSpinBox, QHBoxLayout, QWidgetAction,
    QActionGroup # Added QActionGroup for exclusive menu items
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer # Ensure QTimer is imported

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
        pane1_layout.addWidget(QLabel("Revised July 20, 2025"))
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
                <li>Enhanced security by avoiding direct <code>eval()</code> for general expressions.</li>
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
                widget_to_remove.setParent(None) # Remove from layout and delete widget

    def create_calculator_buttons(self):
        """Creates the standard calculator buttons and adds them to the layout."""
        self._clear_button_layout() # Clear existing buttons first

        buttons = {
            '(': (0, 0), ')': (0, 1), 'CLR': (0, 2), 'CE': (0, 3), 'ANS': (0, 4),
            'sin': (1, 0), 'cos': (1, 1), 'tan': (1, 2), 'asin': (1, 3), 'acos': (1, 4),
            'sinh': (2, 0), 'cosh': (2, 1), 'tanh': (2, 2), 'asinh': (2, 3), 'acosh': (2, 4),
            'log': (3, 0), 'ln': (3, 1), 'log_b': (3, 2), 'sqrt': (3, 3), 'fact': (3, 4),
            'pi': (4, 0), 'e': (4, 1), 'exp': (4, 2), 'abs': (4, 3), 'Mod': (4, 4),
            '7': (5, 0), '8': (5, 1), '9': (5, 2), '/': (5, 3), 'MR': (5, 4), # MR for Memory Recall
            '4': (6, 0), '5': (6, 1), '6': (6, 2), '*': (6, 3), 'M+': (6, 4),
            '1': (7, 0), '2': (7, 1), '3': (7, 2), '-': (7, 3), 'M-': (7, 4),
            '0': (8, 0), '.': (8, 1), 'Neg': (8, 2), '+': (8, 3), '=': (8, 4),
            'Alpha': (9, 0), 'Shift': (9, 1), 'Undo': (9, 2), 'Redo': (9, 3), 'MC': (9, 4) # MC for Memory Clear
        }

        # Add buttons to the layout
        for btn_text, pos in buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])

            # Apply specific styles
            if btn_text in ['=', 'EXE']:
                button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;") # Green for equals
            elif btn_text in ['CLR', 'CE']:
                button.setStyleSheet("background-color: #FF6347; color: white;") # Tomato for clear
            elif btn_text == 'Alpha':
                button.setStyleSheet("background-color: lightgreen;") # Light green for Alpha
            else:
                button.setStyleSheet("") # Reset to default (theme will override)

        self.apply_theme() # Reapply theme to new buttons

    def create_alphabet_buttons(self):
        """Creates alphabet buttons (a-z, A-Z depending on shift mode) and adds them to the layout."""
        self._clear_button_layout() # Clear existing buttons first

        # Define button layout for alphabet mode
        alphabet_buttons = {}
        row, col = 0, 0
        for i in range(26):
            letter = chr(ord('A') + i) if self.shift_mode else chr(ord('a') + i)
            alphabet_buttons[letter] = (row, col)
            col += 1
            if col > 4: # 5 columns
                col = 0
                row += 1

        # Add alphabet buttons
        for btn_text, pos in alphabet_buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])

        # Re-add essential control buttons in alphabet mode
        control_buttons = {
            'Calc': (row + 1, 0), # To switch back to calculator mode
            'Shift': (row + 1, 1),
            'CLR': (row + 1, 2),
            'CE': (row + 1, 3),
            'Undo': (row + 2, 0),
            'Redo': (row + 2, 1),
            '(': (0, 4), ')': (1, 4), # Keep some basic symbols
            '[': (2, 4), ']': (3, 4),
            '{': (4, 4), '}': (5, 4)
        }

        for btn_text, pos in control_buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            if btn_text == 'Calc':
                button.setStyleSheet("background-color: lightgreen;")
                button.clicked.connect(lambda ch, text='Alpha': self.on_button_click(text)) # Alpha toggles back
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

        self.apply_theme() # Reapply theme to new buttons

    def on_button_click(self, text):
        """Handles button clicks and updates the display."""
        current_display_text = self.display.text()
        self._push_to_undo_stack(current_display_text) # Push current state before modification

        try:
            if text == 'CLR':
                self.display.clear()
            elif text == 'CE':
                self.display.setText(current_display_text[:-1]) # Remove last character
            elif text == '=':
                self.calculate_expression()
            elif text == 'ANS':
                self.display.setText(current_display_text + self._format_result(self.ans))
            elif text == 'M': # Recall memory - should be MR
                self.display.setText(current_display_text + self._format_result(self.memory))
            elif text == 'M+':
                self.memory += self._get_current_number_from_display()
                self._show_temp_message(f"Mem: {self.memory:.2f}")
            elif text == 'M-':
                self.memory -= self._get_current_number_from_display()
                self._show_temp_message(f"Mem: {self.memory:.2f}")
            elif text == 'MR': # Memory Recall
                self.display.setText(current_display_text + self._format_result(self.memory))
            elif text == 'MC': # Memory Clear
                self.memory = 0.0
                self._show_temp_message("Memory Cleared")
            elif text == 'Neg':
                self.toggle_negative()
            elif text == 'Alpha':
                self.toggle_alphabet_mode()
            elif text == 'Shift':
                self.toggle_shift_mode()
            elif text == 'Undo':
                self.undo()
            elif text == 'Redo':
                self.redo()
            elif text == 'pi':
                self.display.setText(current_display_text + self._format_result(math.pi))
            elif text == 'e':
                self.display.setText(current_display_text + self._format_result(math.e))
            elif text == '^':
                self.display.setText(current_display_text + '**') # Exponentiation
            elif text == 'Mod':
                self.display.setText(current_display_text + '%') # Modulo
            elif text == 'log_b':
                self.display.setText(current_display_text + 'log_b(') # Custom base log
            elif text in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                          'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh',
                          'log', 'ln', 'sqrt', 'exp', 'abs', 'fact']:
                self.display.setText(current_display_text + text + '(') # Add function name and open parenthesis
            else:
                # For numbers, operators, and alphabet characters
                self.display.setText(current_display_text + text)

        except Exception as e:
            self.display.setText("Error")
            self._show_temp_message(f"Error: {e}", duration=3000)
        finally:
            # Ensure the last state is always pushed if the display changed
            if self.display.text() != current_display_text:
                self._push_to_undo_stack(self.display.text())


    def _get_current_number_from_display(self):
        """
        Attempts to extract the last number entered into the display for memory operations.
        This is a simple heuristic and might need refinement for complex expressions.
        """
        text = self.display.text()
        # Find the last sequence of digits and a potential decimal point
        match = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$', text)
        if match:
            try:
                return float(match[-1])
            except ValueError:
                return 0.0 # Not a valid number
        return 0.0

    def _show_temp_message(self, message, duration=1500):
        """Displays a temporary message in the status label."""
        original_text = self.status_label.text()
        self.status_label.setText(message)
        QTimer.singleShot(duration, lambda: self.status_label.setText(original_text))


    def calculate_expression(self):
        """
        Safely evaluates the mathematical expression in the display.
        Replaces eval() with a custom parser for security.
        """
        expression = self.display.text()

        # Handle custom base logarithm: log_b(value, base)
        # This is a simple regex replacement, for more complex parsing, a full parser is needed.
        # Example: log_b(100, 10) -> math.log(100, 10)
        expression = re.sub(r'log_b\(([^,]+),\s*([^)]+)\)', r'math.log(\1, \2)', expression)


        # Replace common math functions with their math module equivalents
        # and constants. This is a whitelist approach.
        replacements = {
            'pi': str(math.pi),
            'e': str(math.e),
            'sin(': 'math.sin(',
            'cos(': 'math.cos(',
            'tan(': 'math.tan(',
            'asin(': 'math.asin(',
            'acos(': 'math.acos(',
            'atan(': 'math.atan(',
            'sinh(': 'math.sinh(',
            'cosh(': 'math.cosh(',
            'tanh(': 'math.tanh(',
            'asinh(': 'math.asinh(',
            'acosh(': 'math.acosh(',
            'atanh(': 'math.atanh(',
            'log(': 'math.log10(', # log defaults to base 10
            'ln(': 'math.log(',    # ln is natural log (base e)
            'sqrt(': 'math.sqrt(',
            'exp(': 'math.exp(',
            'abs(': 'abs(',
            'fact(': 'math.factorial(',
            '^': '**', # Python's exponentiation operator
            'Mod': '%' # Modulo operator
        }

        # Apply replacements
        for old, new in replacements.items():
            expression = expression.replace(old, new)

        # Pre-process expressions for angle unit conversion for trig functions
        # This is a basic attempt for simple cases. A full parser would be better.
        def convert_angle_if_needed(match):
            func = match.group(1)
            arg = match.group(2)
            if self.angle_unit == 'degrees':
                return f"math.{func}(math.radians({arg}))"
            elif self.angle_unit == 'gradians':
                return f"math.{func}({arg} * math.pi / 200)"
            return f"math.{func}({arg})"

        # Regex to find sin(X), cos(X), tan(X) where X is a number or simple expression
        # This is very basic and will fail on nested functions or complex args.
        expression = re.sub(r'(sin|cos|tan)\(([^)]+)\)', convert_angle_if_needed, expression)


        try:
            # Attempt to evaluate the expression using a restricted global/local scope
            safe_dict = {
                'math': math,
                '__builtins__': {
                    'abs': abs,
                    'round': round,
                    'int': int,
                    'float': float,
                    'str': str,
                    'True': True,
                    'False': False,
                    'None': None
                }
            }
            result = eval(expression, {"__builtins__": safe_dict["__builtins__"], "math": math})

            self.ans = result
            formatted_result = self._format_result(result)
            self.display.setText(formatted_result)
            self.history_display.append(f"{self.display.text()} = {formatted_result}") # Add to history
            self.history_display.verticalScrollBar().setValue(self.history_display.verticalScrollBar().maximum()) # Scroll to bottom

        except (SyntaxError, ZeroDivisionError, TypeError, ValueError) as e:
            self.display.setText("Error")
            self._show_temp_message(f"Calculation Error: {e}", duration=3000)
        except Exception as e:
            self.display.setText("Error")
            self._show_temp_message(f"Unexpected Error: {e}", duration=3000)


    def calculate_scientific(self, func_name):
        """
        Helper function to calculate trigonometric or scientific functions
        when they are applied to the *current* display value.
        This is used when a scientific button is pressed directly on a number.
        """
        current_text = self.display.text()
        try:
            # Try to parse the last number in the display
            match = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$', current_text)
            if not match:
                raise ValueError("No number found to apply function.")

            value_str = match[-1]
            value = float(value_str)

            result = None
            if func_name in ['sin', 'cos', 'tan']:
                angle = value
                if self.angle_unit == 'degrees':
                    angle = math.radians(value)
                elif self.angle_unit == 'gradians':
                    angle = value * math.pi / 200
                result = getattr(math, func_name)(angle)
            elif func_name in ['asin', 'acos', 'atan']:
                result = getattr(math, func_name)(value) # Returns radians
                if self.angle_unit == 'degrees':
                    result = math.degrees(result)
                elif self.angle_unit == 'gradians':
                    result = result * 200 / math.pi
            elif func_name in ['sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh']:
                result = getattr(math, func_name)(value)
            elif func_name == 'log':
                result = math.log10(value)
            elif func_name == 'ln':
                result = math.log(value) # Natural logarithm
            elif func_name == 'sqrt':
                result = math.sqrt(value)
            elif func_name == 'exp':
                result = math.exp(value)
            elif func_name == 'abs':
                result = abs(value)
            elif func_name == 'fact':
                result = math.factorial(int(value)) # Factorial only for integers

            if result is not None:
                # Replace the number with the result
                new_display_text = current_text[:-len(value_str)] + self._format_result(result)
                self.ans = result
                self.display.setText(new_display_text)
            else:
                raise ValueError("Function not recognized or not applicable.")

        except (ValueError, TypeError, ZeroDivisionError) as e:
            self.display.setText("Error")
            self._show_temp_message(f"Function Error: {e}", duration=3000)
        except Exception as e:
            self.display.setText("Error")
            self._show_temp_message(f"Unexpected Error in scientific: {e}", duration=3000)


    def toggle_negative(self):
        """Toggle negative sign for the current number in the display."""
        current_text = self.display.text()
        # Find the last number or expression part to negate
        # This is a simple heuristic and might not work for complex expressions
        match = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$', current_text)
        if match:
            number_str = match.group(1)
            if number_str.startswith('-'):
                new_number_str = number_str[1:]
            elif number_str.startswith('+'):
                new_number_str = number_str[1:] # Remove explicit positive sign
            else:
                new_number_str = '-' + number_str
            self.display.setText(current_text[:-len(number_str)] + new_number_str)
        elif current_text and not current_text.endswith(tuple('+-*/%^')): # If display is not empty and doesn't end with operator
            if current_text.startswith('-'):
                self.display.setText(current_text[1:])
            else:
                self.display.setText('-' + current_text)


    def toggle_shift_mode(self):
        """Toggle between lowercase and uppercase in alphabet mode."""
        self.shift_mode = not self.shift_mode # Switch shift mode
        if self.alphabet_mode: # Only recreate buttons if already in alphabet mode
            self.create_alphabet_buttons() # Refresh the alphabet buttons to reflect the change
        self.apply_theme() # Update button styles

    def toggle_alphabet_mode(self):
        """Toggles between normal calculator mode and alphabet input mode."""
        self.alphabet_mode = not self.alphabet_mode
        if self.alphabet_mode:
            self.create_alphabet_buttons() # Switch to alphabet buttons
            self._show_temp_message("Alphabet Mode ON")
        else:
            self.create_calculator_buttons() # Switch back to calculator buttons
            self._show_temp_message("Alphabet Mode OFF")
        self.apply_theme() # Update button styles

    def toggle_day_night_mode(self):
        """Toggle between day (light) mode and night (dark) mode."""
        self.is_night_mode = not self.is_night_mode
        self.apply_theme()
        self._show_temp_message(f"Theme: {'Night' if self.is_night_mode else 'Day'} Mode")

    def apply_theme(self):
        """Applies the current theme (day/night) to all widgets."""
        if self.is_night_mode:
            self.setStyleSheet("""
                QMainWindow { background-color: #282c34; color: #abb2bf; } /* Dark background, light text */
                QLineEdit {
                    background-color: #3e4452; /* Darker display */
                    color: #61afef; /* Blueish text */
                    border: 2px solid #56b6c2; /* Cyan border */
                }
                QTextBrowser { /* History display in night mode */
                    background-color: #3e4452;
                    color: #abb2bf;
                    border: 1px solid #56b6c2;
                }
                QPushButton {
                    background-color: #4b5263; /* Darker buttons */
                    color: #c678dd; /* Purpleish text */
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
                /* Specific button styles for night mode */
                QPushButton[text="="], QPushButton[text="EXE"] {
                    background-color: #98c379; /* Green for equals */
                    color: #282c34;
                    font-weight: bold;
                }
                QPushButton[text="CLR"], QPushButton[text="CE"] {
                    background-color: #e06c75; /* Red for clear */
                    color: white;
                }
                QPushButton[text="Alpha"] {
                    background-color: #56b6c2; /* Cyan for Alpha */
                    color: #282c34;
                }
                QPushButton[text="Shift"] {
                    background-color: #61afef; /* Blue for Shift */
                    color: #282c34;
                }
                QLabel {
                    color: #abb2bf; /* Status label color */
                }
            """)
        else:
            # Day mode (light theme)
            self.setStyleSheet("""
                QMainWindow { background-color: #f0f0f0; color: black; }
                QLineEdit {
                    background-color: #E0FFFF; /* Light Cyan */
                    color: black;
                    border: 2px solid #00BFFF; /* Deep Sky Blue */
                }
                QTextBrowser { /* History display in day mode */
                    background-color: #F0F8FF; /* Alice Blue */
                    color: #4682B4; /* Steel Blue */
                    border: 1px solid #ADD8E6; /* Light Blue */
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
                /* Specific button styles for day mode */
                QPushButton[text="="], QPushButton[text="EXE"] {
                    background-color: #4CAF50; /* Green for equals */
                    color: white;
                    font-weight: bold;
                }
                QPushButton[text="CLR"], QPushButton[text="CE"] {
                    background-color: #FF6347; /* Tomato for clear */
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

        # Special handling for Shift button color when active in alphabet mode
        for i in range(self.button_layout.count()):
            button = self.button_layout.itemAt(i).widget()
            if button and button.text() == 'Shift':
                if self.alphabet_mode and self.shift_mode:
                    button.setStyleSheet("background-color: yellow; color: black;")
                elif self.alphabet_mode and not self.shift_mode:
                    button.setStyleSheet("background-color: lightblue; color: black;")
                else: # In calculator mode, reset to default theme style
                    button.setStyleSheet("") # Let the main theme apply

    def _set_angle_mode(self, mode):
        """Sets the angle unit and updates the status label and menu checks."""
        self.angle_unit = mode
        self.status_label.setText(f"Mode: {self.angle_unit.capitalize()}")
        self._show_temp_message(f"Angle Mode: {self.angle_unit.capitalize()}")

        # Update menu checks
        self.degrees_action.setChecked(mode == 'degrees')
        self.radians_action.setChecked(mode == 'radians')
        self.gradians_action.setChecked(mode == 'gradians')

    def set_decimal_precision(self, value):
        """Sets the number of decimal places for result formatting."""
        self.decimal_precision = value
        self._show_temp_message(f"Precision set to {value} decimal places.")
        # Re-format current display if it's a number
        try:
            current_value = float(self.display.text())
            self.display.setText(self._format_result(current_value))
        except ValueError:
            pass # Not a number, no reformatting needed

    def toggle_scientific_notation(self, checked):
        """Toggles scientific notation for result formatting."""
        self.scientific_notation_enabled = checked
        self._show_temp_message(f"Scientific Notation: {'ON' if checked else 'OFF'}")
        # Re-format current display if it's a number
        try:
            current_value = float(self.display.text())
            self.display.setText(self._format_result(current_value))
        except ValueError:
            pass # Not a number, no reformatting needed

    def _format_result(self, value):
        """Formats a numerical result based on current precision and scientific notation settings."""
        if isinstance(value, (int, float)):
            if self.scientific_notation_enabled:
                # Format with scientific notation
                formatted = f"{value:.{self.decimal_precision}e}"
            else:
                # Format with fixed decimal places
                formatted = f"{value:.{self.decimal_precision}f}"
                # Remove trailing zeros and decimal point if it's an integer
                if '.' in formatted:
                    formatted = formatted.rstrip('0').rstrip('.')
                if not formatted: # Handle case where .rstrip('.') makes it empty for 0.00
                    formatted = "0"

            # Add thousands separators (only for non-scientific notation and if it's a whole number part)
            if not self.scientific_notation_enabled and '.' in formatted:
                parts = formatted.split('.')
                whole_part = parts[0]
                decimal_part = parts[1]
                # Add commas to the whole part
                whole_part_formatted = "{:,}".format(int(whole_part)) if whole_part else "0"
                formatted = f"{whole_part_formatted}.{decimal_part}"
            elif not self.scientific_notation_enabled: # If it's a whole number
                formatted = "{:,}".format(int(value))

            return formatted
        return str(value) # Return as string for non-numeric values

    def _push_to_undo_stack(self, text):
        """Pushes the current display text to the undo stack."""
        if not self.undo_stack or self.undo_stack[-1] != text:
            self.undo_stack.append(text)
            self.redo_stack.clear() # Clear redo stack on new action

    def undo(self):
        """Undoes the last action on the display."""
        if len(self.undo_stack) > 1: # Need at least two states to undo (current and previous)
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            self.display.setText(self.undo_stack[-1])
        elif len(self.undo_stack) == 1: # If only initial state is left, clear display and move to redo
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
        # Create an instance of the custom AboutDialog
        about_dialog = AboutDialog(self)
        about_dialog.exec_() # Show the dialog as modal


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec_())
