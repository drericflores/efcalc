# efcalc
A scientific Calculator
EfCalc Pro - User's Manual

A Basic Scientific Calculator

(c) 2024 Eric O. Flores 

GPL3 License Notice
PyCalc Pro - A Python-based Scientific Calculator

Copyright (C) 2024 Dr. Eric O. Flores – E-mail:  <eoftoro@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

1. Introduction
EfCalc Pro is a fully functional scientific calculator designed to handle both basic arithmetic and advanced scientific operations. With a simple, intuitive interface, it allows users to perform calculations efficiently while offering functionality like trigonometry, logarithms, and memory storage. This calculator is suitable for students, engineers, and anyone who needs a reliable tool for performing mathematical computations.
This manual should help users navigate the features of EfCalc Pro. With support for both basic and advanced operations, this calculator is equipped to handle everyday calculations and more specialized scientific computations.
2. User Interface
The EfCalc Pro interface is composed of the following sections:
    • Display Panel: The top area shows your input and results.
    • Keypad:
        ◦ Number Pad: Buttons for digits (0–9) and the decimal point (.)
        ◦ Arithmetic Operators: +, -, *, /, =
        ◦ Parentheses and Grouping Symbols: (), {}, []
        ◦ Scientific Functions: sin, cos, tan, log, sqrt, exp, etc.
        ◦ Constants: π (pi), e
        ◦ Memory Functions: M, M+, M-
        ◦ Utility Buttons: ANS, CLR, CE, EXE
3. Basic Operations
Performing Basic Arithmetic:
    • Addition (+): Adds two or more numbers. Example: 5 + 3 = 8
    • Subtraction (-): Subtracts one number from another. Example: 10 - 2 = 8
    • Multiplication (*): Multiplies numbers. Example: 6 * 7 = 42
    • Division (/): Divides one number by another. Example: 20 / 4 = 5
Decimal Point (.):
    • Use the decimal point button to enter numbers with fractional parts. Example: 3.14
Equals (=):
    • After entering your expression, press the = button to calculate the result. Alternatively, you can press EXE to evaluate the expression.
4. Scientific Operations
Trigonometric Functions:
    • sin(x): Calculates the sine of angle x (in radians).
    • cos(x): Calculates the cosine of angle x (in radians).
    • tan(x): Calculates the tangent of angle x (in radians).
        ◦ Note: For trigonometric operations, make sure to input angles in radians. You can convert degrees to radians by multiplying by π/180.
Logarithmic Functions:
    • log(x): Calculates the base-10 logarithm of x. Example: log(100) = 2
Square Root:
    • sqrt(x): Calculates the square root of x. Example: sqrt(16) = 4
Exponential Functions:
    • exp(x): Calculates the value of e^x. Example: exp(1) = 2.71828
Power/Exponentiation:
    • ^: Raises a number to a power. Example: 2 ^ 3 = 8 (Note: this is equivalent to 2 ** 3 in Python).
Absolute Value:
    • abs(x): Calculates the absolute value of x. Example: abs(-5) = 5
Constants:
    • π (pi): Inserts the value of π (3.14159) into the display.
    • e: Inserts the value of Euler's constant e (2.71828) into the display.
5. Memory Functions
EfCalc Pro provides memory functionality to store and recall values during calculations.
    • M: Stores the current displayed value in memory.
    • M+: Adds the displayed value to the current memory value.
    • M-: Subtracts the displayed value from the current memory value.
Example of Memory Usage:
    1. Type 5 and press M. The number 5 is stored in memory.
    2. Type 3 and press M+. The memory now stores 5 + 3 = 8.
    3. Type 4 and press M-. The memory now stores 8 - 4 = 4.
6. Special Features
ANS Button:
The ANS button retrieves the last calculated result. This allows you to use the previous answer in a new calculation.
Example:
    1. Calculate 5 + 3 (Result = 8).
    2. Press ANS and then * 2. The result will be 8 * 2 = 16.
Grouping Symbols:
    • Parentheses (): Use for grouping expressions to control the order of operations. Example: (2 + 3) * 4 = 20
    • Square Brackets [] and Curly Braces {}: These work similarly to parentheses but are used for more complex expressions that involve multiple levels of grouping.
Clear Functions:
    • CLR: Clears the entire display.
    • CE: Clears the last character entered.
7. Examples of Usage
    1. Basic Arithmetic:
        ◦ Input: 5 + 3 * 2 =
        ◦ Output: 11 (Multiplication happens before addition).
    2. Using Trigonometric Functions:
        ◦ Input: sin(30 * pi / 180) =
        ◦ Output: 0.5 (Convert degrees to radians using π/180).
    3. Exponential Calculations:
        ◦ Input: exp(1)
        ◦ Output: 2.71828 (This is e^1).
    4. Memory Usage:
        ◦ Step 1: Type 5 and press M. Memory now contains 5.
        ◦ Step 2: Type 4 and press M+. Memory now contains 9.
        ◦ Step 3: Press ANS after calculating a new result to use the stored value.
8. Troubleshooting
    • Error Message: If an invalid operation is performed (e.g., dividing by zero), "Error" will appear on the display. Press CLR to reset the display.
    • Unexpected Results: Ensure you are inputting values correctly, especially when using radians for trigonometric functions.
    • ANS Not Working: Make sure you've performed a previous calculation before pressing ANS.
9. Credits
EfCalc Pro originated as a personal hobby project by Dr. Eric O. Flores, initially developed in C. It was later transformed into Python, utilizing the PyQt5 framework to provide a modern, user-friendly graphical interface. The goal of EfCalc Pro is to offer a versatile and robust tool for both scientific and everyday mathematical calculations, combining power with ease of use.
