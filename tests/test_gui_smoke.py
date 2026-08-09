import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication
    from efcalc_gui import ScientificCalculator
except ImportError:
    QApplication = None
    ScientificCalculator = None


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class GuiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = ScientificCalculator()

    def tearDown(self):
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


if __name__ == "__main__":
    unittest.main()
