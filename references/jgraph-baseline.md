# External JGraph baseline

Inspected upstream: `jgraph/drawio-mcp` commit `eebe7def96409a15511a51fda958f4a620c2300a` (2026-10-07 review). Technical references, fetch only when needed:

- [XML](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/xml-reference.md)
- [Style syntax](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/style-reference.md)
- [Mermaid](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/mermaid-reference.md)
- [Official MCP](https://github.com/jgraph/drawio-mcp)

Use the format/style/CLI contracts, with this skill's content sizing, source retention and visual acceptance. Upstream layout preferences are not mandatory here. Dependencies are external and separately licensed; do not vendor engines, logos, WASM, fonts or stencil imagery.

Native source: `mxfile` → `diagram` → `mxGraphModel` → `root`; IDs 0 (root), 1 (default layer); unique cell IDs; valid parent/source/target. Every edge has relative `mxGeometry`. XML serialization must escape values including HTML. Containers use real parent-child relationships with child-local coordinates; keep edges at the common ancestor. Preserve object/UserObject wrappers, metadata, pages and unknown constructs on edit.

Use available official MCP `list_pages/get_page/set_page` for targeted page work and `search_shapes` for domain shapes. Inspect the current tool schema before calling. `set_page` replaces a whole page: retain unrelated cells in that page. Search shapes returns exact style strings; check asset rights/availability and avoid unnecessary external-image dependencies. Shape search may contact icons.diagrams.net; don't include private project text in queries.

Desktop examples (PowerShell; quote the executable path):

```powershell
$drawioExe = 'C:\Program Files\draw.io\draw.io.exe'
& $drawioExe -x -f xml -o 'draft.drawio' 'input.mmd'
& $drawioExe -x -f xml --layout horizontalFlow -o 'layout.drawio' 'draft.drawio'
# Only use layouts actually listed by the installed Desktop version.
& $drawioExe -x -f svg -e --theme light -b 16 -o 'routed.drawio.svg' 'routed.drawio'
```

Keep input/source files. Editable Mermaid conversion requires native cells, not `--mermaid-image true`. Review conversion for lost notation/labels. Standard presets include horizontalFlow, verticalFlow, horizontalTree, verticalTree, radialTree and organic; custom layouts use a JSON array. Probe `--help` for the installed version. On GPU initialization failure retry once with `--disable-gpu`. Use separate layout outputs and adopt them only after checking semantic inventory and rendering.

Historical V0.2 runtime finding (retested for V0.3): Desktop 31.7.0 on the author workstation rejects
`--layout libavoid` as unknown. Libavoid is available in the separately installed
official `@drawio/mcp` package. Optional original adapter:
`python scripts/route_drawio.py draft.drawio routed.drawio --mcp-root PATH_TO_PACKAGE`.
It calls external `src/libavoid-pass.js::routeXml`, checks native semantic/node
preservation, keeps input and reports unchanged output as unverified. It does not
bundle WASM or routing code. Export the adopted routed source, then inspect labels.
The upstream module path is an integration boundary, not a promised stable API.
For a diagram generated from unchanged IR, add `--ir diagram.ir.json` to perform
one bounded label repair against router waypoints. Explicit IR label positions
remain authoritative; changed node geometry is rejected. This is not import/sync.

The project export adapter detects Desktop, uses argument arrays and bounded timeouts, verifies signatures and embedded XML for supported image exports, and records hashes. SVG/PNG/PDF are external engine exports. PDF embedding is requested; verify recoverability separately if essential. Opening/rendering is required beyond subprocess success.


## V0.3 capability boundary

**Upstream declaration:** current JGraph Codex skill documents libavoid CLI and
ELK preset/custom JSON layouts. This is not a promise about an installed release.
**Verified local:** Desktop 31.7.0 help advertises ELK layouts; actual libavoid CLI
returns Unknown layout. Actual horizontalFlow changes positions/routes. Installed
@drawio/mcp 1.6.3 routeXml creates an obstacle detour preserving nodes; layoutXml
executes layered placement preserving checked semantics/sizes. These are runtime
smoke results, not visual quality acceptance.

`python scripts/probe_drawio.py --mcp-root PATH --json capabilities.json` tests fresh
temporary fixtures and distinguishes verified/unsupported/unavailable/unverified.
Run explicitly on installation/version change or once when a session needs routing;
never probe every diagram. The version string alone is not the capability contract.

The official MCP ELK interface accepts only direction (horizontal/vertical). PJ's
three named presets intentionally expose no unsupported options; compact currently
aliases clean. Desktop custom JSON may expose more, but no untested tuning is
forwarded through the MCP adapter. Node positions may change under ELK. Fixed
attachments that the official bridge changes are rejected before publication.


### Current bridge limit (verified V0.3)

The installed `@drawio/mcp` 1.6.3 bridges do not provide a verified side-constraint
contract. `routeXml` ignores source/target side masks when constructing libavoid
connections; retained style text is not proof that the route obeys those masks.
The adapters therefore reject side-constrained XML, including compressed pages,
before calling either engine. The strategy permits a side graph only with an
explicit verified `supports_side_constraints: true`; the current probe reports
false (not verified by this integration), including Desktop ELK. This is a bound
on this adapter, not a claim about every upstream ELK/libavoid implementation.
Use native sides and deliberate local waypoints for these graphs. Do not convert
side intent to fixed midpoint coordinates or silently remove constraints.
ELK also rejects output that changes explicit fixed attachment coordinates.
