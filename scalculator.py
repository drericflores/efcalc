#
# GPL3 License Notice
# EfCalc Pro - A Python-based Scientific Calculator
#
# Copyright (C) 2024 Dr. Eric O. Flores – E-mail:  <eoftoro@gmail.com>
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
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout, QMenuBar, QAction, QMessageBox, QMainWindow
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt

class ScientificCalculator(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('EfCalc')
        self.setGeometry(100, 100, 400, 500)

        # Memory and answer storage
        self.memory = 0  # Memory stores a single value
        self.ans = 0     # Store the last calculated result
        self.alphabet_mode = False  # Track whether alphabet mode is active
        self.shift_mode = False     # Track whether Shift is active (for uppercase letters)
        self.is_night_mode = False  # Track whether night mode is active

        # Central widget for the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # Display for input/output
        self.display = QLineEdit()
        self.display.setFixedHeight(50)
        main_layout.addWidget(self.display)

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

    def create_menu_bar(self):
        # Menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_text)
        paste_action = QAction("Paste", self)
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

        # View menu (for Day/Night Mode)
        view_menu = menu_bar.addMenu("View")
        toggle_mode_action = QAction("Toggle Day/Night Mode", self)
        toggle_mode_action.triggered.connect(self.toggle_day_night_mode)
        view_menu.addAction(toggle_mode_action)

        # Help menu
        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def create_calculator_buttons(self):
        """Create the standard calculator buttons and add them to the layout."""
        buttons = {
            '(': (0, 0), ')': (0, 1), '[': (0, 2), ']': (0, 3), 'CLR': (0, 4),
            '{': (1, 0), '}': (1, 1), 'sin': (1, 2), 'cos': (1, 3), 'tan': (1, 4),
            'log': (2, 0), 'sqrt': (2, 1), 'pi': (2, 2), 'e': (2, 3), '^': (2, 4),
            'exp': (3, 0), 'abs': (3, 1), 'Hyp': (3, 2), ',': (3, 3), 'M-': (3, 4),
            '7': (4, 0), '8': (4, 1), '9': (4, 2), '/': (4, 3), 'CE': (4, 4),
            '4': (5, 0), '5': (5, 1), '6': (5, 2), '*': (5, 3), '-': (5, 4),
            '1': (6, 0), '2': (6, 1), '3': (6, 2), '+': (6, 3), 'ANS': (6, 4),
            '0': (7, 0), '.': (7, 1), '=': (7, 2), 'EXE': (7, 3), 'M+': (7, 4),
            'Neg': (8, 0), 'Alpha': (8, 1), 'Undo': (8, 2), 'Redo': (8, 3), 'M': (8, 4)
        }

        # Add buttons to the layout
        for btn_text, pos in buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)

            # Set the Alpha button to be light green
            if btn_text == 'Alpha':
                button.setStyleSheet("background-color: lightgreen")

            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])

    def create_alphabet_buttons(self):
        """Create alphabet buttons (a-g, A-G depending on shift mode) and add them to the layout."""
        if self.shift_mode:
            letters = {
                'A': (1, 0), 'B': (1, 1), 'C': (1, 2), 'D': (1, 3), 'E': (1, 4),
                'F': (2, 0), 'G': (2, 1), 'H': (2, 2), 'I': (2, 3), 'J': (2, 4),
                'K': (3, 0), 'L': (3, 1), 'M': (3, 2), 'N': (3, 3), 'O': (3, 4),
                'P': (4, 0), 'Q': (4, 1), 'R': (4, 2), 'S': (4, 3), 'T': (4, 4),
                'U': (5, 0), 'V': (5, 1), 'W': (5, 2), 'X': (5, 3), 'Y': (5, 4),
                'Z': (6, 0)
            }
        else:
            letters = {
                'a': (1, 0), 'b': (1, 1), 'c': (1, 2), 'd': (1, 3), 'e': (1, 4),
                'f': (2, 0), 'g': (2, 1), 'h': (2, 2), 'i': (2, 3), 'j': (2, 4),
                'k': (3, 0), 'l': (3, 1), 'm': (3, 2), 'n': (3, 3), 'o': (3, 4),
                'p': (4, 0), 'q': (4, 1), 'r': (4, 2), 's': (4, 3), 't': (4, 4),
                'u': (5, 0), 'v': (5, 1), 'w': (5, 2), 'x': (5, 3), 'y': (5, 4),
                'z': (6, 0)
            }

        # Clear existing buttons
        for i in reversed(range(self.button_layout.count())):
            self.button_layout.itemAt(i).widget().setParent(None)

        # Add alphabet buttons
        for btn_text, pos in letters.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])

        # Re-add the Calc, Shift, CLR, and CE buttons in alphabet mode
        calc_button = QPushButton('Calc')  # Change from Alpha to Calc in alphabet mode
        calc_button.setFixedSize(60, 60)
        calc_button.setStyleSheet("background-color: lightgreen")
        calc_button.clicked.connect(lambda ch, text='Alpha': self.on_button_click(text))
        self.button_layout.addWidget(calc_button, 6, 1)

        shift_button = QPushButton('Shift')
        shift_button.setFixedSize(60, 60)
        shift_button.clicked.connect(lambda ch, text='Shift': self.on_button_click(text))
        self.button_layout.addWidget(shift_button, 6, 2)

        clr_button = QPushButton('CLR')
        clr_button.setFixedSize(60, 60)
        clr_button.clicked.connect(lambda ch, text='CLR': self.on_button_click(text))
        self.button_layout.addWidget(clr_button, 6, 3)

        ce_button = QPushButton('CE')
        ce_button.setFixedSize(60, 60)
        ce_button.clicked.connect(lambda ch, text='CE': self.on_button_click(text))
        self.button_layout.addWidget(ce_button, 0, 3)

        # Keep the grouping symbols and move them up
        buttons = {
            '(': (0, 0), ')': (0, 1), '[': (0, 2), ']': (0, 3), '{': (0, 4), '}': (1, 4)
        }

        for btn_text, pos in buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            self.button_layout.addWidget(button, pos[0], pos[1])

    def on_button_click(self, text):
        try:
            if text == 'CLR':
                self.display.clear()
            elif text == 'CE':
                current_text = self.display.text()
                self.display.setText(current_text[:-1])  # Remove last character
            elif text == '=' or text == 'EXE':
                self.calculate_expression()
            elif text == 'ANS':
                self.display.setText(self.display.text() + str(self.ans))
            elif text == 'M':
                self.memory = float(self.display.text())
            elif text == 'M+':
                self.memory += float(self.display.text())
            elif text == 'M-':
                self.memory -= float(self.display.text())
            elif text == 'sin':
                self.calculate_scientific(math.sin)
            elif text == 'cos':
                self.calculate_scientific(math.cos)
            elif text == 'tan':
                self.calculate_scientific(math.tan)
            elif text == 'log':
                self.calculate_scientific(math.log10)
            elif text == 'sqrt':
                self.calculate_scientific(math.sqrt)
            elif text == 'pi':
                self.display.setText(self.display.text() + str(math.pi))
            elif text == 'e':
                self.display.setText(self.display.text() + str(math.e))
            elif text == '^':
                self.display.setText(self.display.text() + '**')  # Exponentiation
            elif text == 'exp':
                self.calculate_scientific(math.exp)
            elif text == 'abs':
                self.calculate_scientific(abs)
            elif text == '[ ]':
                self.display.setText(self.display.text() + '[]')  # Add square brackets
            elif text == '{ }':
                self.display.setText(self.display.text() + '{}')  # Add curly braces
            elif text == 'Neg':
                self.toggle_negative()  # Toggle negative sign
            elif text == 'Alpha':
                self.toggle_alphabet_mode()
            elif text == 'Shift':
                self.toggle_shift_mode()  # Shift key for changing case in alphabet mode
            else:
                current_text = self.display.text()
                self.display.setText(current_text + text)
        except Exception as e:
            self.display.setText("Error")

    def calculate_scientific(self, func):
        """Helper function to calculate trigonometric or scientific functions."""
        try:
            value = float(self.display.text())
            result = func(math.radians(value)) if func in [math.sin, math.cos, math.tan] else func(value)
            self.ans = result  # Store result as ANS
            self.display.setText(str(result))
        except Exception as e:
            self.display.setText("Error")

    def toggle_negative(self):
        """Toggle negative sign for the current number in the display."""
        current_text = self.display.text()
        if current_text.startswith('-'):
            self.display.setText(current_text[1:])  # Remove negative sign
        else:
            self.display.setText('-' + current_text)  # Add negative sign

    def toggle_shift_mode(self):
        """Toggle between lowercase and uppercase in alphabet mode."""
        self.shift_mode = not self.shift_mode  # Switch shift mode
        self.create_alphabet_buttons()  # Refresh the alphabet buttons to reflect the change

    def toggle_alphabet_mode(self):
        # Toggle between normal mode and alphabet mode
        self.alphabet_mode = not self.alphabet_mode
        if self.alphabet_mode:
            self.create_alphabet_buttons()  # Switch to alphabet buttons
        else:
            self.create_calculator_buttons()  # Switch back to calculator buttons

    def toggle_day_night_mode(self):
        """Toggle between day (light) mode and night (dark) mode."""
        if self.is_night_mode:
            # Reverting back to day mode
            self.setStyleSheet("background-color: white; color: black;")
            self.display.setStyleSheet("background-color: white; color: black;")
            # Reset button styles back to day mode
            for i in range(self.button_layout.count()):
                button = self.button_layout.itemAt(i).widget()
                if button.text() == "Alpha":
                    button.setStyleSheet("background-color: lightgreen")  # Keep Alpha green
                else:
                    button.setStyleSheet("")  # Reset other buttons to default
            self.is_night_mode = False
        else:
            # Switching to night mode
            self.setStyleSheet("background-color: black; color: white;")
            self.display.setStyleSheet("background-color: lightgreen; color: black;")
            # Apply light-green border to buttons for night mode
            for i in range(self.button_layout.count()):
                button = self.button_layout.itemAt(i).widget()
                button.setStyleSheet("border: 1px solid lightgreen; color: white;")
            self.is_night_mode = True

    def calculate_expression(self):
        """Calculate the current mathematical expression in the display."""
        try:
            expression = self.display.text()
            result = eval(expression)  # Evaluate the expression (consider using sympy for more safety)
            self.ans = result  # Store result as ANS
            self.display.setText(str(result))
        except Exception as e:
            self.display.setText("Error")

    def track_undo_redo(self, current_text):
        """Track undo and redo functionality."""
        self.undo_stack.append(current_text)
        self.redo_stack.clear()

    def undo(self):
        """Undo the last action."""
        if self.undo_stack:
            current_text = self.undo_stack.pop()
            if self.undo_stack:  # Ensure there's something to undo to
                self.redo_stack.append(current_text)
                self.display.setText(self.undo_stack[-1])

    def redo(self):
        """Redo the last undone action."""
        if self.redo_stack:
            redo_text = self.redo_stack.pop()
            self.undo_stack.append(redo_text)
            self.display.setText(redo_text)

    def copy_text(self):
        # Copy current display text to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.display.text())

    def paste_text(self):
        # Paste text from clipboard to display
        clipboard = QApplication.clipboard()
        self.display.setText(self.display.text() + clipboard.text())

    def show_about_dialog(self):
        # About dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About EfCalc")
        msg.setText(f"""EfCalc - Version 4.3
Author: Dr. Eric O. Flores
Email: eoftoro@gmail.com
Programming Language: Python
GUI Technology: PyQt5""")
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec_())
