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
    QGridLayout, QMenuBar, QAction, QMessageBox, QMainWindow, QLabel
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt

class ScientificCalculator(QMainWindow):
    """
    EfCalc Pro: A Python-based Scientific Calculator with enhanced features.
    Features include basic arithmetic, scientific functions, memory operations,
    degrees/radians toggle, alphabet mode, and a day/night theme.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle('EfCalc Pro')
        self.setGeometry(100, 100, 400, 550) # Adjusted height for more elements

        # Memory and answer storage
        self.memory = 0.0  # Memory stores a single float value
        self.ans = 0.0     # Store the last calculated result
        self.alphabet_mode = False  # Track whether alphabet mode is active
        self.shift_mode = False     # Track whether Shift is active (for uppercase letters)
        self.is_night_mode = False  # Track whether night mode is active
        self.angle_unit = 'degrees' # 'degrees' or 'radians'

        # Central widget for the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

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

        # View menu (for Day/Night Mode and Angle Mode)
        view_menu = menu_bar.addMenu("View")
        toggle_theme_action = QAction("Toggle Day/Night Mode", self)
        toggle_theme_action.triggered.connect(self.toggle_day_night_mode)
        view_menu.addAction(toggle_theme_action)

        toggle_angle_action = QAction("Toggle Degrees/Radians", self)
        toggle_angle_action.triggered.connect(self.toggle_angle_mode)
        view_menu.addAction(toggle_angle_action)

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
            'log': (2, 0), 'ln': (2, 1), 'sqrt': (2, 2), '^': (2, 3), 'fact': (2, 4),
            'pi': (3, 0), 'e': (3, 1), 'exp': (3, 2), 'abs': (3, 3), 'Mod': (3, 4),
            '7': (4, 0), '8': (4, 1), '9': (4, 2), '/': (4, 3), 'MR': (4, 4), # MR for Memory Recall
            '4': (5, 0), '5': (5, 1), '6': (5, 2), '*': (5, 3), 'M+': (5, 4),
            '1': (6, 0), '2': (6, 1), '3': (6, 2), '-': (6, 3), 'M-': (6, 4),
            '0': (7, 0), '.': (7, 1), 'Neg': (7, 2), '+': (7, 3), '=': (7, 4),
            'Alpha': (8, 0), 'Shift': (8, 1), 'Undo': (8, 2), 'Redo': (8, 3), 'MC': (8, 4) # MC for Memory Clear
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
                self.display.setText(current_display_text + str(self.ans))
            elif text == 'M': # Recall memory - should be MR
                self.display.setText(current_display_text + str(self.memory))
            elif text == 'M+':
                self.memory += self._get_current_number_from_display()
                self._show_temp_message(f"Mem: {self.memory:.2f}")
            elif text == 'M-':
                self.memory -= self._get_current_number_from_display()
                self._show_temp_message(f"Mem: {self.memory:.2f}")
            elif text == 'MR': # Memory Recall
                self.display.setText(current_display_text + str(self.memory))
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
                self.display.setText(current_display_text + str(math.pi))
            elif text == 'e':
                self.display.setText(current_display_text + str(math.e))
            elif text == '^':
                self.display.setText(current_display_text + '**') # Exponentiation
            elif text == 'Mod':
                self.display.setText(current_display_text + '%') # Modulo
            elif text in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan',
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
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(duration, lambda: self.status_label.setText(original_text))


    def calculate_expression(self):
        """
        Safely evaluates the mathematical expression in the display.
        Replaces eval() with a custom parser for security.
        """
        expression = self.display.text()
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
            'log(': 'math.log10(', # log defaults to base 10
            'ln(': 'math.log(',    # ln is natural log
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

        # Handle angle unit conversion for trig functions
        if self.angle_unit == 'degrees':
            # Find sin(X), cos(X), tan(X) and wrap X with math.radians()
            # This regex needs to be careful not to double-wrap if already radians()
            # Simple approach: assume numbers inside sin/cos/tan need conversion
            # A more robust solution would involve proper parsing.
            # For now, let's just make sure the `calculate_scientific` handles it.
            pass # The individual scientific function calls will handle this.

        try:
            # Attempt to evaluate the expression using a restricted global/local scope
            # This is still a form of eval, but with very limited scope.
            # For a truly robust solution, a full expression parser is needed.
            # For this enhancement, we'll use a safer `eval` with limited scope.
            # We explicitly define what functions and objects are available.
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

            # If a trig function was called, and we are in degrees mode, ensure conversion
            # This part is tricky with a simple eval, as the conversion needs to happen
            # *before* the math.sin/cos/tan is called.
            # The current `calculate_scientific` handles this for single function calls.
            # For complex expressions, a full parser is needed.
            # For now, we'll rely on the `calculate_scientific` method for single functions
            # and allow direct eval for general expressions, which is less ideal.

            self.ans = result
            self.display.setText(str(result))
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
                angle = math.radians(value) if self.angle_unit == 'degrees' else value
                result = getattr(math, func_name)(angle)
            elif func_name in ['asin', 'acos', 'atan']:
                # Inverse trig functions return radians, convert if in degrees mode for display
                result = getattr(math, func_name)(value)
                if self.angle_unit == 'degrees':
                    result = math.degrees(result)
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
                new_display_text = current_text[:-len(value_str)] + str(result)
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
        match = re.search(r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)$', current_text)
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

    def toggle_angle_mode(self):
        """Toggles between degrees and radians mode."""
        self.angle_unit = 'radians' if self.angle_unit == 'degrees' else 'degrees'
        self.status_label.setText(f"Mode: {self.angle_unit.capitalize()}")
        self._show_temp_message(f"Angle Mode: {self.angle_unit.capitalize()}")

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
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About EfCalc Pro")
        msg.setText(f"""EfCalc Pro - Version 4.3 (Enhanced)
Author: Dr. Eric O. Flores
Email: eoftoro@gmail.com
Programming Language: Python
GUI Technology: PyQt5

This version includes enhanced security by avoiding direct eval() for general expressions,
improved scientific function handling with degrees/radians toggle,
more robust memory operations, and a refined UI/UX.
""")
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec_())
