import configparser
import pathlib
import unittest
import xml.etree.ElementTree as ElementTree


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_required_packaging_files_exist(self):
        required = (
            "packaging/control",
            "packaging/efcalc-pro",
            "packaging/efcalc-pro.desktop",
            "packaging/io.github.drericflores.efcalc.metainfo.xml",
            "assets/efcalc-pro.svg",
            "scripts/build_deb.sh",
        )
        for relative_path in required:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_desktop_entry(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ROOT / "packaging/efcalc-pro.desktop")
        entry = parser["Desktop Entry"]
        self.assertEqual(entry["Type"], "Application")
        self.assertEqual(entry["Exec"], "efcalc-pro")
        self.assertEqual(entry["Icon"], "efcalc-pro")
        self.assertEqual(entry["Terminal"], "false")

    def test_control_dependencies(self):
        control = (ROOT / "packaging/control").read_text(encoding="utf-8")
        self.assertIn("Package: efcalc-pro", control)
        self.assertIn("Version: 5.0.0~rc1", control)
        self.assertIn("python3-pyqt6", control)

    def test_xml_metadata_and_svg_are_well_formed(self):
        ElementTree.parse(
            ROOT / "packaging/io.github.drericflores.efcalc.metainfo.xml"
        )
        ElementTree.parse(ROOT / "assets/efcalc-pro.svg")


if __name__ == "__main__":
    unittest.main()
