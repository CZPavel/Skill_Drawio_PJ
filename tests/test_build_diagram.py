import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_diagram import build, measure, TOKENS


class BuilderTests(unittest.TestCase):
    def test_content_increases_height_and_escapes(self):
        short = measure("Optika", "", 300, TOKENS["profiles"]["document"])[2]
        long = measure("Optika", "Zorné pole a pracovní vzdálenost kamery.", 300, TOKENS["profiles"]["document"])[2]
        self.assertGreater(long, short)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.drawio"
            build({"nodes": [{"id": "a", "title": "A & B < C", "x": 0, "y": 0, "width": 300}]}, path)
            cell = ET.parse(path).find(".//mxCell[@id='a']")
            self.assertIn("&amp;", cell.get("value"))

    def test_decision_preserves_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.drawio"
            build({"nodes": [{"id": "a", "title": "Valid?", "body": "Threshold condition", "shape": "decision", "width": 700, "x": 0, "y": 0}]}, path)
            label = ET.parse(path).find(".//mxCell[@id='a']").get("value")
            self.assertIn("Threshold condition", label)

    def test_common_ancestor_and_no_lost_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.drawio"
            build({"groups": [{"id": "g", "title": "G", "x": 0, "y": 0, "width": 600, "height": 500}],
                   "nodes": [{"id": key, "title": key, "parent": "g", "x": x, "y": 100} for key, x in [("a", 20), ("b", 300)]],
                   "edges": [{"id": "e", "source": "a", "target": "b"}]}, path)
            edge = ET.parse(path).find(".//mxCell[@id='e']")
            self.assertEqual(edge.get("parent"), "g")
            self.assertIsNotNone(edge.find("mxGeometry"))

    def test_fail_instead_of_clip_or_dangling(self):
        with self.assertRaises(ValueError):
            measure("UNBREAKABLE_IDENTIFIER_1234567890", "", 80, TOKENS["profiles"]["document"])
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            build({"edges": [{"id": "e", "source": "missing", "target": "missing"}]}, Path(tmp) / "bad.drawio")


if __name__ == "__main__":
    unittest.main()
