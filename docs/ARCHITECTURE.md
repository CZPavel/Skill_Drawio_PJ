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

No general graph framework or obstacle-routing engine is maintained. ELK/libavoid/Mermaid and
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

## V0.2: semantic composition

New documents may start with a compact semantic IR. `layout_diagram.py` validates
it, measures cards using the existing builder, places bounded deterministic
candidates and selects with `score_layout.py`. The builder remains the native XML
writer and accepts legacy coordinate models. Named presets merge into tokens.
Native/ELK/libavoid remain routing engines; preview routes in scoring are estimates.
No server, database or persistent cache. Same IR supports document/presentation
without deleting content. Arbitrary existing files require targeted native edits;
generation does not implement lossless import or incremental manual-edit sync.
FAST needs Python/Pillow + Desktop + sight only for clear simple native routing;
report-driven FULL escalation adds browser audit. Office
fixtures and style extraction are optional helpers.


## V0.3 routing composition

connector_policy supplies anchoring, pair-specific jumps and capability-aware
engine recommendation. layout/score remain bounded estimates; actual engines are
external. probe_drawio is an explicit diagnostic with temporary fixtures, no DB.
elk_drawio and route_drawio publish separate native outputs only after contract
checks. fanout_junction is opt-in and records logical identity; design_review gives
warning-only grammar/legend/abstraction advice. SVG post_routing measurements are
separate from candidate scores. No new runtime dependency or engine is introduced.
