"""Validate portable package links and native example source structure offline."""
import json
import hashlib
from pathlib import Path
import re
import sys
from lint_drawio import lint

root = Path(__file__).resolve().parents[1]
errors = []
skill = (root / "SKILL.md").read_text(encoding="utf-8")
if not re.search(r"^name: skill-drawio-pj$", skill, re.M):
    errors.append("canonical skill name is missing")
for file in root.rglob("*.md"):
    if any(part in {"node_modules", ".git", ".venv"} for part in file.relative_to(root).parts):
        continue
    for match in re.finditer(r"\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
        link = match.group(1).split("#")[0]
        if not link or "://" in link or link.startswith("mailto:"):
            continue
        if not (file.parent / link).exists():
            errors.append(f"{file.relative_to(root)}: broken local link {link}")
for file in (root / "examples").rglob("*.drawio"):
    result = lint(file)
    errors += [f"{file.relative_to(root)}: {f['code']} {f['cells']}" for f in result['findings'] if f['severity'] == 'error']
json.loads((root / "assets/design-tokens.json").read_text(encoding="utf-8"))
for manifest in (root / "benchmark").rglob("*.export.json"):
    record = json.loads(manifest.read_text(encoding="utf-8"))
    for relative, expected in [(record['source'], record['source_sha256'])] + [(f['path'], f['sha256']) for f in record['files']]:
        artifact = root / relative
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected:
            errors.append(f"{manifest.relative_to(root)}: stale artifact identity {relative}")
print("\n".join(errors) if errors else "Package links, tokens and example structures: PASS")
sys.exit(bool(errors))
