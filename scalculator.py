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
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout

class ScientificCalculator(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle('Scientific Calculator')
        self.setGeometry(100, 100, 400, 500)

        # Memory and answer storage
        self.memory = 0
        self.ans = 0

        # Main layout
        main_layout = QVBoxLayout()

        # Display for input/output
        self.display = QLineEdit()
        self.display.setFixedHeight(50)
        main_layout.addWidget(self.display)

        # Grid layout for buttons
        button_layout = QGridLayout()

        # Add buttons to the layout (math functions above the number keypad, with grouping symbols)
        buttons = {
            '(': (0, 0), ')': (0, 1), '[': (0, 2), ']': (0, 3), 'CLR': (0, 4),
            '{': (1, 0), '}': (1, 1), 'sin': (1, 2), 'cos': (1, 3), 'tan': (1, 4),
            'log': (2, 0), 'sqrt': (2, 1), 'pi': (2, 2), 'e': (2, 3), '^': (2, 4),
            'exp': (3, 0), 'abs': (3, 1), 'M': (3, 2), 'M+': (3, 3), 'M-': (3, 4),
            '7': (4, 0), '8': (4, 1), '9': (4, 2), '/': (4, 3), 'CE': (4, 4),
            '4': (5, 0), '5': (5, 1), '6': (5, 2), '*': (5, 3), '-': (5, 4),
            '1': (6, 0), '2': (6, 1), '3': (6, 2), '+': (6, 3), 'ANS': (6, 4),
            '0': (7, 0), '.': (7, 1), '=': (7, 2), 'EXE': (7, 3), 'CLR': (7, 4)
        }

        # Loop through the buttons and place them in the grid
        for btn_text, pos in buttons.items():
            button = QPushButton(btn_text)
            button.setFixedSize(60, 60)
            button.clicked.connect(lambda ch, text=btn_text: self.on_button_click(text))
            button_layout.addWidget(button, pos[0], pos[1])

        # Add button layout to the main layout
        main_layout.addLayout(button_layout)

        # Set the main layout for the window
        self.setLayout(main_layout)

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
                self.display.setText(self.display.text() + str(self.ans))  # Use last answer
            elif text == 'M':
                self.memory = float(self.display.text())  # Store to memory
            elif text == 'M+':
                self.memory += float(self.display.text())  # Add to memory
            elif text == 'M-':
                self.memory -= float(self.display.text())  # Subtract from memory
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
                self.display.setText(self.display.text() + str(math.pi))  # Insert pi
            elif text == 'e':
                self.display.setText(self.display.text() + str(math.e))  # Insert e
            elif text == '^':
                self.display.setText(self.display.text() + '**')  # Exponentiation (Python uses **)
            elif text == 'exp':
                self.calculate_scientific(math.exp)  # e^x function
            elif text == 'abs':
                self.calculate_scientific(abs)  # Absolute value
            else:
                current_text = self.display.text()
                self.display.setText(current_text + text)
        except Exception as e:
            self.display.setText("Error")

    def calculate_expression(self):
        try:
            expression = self.display.text()
            result = eval(expression)  # Evaluate the expression (consider using sympy for more safety)
            self.ans = result  # Store result as ANS
            self.display.setText(str(result))
        except Exception as e:
            self.display.setText("Error")

    def calculate_scientific(self, func):
        try:
            value = float(self.display.text())  # Get the value from display
            result = func(math.radians(value)) if func in [math.sin, math.cos, math.tan] else func(value)
            self.ans = result  # Store result as ANS
            self.display.setText(str(result))
        except Exception as e:
            self.display.setText("Error")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec_())

