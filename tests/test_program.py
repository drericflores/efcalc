import unittest

from efcalc_program import ProgramError, ProgramInterpreter, ProgramStopped


class ProgramInterpreterTests(unittest.TestCase):
    def test_assignments_and_output(self):
        source = """
            voltage := 12.5
            current := 2
            power := voltage * current
            print(power)
        """
        result = ProgramInterpreter().run(source)
        self.assertEqual(result.variables["power"], 25)
        self.assertEqual(result.output, ["25"])

    def test_answer_flows_between_lines(self):
        result = ProgramInterpreter().run("5+5\nans*3")
        self.assertEqual(result.output, ["10", "30"])
        self.assertEqual(result.last_result, 30)

    def test_comments_and_blank_lines(self):
        result = ProgramInterpreter().run("# test\nx := 4 # value\n\nprint(x^2)")
        self.assertEqual(result.output, ["16"])

    def test_reserved_names_are_rejected(self):
        with self.assertRaisesRegex(ProgramError, "reserved"):
            ProgramInterpreter().run("pi := 3")

    def test_errors_report_line_number(self):
        with self.assertRaisesRegex(ProgramError, "Line 2"):
            ProgramInterpreter().run("x := 2\ny := missing + 1")

    def test_if_else_comparisons(self):
        source = """
            value := 12
            if value >= 10
                print(value)
            else
                print(0)
            end
        """
        self.assertEqual(ProgramInterpreter().run(source).output, ["12"])

    def test_false_branch_and_nested_if(self):
        source = """
            value := 3
            if value > 10
                print(100)
            else
                if value == 3
                    print(3)
                end
            end
        """
        self.assertEqual(ProgramInterpreter().run(source).output, ["3"])

    def test_repeat_loop(self):
        source = """
            total := 0
            repeat 5
                total := total + 2
            end
            print(total)
        """
        result = ProgramInterpreter().run(source)
        self.assertEqual(result.variables["total"], 10)
        self.assertEqual(result.output, ["10"])

    def test_repeat_limit(self):
        with self.assertRaisesRegex(ProgramError, "repeat limit"):
            ProgramInterpreter().run("repeat 10001\nprint(1)\nend")

    def test_controlled_stop(self):
        interpreter = ProgramInterpreter(stop_requested=lambda: True)
        with self.assertRaises(ProgramStopped):
            interpreter.run("print(1)")

    def test_unclosed_block_reports_source_line(self):
        with self.assertRaisesRegex(ProgramError, "Line 1"):
            ProgramInterpreter().run("if 1\nprint(1)")

    def test_user_defined_formula(self):
        source = """
            formula area(r) := pi*r^2
            radius := 3
            print(area(radius))
        """
        result = ProgramInterpreter().run(source)
        self.assertAlmostEqual(float(result.output[0]), 28.2743338823)
        self.assertIn("area", result.formulas)

    def test_formula_with_multiple_parameters(self):
        source = """
            formula power(v, i) := v*i
            print(power(12.5, 2))
        """
        self.assertEqual(ProgramInterpreter().run(source).output, ["25"])

    def test_nested_formula_calls(self):
        source = """
            formula double(x) := x*2
            formula quadruple(x) := double(double(x))
            print(quadruple(5))
        """
        self.assertEqual(ProgramInterpreter().run(source).output, ["20"])

    def test_formula_argument_count(self):
        source = "formula add(a,b) := a+b\nprint(add(1))"
        with self.assertRaisesRegex(ProgramError, "requires 2 argument"):
            ProgramInterpreter().run(source)

    def test_duplicate_formula_parameter(self):
        with self.assertRaisesRegex(ProgramError, "Duplicate"):
            ProgramInterpreter().run("formula bad(x,x) := x")

    def test_formula_recursion_limit(self):
        source = "formula recurse(x) := recurse(x)\nprint(recurse(1))"
        with self.assertRaisesRegex(ProgramError, "recursion limit"):
            ProgramInterpreter().run(source)

    def test_program_session_evaluates_saved_symbols(self):
        interpreter = ProgramInterpreter()
        interpreter.run(
            "formula add(a,b) := a+b\nx := 10\ny := 7"
        )
        self.assertEqual(interpreter.evaluate_expression("add(x,y)"), 17)


if __name__ == "__main__":
    unittest.main()
