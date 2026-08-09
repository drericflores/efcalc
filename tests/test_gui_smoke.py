import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication
    from efcalc_gui import ScientificCalculator
except ImportError:
    QApplication = None
    ScientificCalculator = None


class MemorySettings:
    def __init__(self):
        self.theme = "light"
        self.angle_unit = "degrees"
        self.precision = 8
        self.scientific_notation = False
        self.history = []
        self.window_geometry = None


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class GuiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.settings = MemorySettings()
        self.window = ScientificCalculator(settings=self.settings)

    def tearDown(self):
        if self.window.program_dialog is not None:
            self.window.program_dialog.editor.document().setModified(False)
        self.window.close()

    def test_window_and_basic_calculation(self):
        self.assertIn("EfCalc Pro", self.window.windowTitle())
        self.window.display.setText("5+3*2")
        self.assertEqual(self.window.calculate_expression(), 11)
        self.assertEqual(self.window.display.text(), "11")

    def test_error_does_not_replace_expression(self):
        self.window.display.setText("1/0")
        self.assertIsNone(self.window.calculate_expression())
        self.assertEqual(self.window.display.text(), "1/0")

    def test_alpha_mode_can_be_entered_and_left(self):
        self.assertFalse(self.window.alpha_mode)
        self.window._toggle_alpha_mode()
        self.assertTrue(self.window.alpha_mode)
        self.window._toggle_alpha_mode()
        self.assertFalse(self.window.alpha_mode)

    def test_program_editor_executes_program(self):
        self.window._show_program_editor()
        dialog = self.window.program_dialog
        dialog.editor.setPlainText("x := 6\nprint(x^2)")
        dialog.run_program()
        self.assertEqual(dialog.output.toPlainText(), "36")
        self.assertEqual(dialog.variables["x"], 6)

    def test_program_editor_lists_formulas(self):
        self.window._show_program_editor()
        dialog = self.window.program_dialog
        dialog.editor.setPlainText(
            "formula square(x) := x^2\nvalue := square(4)\nprint(value)"
        )
        dialog.run_program()
        self.assertIn("square(x) := x^2", dialog.symbols.toPlainText())

    def test_program_symbols_are_available_in_calculator(self):
        self.window._show_program_editor()
        dialog = self.window.program_dialog
        dialog.editor.setPlainText(
            "formula add(a,b) := a+b\nx := 5\ny := 7"
        )
        dialog.run_program()
        self.window.display.setText("add(x,y)")
        self.assertEqual(self.window.calculate_expression(), 12)
        self.assertEqual(self.window.display.text(), "12")

    def test_clear_program_symbols(self):
        self.window.update_program_symbols({"x": 5}, {}, 5)
        self.window.clear_program_symbols()
        self.assertEqual(self.window.program_variables, {})
        self.assertEqual(self.window.program_formulas, {})

    def test_history_is_bounded_and_persisted(self):
        for number in range(105):
            self.window._add_history(str(number), str(number))
        self.assertEqual(len(self.window.history_entries), 100)
        self.assertEqual(len(self.settings.history), 100)
        self.assertEqual(self.window.history_entries[0], ("5", "5"))

    def test_clear_history_updates_settings(self):
        self.window._add_history("1+1", "2")
        self.window.clear_history()
        self.assertEqual(self.window.history_entries, [])
        self.assertEqual(self.settings.history, [])

    def test_saved_history_is_hidden_on_startup(self):
        self.window.close()
        self.settings = MemorySettings()
        self.settings.history = [("6*6", "36")]
        self.window = ScientificCalculator(settings=self.settings)
        self.assertEqual(self.window.display.text(), "")
        self.assertNotIn("6*6", self.window.history_display.toPlainText())
        self.window.show_saved_history()
        self.assertIn("6*6 = 36", self.window.history_display.toPlainText())


if __name__ == "__main__":
    unittest.main()
