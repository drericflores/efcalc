import math
import unittest

from efcalc_engine import CalcError, Interpreter, evaluate


class EngineTests(unittest.TestCase):
    def test_gui_compatibility_collections(self):
        interpreter = Interpreter()
        self.assertIn("sin", interpreter.functions)
        self.assertIn("log_b", interpreter.functions)
        self.assertIn("pi", interpreter.constants)
        self.assertIn("ans", interpreter.constants)

    def test_named_variables(self):
        variables = {"voltage": 12.5, "current": 2}
        self.assertEqual(evaluate("voltage*current", variables=variables), 25)

    def test_controlled_user_function(self):
        functions = {"double": lambda value: value * 2}
        self.assertEqual(evaluate("double(6)", user_functions=functions), 12)

    def test_operator_precedence(self):
        self.assertEqual(evaluate("5+3*2"), 11)
        self.assertEqual(evaluate("-2^2"), -4)
        self.assertEqual(evaluate("(-2)^2"), 4)
        self.assertEqual(evaluate("2^3^2"), 512)
        self.assertEqual(evaluate("2^-2"), 0.25)

    def test_scientific_notation_and_implicit_multiplication(self):
        self.assertEqual(evaluate("1e3+2.5e2"), 1250)
        self.assertAlmostEqual(evaluate("2pi"), 2 * math.pi)
        self.assertEqual(evaluate("3(4+5)"), 27)
        self.assertAlmostEqual(evaluate("2sin(30)"), 1)

    def test_functions_and_units(self):
        self.assertAlmostEqual(evaluate("sin(30)"), 0.5)
        self.assertAlmostEqual(evaluate("sin(pi/2)", "radians"), 1)
        self.assertAlmostEqual(evaluate("asin(0.5)"), 30)
        self.assertEqual(evaluate("log(1000)"), 3)
        self.assertEqual(evaluate("log_b(8,2)"), 3)
        self.assertEqual(evaluate("sqrt(81)"), 9)

    def test_factorial_modulo_and_answer(self):
        self.assertEqual(evaluate("5!"), 120)
        self.assertEqual(evaluate("fact(6)"), 720)
        self.assertEqual(evaluate("17%5"), 2)
        self.assertEqual(evaluate("ans*2", ans=21), 42)

    def test_domains_and_syntax(self):
        invalid = ("1/0", "sqrt(-1)", "log(0)", "(-2)^0.5", "3.2!", ".", "1e+")
        for expression in invalid:
            with self.subTest(expression=expression):
                with self.assertRaises(CalcError):
                    evaluate(expression)


if __name__ == "__main__":
    unittest.main()
