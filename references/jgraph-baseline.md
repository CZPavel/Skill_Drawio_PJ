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
& $drawioExe -x -f xml --layout libavoid -o 'routed.drawio' 'layout.drawio'
& $drawioExe -x -f svg -e --theme light -b 16 -o 'routed.drawio.svg' 'routed.drawio'
```

Keep input/source files. Editable Mermaid conversion requires native cells, not `--mermaid-image true`. Review conversion for lost notation/labels. Standard ELK presets include horizontalFlow, verticalFlow, horizontalTree, verticalTree, radialTree and organic; custom layouts use a JSON array. Probe `--help` for the installed version. On GPU initialization failure retry once with `--disable-gpu`. Use separate layout outputs and adopt them only after checking semantic inventory and rendering.

The project export adapter detects Desktop, uses argument arrays and bounded timeouts, verifies signatures and embedded XML for supported image exports, and records hashes. SVG/PNG/PDF are external engine exports. PDF embedding is requested; verify recoverability separately if essential. Opening/rendering is required beyond subprocess success.
