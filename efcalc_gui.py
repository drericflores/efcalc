"""Qt6 graphical interface for EfCalc Pro 5.0.0."""

import html
import math
from urllib.parse import quote, unquote

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import (
    QAction, QActionGroup, QCloseEvent, QKeySequence, QShortcut, QTextCursor,
)
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
    QSpinBox, QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
    QWidgetAction,
)

from efcalc_engine import CalcError, Interpreter, Lexer, Parser
from efcalc_program import ProgramError, ProgramInterpreter, ProgramStopped
from efcalc_settings import CalculatorSettings


APP_NAME = "EfCalc Pro"
APP_VERSION = "5.0.0-dev5.1"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumSize(480, 360)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        general = QWidget()
        general_layout = QVBoxLayout(general)
        general_layout.addWidget(QLabel(f"<h2>{APP_NAME} {APP_VERSION}</h2>"))
        general_layout.addWidget(QLabel("Scientific calculator for Linux"))
        general_layout.addWidget(QLabel("Programmed by Dr. Eric O. Flores"))
        general_layout.addWidget(QLabel("Development release: August 2026"))
        general_layout.addWidget(QLabel("License: GPL-3.0-or-later"))
        general_layout.addStretch()
        tabs.addTab(general, "About")

        changes = QTextBrowser()
        changes.setHtml("""
            <h3>Version 5.0.0 modernization</h3>
            <ul>
              <li>Qt6 interface using PyQt6.</li>
              <li>Independent, tested calculation engine.</li>
              <li>Persistent theme and calculation preferences.</li>
              <li>Native keyboard editing, Undo, and Redo.</li>
              <li>Improved history, memory, and error handling.</li>
              <li>Programmable mode with variables, formulas, and .efp files.</li>
              <li>Program symbols shared with the main calculator.</li>
            </ul>
        """)
        tabs.addTab(changes, "Changes")


class ProgramDialog(QDialog):
    SAMPLE_PROGRAM = """# EfCalc Pro program
voltage := 12.5
current := 2
power := voltage * current
if power >= 25
    print(power)
else
    print(0)
end
"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EfCalc Program Editor")
        self.resize(760, 620)
        self.current_path = None
        self.variables = {}
        self.formulas = {}
        self.stop_requested = False
        self._build_interface()

    def _build_interface(self):
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        actions = (
            ("New", self.new_program), ("Open", self.open_program),
            ("Save", self.save_program), ("Save As", self.save_program_as),
            ("Run", self.run_program), ("Stop", self.stop_program),
            ("Clear Output", lambda: self.output.clear()),
        )
        for label, callback in actions:
            button = QPushButton(label)
            button.clicked.connect(callback)
            if label == "Run":
                self.run_button = button
            elif label == "Stop":
                self.stop_button = button
                button.setEnabled(False)
            toolbar.addWidget(button)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Enter an EfCalc program")
        self.editor.setPlainText(self.SAMPLE_PROGRAM)
        self.editor.document().setModified(False)
        self.editor.document().modificationChanged.connect(self._update_title)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Program output")
        self.symbols = QPlainTextEdit()
        self.symbols.setReadOnly(True)
        self.symbols.setPlaceholderText("Variables and formulas")
        splitter.addWidget(self.editor)
        splitter.addWidget(self.output)
        splitter.addWidget(self.symbols)
        splitter.setSizes([360, 140, 120])
        layout.addWidget(splitter)

        self.status = QLabel("Ready | .efp program format")
        layout.addWidget(self.status)
        self._update_title()

    def new_program(self):
        if not self.maybe_save():
            return
        self.editor.clear()
        self.output.clear()
        self.variables.clear()
        self.formulas.clear()
        self.symbols.clear()
        self.current_path = None
        self.editor.document().setModified(False)
        self._update_title()
        self.status.setText("New program")

    def open_program(self):
        if not self.maybe_save():
            return
        path, _selected_filter = QFileDialog.getOpenFileName(
            self, "Open EfCalc Program", "", "EfCalc Programs (*.efp);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as program_file:
                self.editor.setPlainText(program_file.read())
            self.current_path = path
            self.editor.document().setModified(False)
            self._update_title()
            self.status.setText(f"Opened: {path}")
        except OSError as error:
            QMessageBox.critical(self, "Open Failed", str(error))

    def save_program(self):
        if not self.current_path:
            return self.save_program_as()
        return self._write_program(self.current_path)

    def save_program_as(self):
        path, _selected_filter = QFileDialog.getSaveFileName(
            self, "Save EfCalc Program", "program.efp", "EfCalc Programs (*.efp)"
        )
        if not path:
            return False
        if not path.lower().endswith(".efp"):
            path += ".efp"
        if self._write_program(path):
            self.current_path = path
            self._update_title()
            return True
        return False

    def _write_program(self, path):
        try:
            with open(path, "w", encoding="utf-8") as program_file:
                program_file.write(self.editor.toPlainText())
            self.status.setText(f"Saved: {path}")
            self.editor.document().setModified(False)
            self._update_title()
            return True
        except OSError as error:
            QMessageBox.critical(self, "Save Failed", str(error))
            return False

    def run_program(self):
        self.output.clear()
        self.stop_requested = False
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        calculator = self.parent()
        try:
            interpreter = ProgramInterpreter(
                angle_unit=calculator.angle_unit,
                initial_variables=self.variables,
                initial_formulas=self.formulas,
                ans=calculator.ans,
                stop_requested=lambda: self.stop_requested,
                progress_callback=self._program_progress,
            )
            result = interpreter.run(self.editor.toPlainText())
            self.variables = result.variables
            self.formulas = result.formulas
            calculator.ans = result.last_result
            calculator.update_program_symbols(
                self.variables, self.formulas, result.last_result
            )
            if result.output:
                self.output.setPlainText("\n".join(result.output))
            else:
                self.output.setPlainText("Program completed without output.")
            variable_count = len(result.variables)
            formula_count = len(result.formulas)
            self._show_symbols(result)
            self.status.setText(
                f"Completed | {variable_count} variable(s) | "
                f"{formula_count} formula(s)"
            )
        except ProgramError as error:
            self.output.setPlainText(f"ERROR: {error}")
            self.status.setText("Program stopped")
            self._select_error_line(error.line_number)
        except ProgramStopped:
            self.output.appendPlainText("Program stopped by operator.")
            self.status.setText("Program stopped")
        finally:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def stop_program(self):
        self.stop_requested = True
        self.status.setText("Stopping program...")

    def _program_progress(self, line_number):
        self.status.setText(f"Running line {line_number}")
        QApplication.processEvents()

    def _select_error_line(self, line_number):
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _index in range(max(0, line_number - 1)):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _show_symbols(self, result):
        lines = ["VARIABLES"]
        if result.variables:
            for name in sorted(result.variables):
                lines.append(f"{name} = {result.variables[name]}")
        else:
            lines.append("(none)")
        lines.extend(("", "FORMULAS"))
        if result.formulas:
            for name in sorted(result.formulas):
                formula = result.formulas[name]
                parameters = ", ".join(formula.parameters)
                lines.append(f"{name}({parameters}) := {formula.expression}")
        else:
            lines.append("(none)")
        self.symbols.setPlainText("\n".join(lines))

    def _update_title(self, _modified=None):
        name = self.current_path or "Untitled.efp"
        marker = " *" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"EfCalc Program Editor — {name}{marker}")

    def maybe_save(self):
        if not self.editor.document().isModified():
            return True
        response = QMessageBox.warning(
            self,
            "Unsaved Program",
            "The current EfCalc program has unsaved changes.",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if response == QMessageBox.StandardButton.Save:
            return bool(self.save_program())
        if response == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def closeEvent(self, event: QCloseEvent):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()


class ScientificCalculator(QMainWindow):
    BUTTONS = (
        (("(", "insert"), (")", "insert"), ("CLR", "clear"), ("CE", "backspace"), ("ANS", "constant")),
        (("sin", "function"), ("cos", "function"), ("tan", "function"), ("asin", "function"), ("acos", "function")),
        (("atan", "function"), ("sinh", "function"), ("cosh", "function"), ("tanh", "function"), ("sqrt", "function")),
        (("log", "function"), ("ln", "function"), ("log_b", "log_base"), ("exp", "function"), ("!", "insert")),
        (("pi", "constant"), ("e", "constant"), ("abs", "function"), ("%", "insert"), ("MR", "memory_recall")),
        (("7", "insert"), ("8", "insert"), ("9", "insert"), ("/", "insert"), ("M+", "memory_add")),
        (("4", "insert"), ("5", "insert"), ("6", "insert"), ("*", "insert"), ("M-", "memory_subtract")),
        (("1", "insert"), ("2", "insert"), ("3", "insert"), ("-", "insert"), ("MC", "memory_clear")),
        (("0", "insert"), (".", "insert"), ("^", "insert"), ("+", "insert"), ("=", "calculate")),
    )

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings or CalculatorSettings()
        self.angle_unit = self.settings.angle_unit
        self.decimal_precision = self.settings.precision
        self.scientific_notation_enabled = self.settings.scientific_notation
        self.theme = self.settings.theme
        self.memory = 0.0
        self.ans = 0.0
        self.program_variables = {}
        self.program_formulas = {}
        self.alpha_mode = False
        self.shift_mode = False
        self.interpreter = Interpreter(self.angle_unit, self.ans)
        self.program_dialog = None
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._restore_mode_status)

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(470, 680)
        self._build_interface()
        self._build_menus()
        self._build_shortcuts()
        self.apply_theme()
        self._initialize_history()
        geometry = self.settings.window_geometry
        if geometry is not None:
            self.restoreGeometry(geometry)
        self._restore_mode_status()

    def _build_interface(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.history_display = QTextBrowser()
        self.history_display.setObjectName("history")
        self.history_display.setMaximumHeight(120)
        self.history_display.setOpenExternalLinks(False)
        self.history_display.anchorClicked.connect(self._history_link_clicked)
        layout.addWidget(self.history_display)

        self.display = QLineEdit()
        self.display.setObjectName("display")
        self.display.setMinimumHeight(64)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("Enter an expression")
        self.display.returnPressed.connect(self.calculate_expression)
        layout.addWidget(self.display)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.status_label)

        self.button_grid = QGridLayout()
        self.button_grid.setSpacing(6)
        self._show_calculator_buttons()
        layout.addLayout(self.button_grid)

    def _clear_buttons(self):
        while self.button_grid.count():
            item = self.button_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_button(self, label, action, row, column):
        button = QPushButton(label)
        button.setObjectName(self._button_name(label))
        button.setMinimumSize(64, 50)
        button.clicked.connect(
            lambda _checked=False, a=action, value=label: self._dispatch(a, value)
        )
        self.button_grid.addWidget(button, row, column)

    def _show_calculator_buttons(self):
        self._clear_buttons()
        for row, button_row in enumerate(self.BUTTONS):
            for column, (label, action) in enumerate(button_row):
                self._add_button(label, action, row, column)
        control_row = len(self.BUTTONS)
        controls = (
            ("Alpha", "alpha_toggle"), (",", "insert"),
            ("[", "insert"), ("]", "insert"), ("Neg", "negative"),
        )
        for column, (label, action) in enumerate(controls):
            self._add_button(label, action, control_row, column)

    def _show_alpha_buttons(self):
        self._clear_buttons()
        for index in range(26):
            letter = chr(ord("A") + index) if self.shift_mode else chr(ord("a") + index)
            self._add_button(letter, "insert", index // 5, index % 5)
        start_row = 6
        controls = (
            ("Calc", "alpha_toggle"), ("Shift", "shift_toggle"),
            ("(", "insert"), (")", "insert"), (",", "insert"),
            ("[", "insert"), ("]", "insert"), ("{", "insert"),
            ("}", "insert"), ("!", "insert"),
            ("CLR", "clear"), ("CE", "backspace"), ("Undo", "undo"),
            ("Redo", "redo"), ("=", "calculate"),
        )
        for index, (label, action) in enumerate(controls):
            self._add_button(label, action, start_row + index // 5, index % 5)

    def _build_menus(self):
        file_menu = self.menuBar().addMenu("File")
        clear_history = QAction("Clear History", self)
        clear_history.triggered.connect(self.clear_history)
        show_history = QAction("Show Saved History", self)
        show_history.triggered.connect(self.show_saved_history)
        file_menu.addAction(show_history)
        file_menu.addAction(clear_history)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = self.menuBar().addMenu("Edit")
        self._add_edit_action(edit_menu, "Copy", QKeySequence.StandardKey.Copy, self.display.copy)
        self._add_edit_action(edit_menu, "Paste", QKeySequence.StandardKey.Paste, self.display.paste)
        self._add_edit_action(edit_menu, "Undo", QKeySequence.StandardKey.Undo, self.display.undo)
        self._add_edit_action(edit_menu, "Redo", QKeySequence.StandardKey.Redo, self.display.redo)

        view_menu = self.menuBar().addMenu("View")
        theme_action = QAction("Dark Theme", self, checkable=True)
        theme_action.setChecked(self.theme == "dark")
        theme_action.toggled.connect(self._set_dark_theme)
        view_menu.addAction(theme_action)

        angle_menu = view_menu.addMenu("Angle Mode")
        angle_group = QActionGroup(self)
        angle_group.setExclusive(True)
        for label, unit in (("Degrees", "degrees"), ("Radians", "radians"), ("Gradians", "gradians")):
            action = QAction(label, self, checkable=True)
            action.setChecked(unit == self.angle_unit)
            action.triggered.connect(lambda _checked=False, value=unit: self._set_angle_mode(value))
            angle_group.addAction(action)
            angle_menu.addAction(action)

        format_menu = view_menu.addMenu("Output Format")
        precision_widget = QWidget()
        precision_layout = QHBoxLayout(precision_widget)
        precision_layout.setContentsMargins(8, 2, 8, 2)
        precision_layout.addWidget(QLabel("Decimal places"))
        precision = QSpinBox()
        precision.setRange(0, 15)
        precision.setValue(self.decimal_precision)
        precision.valueChanged.connect(self._set_precision)
        precision_layout.addWidget(precision)
        precision_action = QWidgetAction(self)
        precision_action.setDefaultWidget(precision_widget)
        format_menu.addAction(precision_action)

        scientific = QAction("Scientific Notation", self, checkable=True)
        scientific.setChecked(self.scientific_notation_enabled)
        scientific.toggled.connect(self._set_scientific_notation)
        format_menu.addAction(scientific)

        program_menu = self.menuBar().addMenu("Program")
        editor_action = QAction("Program Editor", self)
        editor_action.setShortcut("Ctrl+Shift+P")
        editor_action.triggered.connect(self._show_program_editor)
        program_menu.addAction(editor_action)
        clear_symbols = QAction("Clear Program Symbols", self)
        clear_symbols.triggered.connect(self.clear_program_symbols)
        program_menu.addAction(clear_symbols)

        help_menu = self.menuBar().addMenu("Help")
        about = QAction("About EfCalc Pro", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _build_shortcuts(self):
        clear_shortcut = QShortcut(QKeySequence("Esc"), self)
        clear_shortcut.activated.connect(self.display.clear)
        about_shortcut = QShortcut(QKeySequence("F1"), self)
        about_shortcut.activated.connect(self._show_about)

    def _add_edit_action(self, menu: QMenu, label, shortcut, callback):
        action = QAction(label, self)
        action.setShortcut(shortcut)
        action.triggered.connect(callback)
        menu.addAction(action)

    @staticmethod
    def _button_name(label):
        if label == "=":
            return "equalsButton"
        if label in ("CLR", "CE"):
            return "clearButton"
        if label in ("M+", "M-", "MR", "MC"):
            return "memoryButton"
        if label in ("Alpha", "Calc", "Shift"):
            return "modeButton"
        if label in ("+", "-", "*", "/", "%", "^", "!"):
            return "operatorButton"
        return "calculatorButton"

    def _dispatch(self, action, value):
        handlers = {
            "clear": self.display.clear,
            "backspace": self.display.backspace,
            "calculate": self.calculate_expression,
            "memory_recall": lambda: self._insert(self._format_result(self.memory)),
            "memory_clear": self._clear_memory,
            "memory_add": lambda: self._adjust_memory(1),
            "memory_subtract": lambda: self._adjust_memory(-1),
            "log_base": self._insert_log_base,
            "alpha_toggle": self._toggle_alpha_mode,
            "shift_toggle": self._toggle_shift_mode,
            "negative": self._insert_negative,
            "undo": self.display.undo,
            "redo": self.display.redo,
        }
        if action == "insert":
            self._insert(value)
        elif action == "function":
            self._insert(f"{value}(")
        elif action == "constant":
            self._insert(value.lower())
        else:
            handlers[action]()

    def _toggle_alpha_mode(self):
        self.alpha_mode = not self.alpha_mode
        if self.alpha_mode:
            self._show_alpha_buttons()
            self._show_status("Alpha mode: expression entry")
        else:
            self._show_calculator_buttons()
            self._show_status("Calculator mode")

    def _toggle_shift_mode(self):
        self.shift_mode = not self.shift_mode
        if self.alpha_mode:
            self._show_alpha_buttons()
        self._show_status(f"Shift: {'Uppercase' if self.shift_mode else 'Lowercase'}")

    def _insert_negative(self):
        position = self.display.cursorPosition()
        expression = self.display.text()
        if position == 0 or expression[position - 1] in "+-*/%^([,{":
            self._insert("-")
        else:
            self._insert("*(-1)")

    def _insert(self, value):
        self.display.insert(value)
        self.display.setFocus()

    def _insert_log_base(self):
        self._insert("log_b(,)")
        self.display.setCursorPosition(self.display.cursorPosition() - 2)

    def calculate_expression(self, set_answer=True):
        expression = self.display.text().strip()
        if not expression:
            self._show_status("Enter an expression")
            return None
        try:
            if self.program_variables or self.program_formulas:
                session = ProgramInterpreter(
                    angle_unit=self.angle_unit,
                    initial_variables=self.program_variables,
                    initial_formulas=self.program_formulas,
                    ans=self.ans,
                )
                result = session.evaluate_expression(expression)
            else:
                tree = Parser(Lexer(expression).generate_tokens()).parse()
                result = Interpreter(self.angle_unit, self.ans).visit(tree)
            if set_answer:
                self.ans = result
                formatted = self._format_result(result)
                self._add_history(expression, formatted)
                self.display.setText(formatted)
            return result
        except CalcError as error:
            self._show_status(str(error), 3500)
            self.display.selectAll()
            return None
        except (OverflowError, ValueError) as error:
            self._show_status(f"Calculation error: {error}", 3500)
            self.display.selectAll()
            return None

    def _format_result(self, value):
        if isinstance(value, int):
            return str(value)
        if not isinstance(value, float):
            return str(value)
        if not math.isfinite(value):
            return "Overflow" if math.isinf(value) else "NaN"
        if self.scientific_notation_enabled:
            return f"{value:.{self.decimal_precision}e}"
        formatted = f"{value:.{self.decimal_precision}f}".rstrip("0").rstrip(".")
        return formatted or "0"

    def _adjust_memory(self, direction):
        result = self.calculate_expression(set_answer=False)
        if result is not None:
            self.memory += direction * result
            self._show_status(f"Memory: {self._format_result(self.memory)}")

    def _clear_memory(self):
        self.memory = 0.0
        self._show_status("Memory cleared")

    def _history_link_clicked(self, url: QUrl):
        self.display.setText(unquote(url.toString()))
        self.display.setFocus()
        self._show_status("Loaded from history")

    def _add_history(self, expression, result):
        entry = (expression, result)
        self.history_entries.append(entry)
        self.history_entries = self.history_entries[-100:]
        self.settings.history = self.history_entries
        self._append_history_entry(expression, result)

    def _append_history_entry(self, expression, result):
        href = quote(expression, safe="")
        label = html.escape(f"{expression} = {result}")
        self.history_display.append(
            f'<a href="{href}" style="text-decoration:none;color:inherit">'
            f"{label}</a>"
        )
        scrollbar = self.history_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _initialize_history(self):
        """Load history data without pre-filling the startup history panel."""
        self.history_entries = list(self.settings.history)
        self.history_display.clear()

    def show_saved_history(self):
        self.history_display.clear()
        for expression, result in self.history_entries:
            self._append_history_entry(expression, result)
        self._show_status(
            f"Showing {len(self.history_entries)} saved history item(s)"
        )

    def clear_history(self):
        self.history_entries = []
        self.settings.history = []
        self.history_display.clear()
        self._show_status("History cleared")

    def _set_angle_mode(self, unit):
        self.angle_unit = unit
        self.settings.angle_unit = unit
        self._show_status(f"Angle mode: {unit.capitalize()}")

    def _set_precision(self, precision):
        self.decimal_precision = precision
        self.settings.precision = precision
        self._show_status(f"Precision: {precision} decimal places")

    def _set_scientific_notation(self, enabled):
        self.scientific_notation_enabled = enabled
        self.settings.scientific_notation = enabled
        self._show_status(f"Scientific notation: {'On' if enabled else 'Off'}")

    def _set_dark_theme(self, enabled):
        self.theme = "dark" if enabled else "light"
        self.settings.theme = self.theme
        self.apply_theme()
        self._show_status(f"Theme: {self.theme.capitalize()}")

    def _show_status(self, message, duration=1800):
        self._status_timer.stop()
        self.status_label.setText(message)
        self._status_timer.start(duration)

    def _restore_mode_status(self):
        memory_flag = " | M" if self.memory else ""
        symbol_count = len(self.program_variables) + len(self.program_formulas)
        symbol_flag = f" | Symbols {symbol_count}" if symbol_count else ""
        self.status_label.setText(
            f"{self.angle_unit.capitalize()} | Precision {self.decimal_precision}"
            f"{memory_flag}{symbol_flag}"
        )

    def _show_about(self):
        AboutDialog(self).exec()

    def _show_program_editor(self):
        if self.program_dialog is None:
            self.program_dialog = ProgramDialog(self)
        self.program_dialog.show()
        self.program_dialog.raise_()
        self.program_dialog.activateWindow()

    def update_program_symbols(self, variables, formulas, last_result):
        self.program_variables = dict(variables)
        self.program_formulas = dict(formulas)
        self.ans = last_result
        self._show_status(
            f"Program symbols loaded: "
            f"{len(variables)} variable(s), {len(formulas)} formula(s)",
            3000,
        )

    def clear_program_symbols(self):
        self.program_variables.clear()
        self.program_formulas.clear()
        if self.program_dialog is not None:
            self.program_dialog.variables.clear()
            self.program_dialog.formulas.clear()
            self.program_dialog.symbols.clear()
        self._show_status("Program variables and formulas cleared")

    def apply_theme(self):
        if self.theme == "dark":
            colors = {
                "window": "#20242b", "text": "#e6edf3", "display": "#11161d",
                "button": "#30363d", "border": "#59636e", "accent": "#2f81f7",
                "operator": "#3d4f66", "clear": "#b0444c", "memory": "#6246a8",
            }
        else:
            colors = {
                "window": "#f4f6f8", "text": "#17202a", "display": "#ffffff",
                "button": "#e7ebef", "border": "#aeb8c2", "accent": "#198754",
                "operator": "#cfe2ff", "clear": "#dc5a63", "memory": "#d9ccff",
            }
        self.setStyleSheet(f"""
            QMainWindow {{ background: {colors['window']}; color: {colors['text']}; }}
            QLabel {{ color: {colors['text']}; }}
            QLineEdit#display {{ background: {colors['display']}; color: {colors['text']};
                border: 2px solid {colors['border']}; border-radius: 8px;
                padding: 8px; font-size: 24pt; }}
            QTextBrowser#history {{ background: {colors['display']}; color: {colors['text']};
                border: 1px solid {colors['border']}; border-radius: 6px; }}
            QPushButton {{ background: {colors['button']}; color: {colors['text']};
                border: 1px solid {colors['border']}; border-radius: 6px; font-size: 11pt; }}
            QPushButton:hover {{ border: 2px solid {colors['accent']}; }}
            QPushButton#equalsButton {{ background: {colors['accent']}; color: white; font-weight: bold; }}
            QPushButton#operatorButton {{ background: {colors['operator']}; }}
            QPushButton#clearButton {{ background: {colors['clear']}; color: white; }}
            QPushButton#memoryButton {{ background: {colors['memory']}; }}
            QPushButton#modeButton {{ background: {colors['accent']}; color: white; }}
        """)

    def closeEvent(self, event: QCloseEvent):
        self.settings.window_geometry = self.saveGeometry()
        if self.program_dialog is not None and not self.program_dialog.maybe_save():
            event.ignore()
            return
        event.accept()


def run():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = ScientificCalculator()
    window.show()
    return app.exec()
