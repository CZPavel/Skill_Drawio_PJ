"""Export native draw.io with the external Desktop CLI and verified artifacts.

No upstream implementation is bundled. Each run stages fresh files in a private
output-directory temporary folder; previous artifacts cannot satisfy validation.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
from html.parser import HTMLParser
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zlib

from PIL import Image


def discover_drawio(explicit=None):
    """Find Desktop without assuming a PATH entry or a C: installation."""
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise ValueError(f"draw.io executable does not exist: {path}")
        return path.resolve()
    candidates = []
    for name in ("draw.io", "drawio", "draw.io.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    if sys.platform == "win32":
        candidates += [Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "draw.io/draw.io.exe",
                       Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/draw.io/draw.io.exe"]
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for branch in (r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                           r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
                try:
                    with winreg.OpenKey(hive, branch) as root:
                        for i in range(winreg.QueryInfoKey(root)[0]):
                            try:
                                with winreg.OpenKey(root, winreg.EnumKey(root, i)) as item:
                                    name = winreg.QueryValueEx(item, "DisplayName")[0]
                                    if "draw.io" not in name.lower():
                                        continue
                                    try:
                                        candidates.append(Path(winreg.QueryValueEx(item, "InstallLocation")[0]) / "draw.io.exe")
                                    except OSError:
                                        icon = winreg.QueryValueEx(item, "DisplayIcon")[0]
                                        candidates.append(Path(icon.rsplit(",", 1)[0].strip('"')))
                            except OSError:
                                continue
                except OSError:
                    continue
        candidates += [Path(f"{drive}:/Program Files/draw.io/draw.io.exe") for drive in "DEFGHIJKLMNOPQRSTUVWXYZ"]
    elif sys.platform == "darwin":
        candidates += [Path("/Applications/draw.io.app/Contents/MacOS/draw.io"),
                       Path.home() / "Applications/draw.io.app/Contents/MacOS/draw.io"]
    else:
        candidates += [Path("/usr/bin/drawio"), Path("/snap/bin/drawio"), Path("/opt/draw.io/drawio")]
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise ValueError("draw.io Desktop CLI not found; pass --drawio PATH")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _native_xml(text):
    root = ET.fromstring(text)
    if root.tag not in ("mxfile", "mxGraphModel"):
        raise ValueError("Expected native mxfile or mxGraphModel XML")
    if root.tag == "mxfile" and root.find("diagram") is None:
        raise ValueError("mxfile has no diagram")
    return root



class _ImageReferences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img":
            self.references.extend(value for key, value in attrs
                                   if key.lower() == "src" and value)


def _check_image_references(root):
    """Reject relative local images: temporary staging changes their base directory.

    HTTP(S), data URLs, file URLs and absolute filesystem paths pass this
    containment check; availability/rights/rendering are still caller concerns.
    Compressed pages are decoded for inspection only; Desktop receives the original.
    """
    for page in root.findall("diagram"):
        if page.find("mxGraphModel") is None and (page.text or "").strip():
            try:
                payload = base64.b64decode((page.text or "").strip(), validate=True)
                xml = unquote(zlib.decompress(payload, -15).decode("utf-8"))
                decoded = ET.fromstring(xml)
                if decoded.tag != "mxGraphModel":
                    raise ValueError("Decoded page is not mxGraphModel")
            except (ValueError, zlib.error, UnicodeError, ET.ParseError) as error:
                raise ValueError("Invalid compressed draw.io page; cannot inspect image references") from error
            _check_image_references(decoded)
    for cell in root.iter():
        references = []
        style = cell.get("style", "")
        # A semicolon is a style delimiter; data URLs may also contain one, but
        # their prefix is sufficient to classify them as non-local resources.
        references.extend(re.findall(r"(?:^|;)image=([^;]*)", style, flags=re.IGNORECASE))
        for attribute in ("value", "label"):
            parser = _ImageReferences()
            parser.feed(cell.get(attribute, ""))
            references.extend(parser.references)
        for reference in references:
            reference = unquote(reference.strip())
            scheme = urlsplit(reference).scheme.lower()
            absolute = (Path(reference).is_absolute() or
                        bool(re.match(r"^[a-zA-Z]:[\\/]", reference)) or
                        reference.startswith(("\\\\", "/")))
            if reference and scheme not in ("http", "https", "data", "file") and not absolute:
                raise ValueError("Relative local image reference is unsupported during staging; use embedded data or an absolute image path/URL")


def validate_artifact(path, kind):
    """Check signature, parseability and editable embed where supported here."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"CLI did not create a fresh nonempty {kind} output")
    if kind == "xml":
        _native_xml(path.read_text(encoding="utf-8-sig"))
    elif kind == "svg":
        root = ET.parse(path).getroot()
        if root.tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError("Export is not an SVG document")
        content = root.get("content")
        if not content:
            raise ValueError("SVG is missing embedded draw.io XML")
        _native_xml(content)
    elif kind == "png":
        if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Export is not PNG")
        with Image.open(path) as picture:
            # Desktop 31.7.0 uses mxGraphModel even when the value is mxfile.
            embedded = picture.info.get("mxGraphModel") or picture.info.get("mxfile")
            if not embedded:
                raise ValueError("PNG is missing embedded draw.io XML metadata")
            _native_xml(unquote(embedded))
            picture.verify()
    elif kind == "pdf":
        if not path.read_bytes().startswith(b"%PDF-"):
            raise ValueError("Export is not PDF")
    else:
        raise ValueError(f"Unsupported validation format: {kind}")


def _run(command, timeout):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"draw.io timed out after {timeout}s") from error
    if result.returncode:
        # Do not replay environment, application log output or potentially sensitive content.
        raise RuntimeError(f"draw.io failed with exit code {result.returncode}")
    return result


def _aliases(a, b):
    return a.resolve() == b.resolve() or (a.exists() and b.exists() and os.path.samefile(a, b))


def export(input_path, formats=("svg", "png"), output_dir=None, drawio=None,
           page_index=1, layout=None, timeout=45, crop_pdf=False):
    """Return a manifest after validated exports have been atomically published.

    Layout writes INPUTSTEM.layout.drawio alongside exports and exports only that
    persisted revised source. The input is never a destination. PDF validation is
    signature-only; it does not certify its embedded XML or visual correctness.
    """
    source = Path(input_path).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Input file does not exist: {source}")
    if source.suffix.lower() not in (".drawio", ".xml"):
        raise ValueError("Input must be a native .drawio or .xml file")
    _check_image_references(_native_xml(source.read_text(encoding="utf-8-sig")))
    formats = list(formats)
    if not formats or any(f not in ("svg", "png", "pdf") for f in formats) or len(set(formats)) != len(formats):
        raise ValueError("Choose unique formats from svg, png, pdf")
    if not isinstance(page_index, int) or page_index < 1:
        raise ValueError("page_index must be a positive 1-based integer")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    destination = Path(output_dir or source.parent).expanduser().resolve()
    targets = {fmt: destination / f"{source.stem}.{fmt}" for fmt in formats}
    revised = destination / f"{source.stem}.layout.drawio" if layout else None
    manifest_path = destination / f"{source.stem}.export.json"
    for target in [*targets.values(), manifest_path, *([revised] if revised else [])]:
        if _aliases(source, target):
            raise ValueError("Input/output alias rejected")
    executable = discover_drawio(drawio)
    destination.mkdir(parents=True, exist_ok=True)
    original_hash = sha256(source)
    commands = []
    version_command = [str(executable), "--version"]
    version = _run(version_command, timeout).stdout.strip()
    if not version:
        raise RuntimeError("draw.io did not report a version")
    commands.append(version_command)
    with tempfile.TemporaryDirectory(prefix=".drawio-export-", dir=destination) as temp:
        staging = Path(temp)
        # Snapshot avoids source races during CLI processing; preserves basename.
        snapshot = staging / source.name
        snapshot.write_bytes(source.read_bytes())
        if sha256(snapshot) != original_hash:
            raise RuntimeError("Input changed while preparing export")
        effective = snapshot
        if layout:
            effective = staging / "layout.drawio"
            cmd = [str(executable), "-x", "-f", "xml", "--layout", str(layout),
                   "-u", "--timeout", str(timeout), "-o", str(effective), str(snapshot)]
            commands.append(cmd)
            _run(cmd, timeout)
            validate_artifact(effective, "xml")
        staged = {}
        for fmt in formats:
            path = staging / f"export.{fmt}"
            cmd = [str(executable), "-x", "-f", fmt, "-e", "--theme", "light",
                   "-b", "16", "--page-index", str(page_index), "--timeout", str(timeout)]
            if fmt == "svg":
                cmd += ["--embed-svg-fonts", "false"]
            if fmt == "png":
                cmd += ["-s", "2"]
            if fmt == "pdf" and crop_pdf:
                cmd.append("--crop")
            cmd += ["-o", str(path), str(effective)]
            commands.append(cmd)
            _run(cmd, timeout)
            validate_artifact(path, fmt)
            staged[fmt] = path
        if sha256(source) != original_hash:
            raise RuntimeError("Input changed during export; outputs were not published")
        record = {
            "input": str(source), "input_sha256": original_hash,
            "source": str(revised or source), "source_sha256": sha256(effective),
            "drawio_executable": str(executable), "drawio_version": version,
            "page_index": page_index, "layout": layout, "commands": commands,
            "files": [{"format": fmt, "path": str(targets[fmt]), "sha256": sha256(path),
                       "bytes": path.stat().st_size} for fmt, path in staged.items()],
            "validation": {"svg": "parsed SVG root and native XML content attribute",
                           "png": "PNG signature, Pillow verify, native XML metadata",
                           "pdf": "PDF signature only; embedded XML not independently checked"},
            "manifest": str(manifest_path),
        }
        manifest_temp = staging / "manifest.json"
        manifest_temp.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if revised:
            os.replace(effective, revised)
        for fmt, path in staged.items():
            os.replace(path, targets[fmt])
        # A manifest is written last; earlier manifests are never treated as proof
        # of this run. Individual file replaces are atomic, not the whole batch.
        os.replace(manifest_temp, manifest_path)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--formats", nargs="+", choices=("svg", "png", "pdf"), default=["svg", "png"])
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--drawio")
    parser.add_argument("--page-index", type=int, default=1)
    parser.add_argument("--layout")
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--crop-pdf", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = export(args.input, args.formats, args.output_dir, args.drawio,
                        args.page_index, args.layout, args.timeout, args.crop_pdf)
    except (ValueError, RuntimeError, OSError, ET.ParseError) as error:
        parser.exit(1, f"Export failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
