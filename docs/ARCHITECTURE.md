# Architecture

The skill is a decision and quality layer above external draw.io tooling.

| Component | Contract |
|---|---|
| SKILL.md | short workflow, target selection, progressive reference loading, acceptance |
| references | composition, editing, engine interoperability, explicit QA coverage |
| assets/design-tokens.json | shared semantic palette and parameterized target profiles |
| build_diagram.py | optional new-document JSON authoring, font-based wrapping/sizing, native cells/containers |
| export_drawio.py | external Desktop adapter, bounded subprocess, embedded exports, source/export traceability |
| lint_drawio.py | read-only native structure, conservative geometry, contrast and estimated text fit |
| audit_svg.cjs | optional browser measurement of actual exported geometry/text, explicit unsupported coverage |
| examples + benchmark | reproducible inputs and native final source; independent official baseline |
| install.ps1 | managed copy of the skill package; preserves official/other skills |

No custom graph-layout/routing engine is maintained. ELK/libavoid/Mermaid and
native stencil rendering remain external capabilities. Direct XML/MCP editing
is available beyond the bounded JSON helper. Existing arbitrary diagrams must
not be regenerated through that helper: preservation requires targeted edits.

Generated model JSON is an authoring input, not an excuse to overwrite later
interactive edits. The delivered `.drawio` is source of truth. Export manifests
bind final source hash, engine version, page and output hashes. They can contain
local absolute paths and should remain local or be sanitized for public reports.

Portability: Python 3.10+; Pillow for sizing/PNG verification; Desktop for exports;
Node + Playwright/browser for optional rendered audit. Native linter is stdlib.
Missing optional tools must be reported, not silently represented as passed QA.
