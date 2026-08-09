#!/usr/bin/env python3
"""Backward-compatible launcher for EfCalc Pro 5.0.0.

The Qt6 application is implemented in :mod:`efcalc_gui`. Existing users can
continue launching ``python3 efcalc.py``; packages use ``main.py``.
"""

import sys

from efcalc_gui import run


if __name__ == "__main__":
    sys.exit(run())
