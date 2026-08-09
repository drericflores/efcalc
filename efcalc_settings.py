"""Persistent application settings for EfCalc Pro."""

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
