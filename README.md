# EfCalc Pro 5.0.0

EfCalc Pro is a native Linux scientific calculator with a Qt6 graphical
interface and an independently tested expression engine.

Programmed by **Dr. Eric O. Flores**

Development release: **August 2026**

License: **GPL-3.0-or-later**

## Development status

Version 5.0.0 is under controlled development on the `develop-5.0.0` branch.
The `main` branch remains the recovered stable baseline until the new release
passes functional, interface, packaging, and installation testing.

## Capabilities

- Standard arithmetic and right-associative exponentiation.
- Parentheses and implicit multiplication, including `2pi` and `3(4+5)`.
- Scientific notation such as `1.25e-6`.
- Degree, radian, and gradian angle modes.
- Trigonometric, inverse-trigonometric, and hyperbolic functions.
- Base-10, natural, and arbitrary-base logarithms.
- Square root, exponential, absolute-value, modulo, and factorial operations.
- `ans` constant, calculation history, and calculator memory.
- Persistent light/dark theme, angle mode, precision, and output format.
- Keyboard editing with native Copy, Paste, Undo, and Redo.
- Persistent calculation history limited to the latest 100 results.
- Unsaved-program protection for New, Open, Close, and application exit.
- Alpha/Shift keypad for named functions and advanced expression entry.
- Multi-line programmable mode with named variables and `.efp` files.

## Pop!_OS and Ubuntu installation

Install the system-provided Qt6 Python bindings:

```bash
sudo apt update
sudo apt install -y python3-pyqt6
```

The Python Package Index dependency is documented in `requirements.txt` for
other Linux distributions and development environments.

## Running EfCalc Pro

```bash
python3 main.py
```

The historical command remains supported:

```bash
python3 efcalc.py
```

## Building the Pop!_OS/Ubuntu package

Build the release-candidate package reproducibly from the project root:

```bash
./scripts/build_deb.sh
```

Install and launch it:

```bash
sudo apt install ./dist/efcalc-pro_5.0.0~rc2_all.deb
efcalc-pro
```

The application is also available from the desktop application menu. Remove
the installed package without deleting user settings with:

```bash
sudo apt remove efcalc-pro
```

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile \
    main.py efcalc.py efcalc_engine.py efcalc_gui.py efcalc_settings.py
```

## Expression examples

| Expression | Result in degree mode |
|---|---:|
| `5+3*2` | `11` |
| `-2^2` | `-4` |
| `2^3^2` | `512` |
| `2pi` | `6.28318531` |
| `sin(30)` | `0.5` |
| `log_b(8,2)` | `3` |
| `5!` | `120` |

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Primary application launcher |
| `efcalc.py` | Backward-compatible launcher |
| `efcalc_gui.py` | PyQt6/Qt6 graphical interface |
| `efcalc_engine.py` | Lexer, parser, and calculation engine |
| `efcalc_program.py` | Safe multi-line program interpreter |
| `efcalc_settings.py` | Persistent Qt settings |
| `tests/` | Engine and GUI regression tests |

EfCalc Pro evaluates expressions through its own parser and does not use
Python's `eval()` function.

## Programmable mode

Open **Program → Program Editor** or press **Ctrl+Shift+P**. Phase 3A supports
comments, named-variable assignment, expressions, and printed output:

```text
# Ohm's law example
voltage := 12.5
current := 2
power := voltage * current
print(power)
```

Phase 3B also supports numeric comparisons, conditional blocks, and bounded
loops:

```text
total := 0
repeat 5
    total := total + 2
end

if total == 10
    print(total)
else
    print(0)
end
```

Supported comparisons are `<`, `<=`, `>`, `>=`, `==`, and `!=`. A repeat
count is limited to 10,000 and total execution is limited to 100,000
statements. The **Stop** control requests a safe stop between statements.

Programs are stored as UTF-8 `.efp` files. The interpreter reports the exact
line containing an error and never executes arbitrary Python code.

### User-defined formulas

Define reusable numeric formulas with one or more parameters:

```text
formula power(voltage, current) := voltage*current
formula circle_area(radius) := pi*radius^2

print(power(12.5, 2))
print(circle_area(3))
```

Formulas may call previously defined formulas. Formula execution is limited to
100 nested calls. The Program Editor symbol panel lists the variables and
formulas created by the latest successful run.

### Main-calculator integration

After a program runs successfully, its variables and formulas are immediately
available in the main calculator and Alpha mode. For example, run:

```text
formula add(a,b) := a+b
x := 5
y := 7
```

Then enter `add(x,y)` or `(x+y)` in the calculator display and press `=`. The
status bar reports the number of active program symbols. Use **Program → Clear
Program Symbols** to remove the shared variables and formulas deliberately.

## Reliability controls

- Calculation history and window geometry persist between sessions.
- EfCalc opens with a clear calculation area; saved history is displayed only
  when **File → Show Saved History** is selected.
- History is bounded to 100 entries to prevent uncontrolled growth.
- **Esc** clears the calculator display and **F1** opens About.
- Modified `.efp` programs show `*` in the editor title.
- New, Open, Close, and application exit prompt to Save, Discard, or Cancel
  when a program has unsaved changes.
