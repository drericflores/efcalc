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
- Alpha/Shift keypad for named functions and advanced expression entry.

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
| `efcalc_settings.py` | Persistent Qt settings |
| `tests/` | Engine and GUI regression tests |

EfCalc Pro evaluates expressions through its own parser and does not use
Python's `eval()` function.
