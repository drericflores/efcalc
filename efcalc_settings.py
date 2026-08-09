"""Persistent application settings for EfCalc Pro."""

import json

from PyQt6.QtCore import QSettings


class CalculatorSettings:
    def __init__(self):
        self._settings = QSettings("Anatolica", "EfCalc Pro")

    @property
    def theme(self):
        return self._settings.value("appearance/theme", "light", str)

    @theme.setter
    def theme(self, value):
        self._settings.setValue("appearance/theme", value)

    @property
    def angle_unit(self):
        return self._settings.value("calculation/angle_unit", "degrees", str)

    @angle_unit.setter
    def angle_unit(self, value):
        self._settings.setValue("calculation/angle_unit", value)

    @property
    def precision(self):
        return self._settings.value("calculation/precision", 8, int)

    @precision.setter
    def precision(self, value):
        self._settings.setValue("calculation/precision", int(value))

    @property
    def scientific_notation(self):
        return self._settings.value("calculation/scientific_notation", False, bool)

    @scientific_notation.setter
    def scientific_notation(self, value):
        self._settings.setValue("calculation/scientific_notation", bool(value))

    @property
    def history(self):
        raw_value = self._settings.value("history/items", "[]", str)
        try:
            items = json.loads(raw_value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
        if not isinstance(items, list):
            return []
        valid = []
        for item in items[-100:]:
            if (
                isinstance(item, list)
                and len(item) == 2
                and all(isinstance(value, str) for value in item)
            ):
                valid.append(tuple(item))
        return valid

    @history.setter
    def history(self, items):
        safe_items = [[str(expression), str(result)] for expression, result in items[-100:]]
        self._settings.setValue("history/items", json.dumps(safe_items))

    @property
    def window_geometry(self):
        return self._settings.value("window/geometry")

    @window_geometry.setter
    def window_geometry(self, geometry):
        self._settings.setValue("window/geometry", geometry)
