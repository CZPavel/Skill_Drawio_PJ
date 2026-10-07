"""Focused offline tests of fresh-output validation and source preservation."""
import importlib.util
import base64
import zlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote
import xml.etree.ElementTree as ET

from PIL import Image, PngImagePlugin

SPEC = importlib.util.spec_from_file_location("export_drawio", Path(__file__).resolve().parents[1] / "scripts/export_drawio.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
NATIVE = '<mxfile><diagram id="page" name="Page-1"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel></diagram></mxfile>'


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.source = self.base / "input.drawio"
        self.source.write_text(NATIVE, encoding="utf-8")
        self.executable = self.base / "draw.io.exe"
        self.executable.touch()
        self.output = self.base / "out"
        self.original = self.source.read_bytes()
        self.commands = []

    def fake_cli(self, command, **kwargs):
        self.commands.append(command)
        self.assertNotIn("shell", kwargs)
        self.assertGreater(kwargs["timeout"], 0)
        if "--version" in command:
            return subprocess.CompletedProcess(command, 0, "31.7.0\n", "")
        path = Path(command[command.index("-o") + 1])
        kind = command[command.index("-f") + 1]
        if kind == "xml":
            path.write_text(NATIVE.replace('name="Page-1"', 'name="Revised"'), encoding="utf-8")
        elif kind == "svg":
            root = ET.Element("{http://www.w3.org/2000/svg}svg", {"content": NATIVE})
            ET.ElementTree(root).write(path, encoding="utf-8")
        elif kind == "png":
            info = PngImagePlugin.PngInfo()
            info.add_text("mxGraphModel", quote(NATIVE))
            Image.new("RGB", (20, 20), "white").save(path, pnginfo=info)
        elif kind == "pdf":
            path.write_bytes(b"%PDF-1.7\nfixture")
        return subprocess.CompletedProcess(command, 0, "", "")

    def run_export(self, **kwargs):
        return module.export(self.source, output_dir=self.output, drawio=self.executable, **kwargs)

    @patch.object(module.subprocess, "run")
    def test_exports_embedded_formats_manifest_and_preserves_input(self, run):
        run.side_effect = self.fake_cli
        manifest = self.run_export(formats=("svg", "png", "pdf"), page_index=2, crop_pdf=True)
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(manifest["source_sha256"], module.sha256(self.source))
        self.assertEqual(len(manifest["files"]), 3)
        self.assertEqual(json.loads(Path(manifest["manifest"]).read_text())["page_index"], 2)
        self.assertTrue(all("--theme" in c and "-e" in c for c in self.commands[1:]))
        self.assertIn("--crop", self.commands[-1])
        self.assertEqual(self.commands[1][self.commands[1].index("--embed-svg-fonts") + 1], "false")
        self.assertEqual(self.commands[-2][self.commands[-2].index("-s") + 1], "2")

    @patch.object(module.subprocess, "run")
    def test_layout_persists_native_source_and_exports_that_same_state(self, run):
        run.side_effect = self.fake_cli
        manifest = self.run_export(layout="horizontalFlow")
        revised = Path(manifest["source"])
        self.assertTrue(revised.is_file())
        self.assertEqual(manifest["source_sha256"], module.sha256(revised))
        self.assertNotEqual(manifest["source_sha256"], manifest["input_sha256"])
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertIn("--layout", self.commands[1])
        self.assertNotIn("--layout", self.commands[2])
        self.assertEqual(self.commands[2][-1], self.commands[1][self.commands[1].index("-o") + 1])

    @patch.object(module.subprocess, "run")
    def test_stale_outputs_cannot_pass_when_cli_writes_nothing(self, run):
        self.output.mkdir()
        old = self.output / "input.svg"
        old.write_text("old output", encoding="utf-8")
        run.side_effect = lambda command, **kw: subprocess.CompletedProcess(command, 0, "31.7.0" if "--version" in command else "", "")
        with self.assertRaisesRegex(ValueError, "fresh nonempty"):
            self.run_export(formats=("svg",))
        self.assertEqual(old.read_text(), "old output")
        self.assertFalse((self.output / "input.export.json").exists())

    @patch.object(module.subprocess, "run")
    def test_failure_after_first_format_does_not_publish_partial_outputs(self, run):
        def fail_second(command, **kwargs):
            if "png" in command:
                return subprocess.CompletedProcess(command, 7, "", "sensitive log not replayed")
            return self.fake_cli(command, **kwargs)
        run.side_effect = fail_second
        with self.assertRaisesRegex(RuntimeError, "exit code 7"):
            self.run_export()
        self.assertFalse((self.output / "input.svg").exists())
        self.assertEqual(self.source.read_bytes(), self.original)

    @patch.object(module.subprocess, "run")
    def test_timeout_is_bounded(self, run):
        run.side_effect = subprocess.TimeoutExpired("draw.io", 1)
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            self.run_export(timeout=1)

    def test_input_output_alias_is_rejected(self):
        self.output.mkdir()
        (self.output / "input.svg").hardlink_to(self.source)
        with self.assertRaisesRegex(ValueError, "alias"):
            self.run_export(formats=("svg",))
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_svg_without_editable_embed_rejected(self):
        output = self.base / "invalid.svg"
        output.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        with self.assertRaisesRegex(ValueError, "embedded"):
            module.validate_artifact(output, "svg")

    def test_png_without_editable_embed_rejected(self):
        output = self.base / "invalid.png"
        Image.new("RGB", (10, 10)).save(output)
        with self.assertRaisesRegex(ValueError, "embedded"):
            module.validate_artifact(output, "png")

    def test_relative_style_images_rejected_before_cli(self):
        for reference in ("images/camera.png", "../camera.png", "camera.png"):
            with self.subTest(reference=reference):
                self.source.write_text(NATIVE.replace('<mxCell id="1" parent="0"/>',
                    f'<mxCell id="1" parent="0" style="shape=image;image={reference};"/>'))
                with patch.object(module.subprocess, "run") as run:
                    with self.assertRaisesRegex(ValueError, "Relative local image"):
                        self.run_export()
                    run.assert_not_called()

    def test_relative_html_images_rejected(self):
        for attr in ("value", "label"):
            root = ET.fromstring(NATIVE)
            root.find(".//mxCell").set(attr, '<b>Caption</b><img src="images/camera.png"/>')
            with self.subTest(attr=attr), self.assertRaisesRegex(ValueError, "Relative local image"):
                module._check_image_references(root)

    def test_absolute_and_embedded_image_references_allowed(self):
        for reference in ("https://example.com/camera.png", "data:image/png;base64,AA==",
                          "file:///C:/images/camera.png", "C:/images/camera.png",
                          "C:\\images\\camera.png", "/images/camera.png", "//host/share/camera.png"):
            root = ET.fromstring(NATIVE)
            root.find(".//mxCell").set("style", "shape=image;image=" + reference + ";")
            root.find(".//mxCell").set("value", '<img src="' + reference + '"/>')
            with self.subTest(reference=reference):
                module._check_image_references(root)

    def compressed_page(self, model):
        compressor = zlib.compressobj(wbits=-15)
        encoded = quote(model).encode("utf-8")
        payload = base64.b64encode(compressor.compress(encoded) + compressor.flush()).decode("ascii")
        return ET.fromstring("<mxfile><diagram>" + payload + "</diagram></mxfile>")

    def test_compressed_native_page_allowed_without_changing_input(self):
        root = self.compressed_page('<mxGraphModel><root><mxCell id="n" value="Camera"/></root></mxGraphModel>')
        before = ET.tostring(root)
        module._check_image_references(root)
        self.assertEqual(ET.tostring(root), before)

    def test_compressed_relative_images_rejected(self):
        for attributes in ({"style": "shape=image;image=images/camera.png;"},
                           {"value": '<img src="images/camera.png"/>'}):
            model = ET.Element("mxGraphModel")
            ET.SubElement(ET.SubElement(model, "root"), "mxCell", attributes)
            root = self.compressed_page(ET.tostring(model, encoding="unicode"))
            with self.subTest(attributes=attributes), self.assertRaisesRegex(ValueError, "Relative local image"):
                module._check_image_references(root)

    def test_invalid_compressed_page_rejected_clearly(self):
        with self.assertRaisesRegex(ValueError, "Invalid compressed draw.io"):
            module._check_image_references(ET.fromstring('<mxfile><diagram>encoded-content</diagram></mxfile>'))

    def test_invalid_options_are_rejected(self):
        for options in ({"formats": ("svg", "svg")}, {"timeout": 0}, {"page_index": 0}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.run_export(**options)


if __name__ == "__main__":
    unittest.main()
