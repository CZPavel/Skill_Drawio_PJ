# JSON authoring: semantic IR and legacy coordinates

## V0.2 fast semantic input

```json
{
  "target": "document",
  "archetype": "process-flow",
  "direction": "auto",
  "style_preset": "industrial",
  "nodes": [
    {"id": "camera", "title": "Kamera", "body": "Pořízení snímku", "role": "data"},
    {"id": "ipc", "title": "IPC", "body": "Vyhodnocení", "role": "ok"}
  ],
  "groups": [],
  "edges": [{"id": "image", "source": "camera", "target": "ipc", "label": "Snímek"}]
}
```

`python scripts/build_diagram.py diagram.ir.json diagram.drawio --report layout.json`

Target uses the existing document/presentation/a4-portrait/a4-landscape/standalone
profiles. `direction`: auto/LR/TB. No coordinates required. Node requires id/title;
optional body, role, shape, group (alias parent), preferred_width, explicit width/
height and native style overrides. Role: data/control/ok/note/risk. Group requires
id/title; optional group/parent, role and explicit width/height. Missing group sizes
derive from children plus header/padding; explicit insufficient sizes produce review.

Edges require source/target; ID optional (stable edge-N generated). Optional label,
role, type (retry/feedback excluded from forward ranking), ports
`{"source":"bottom","target":"top"}`, style, label_position and label_offset.
Use ports only for semantic exceptions; otherwise geometry chooses facing sides.
Semantic placement clears old points, reporting the change. Legacy coordinate input
keeps user points. Labels are estimated; actual router paths need rendered review.

Missing any node/group x/y invokes semantic layout; `semantic:true` explicitly
requests it. Explicit direction restricts candidates. Limits are 3 for <=6 nodes,
8 for <=18, 12 above; forced directions may produce fewer. Candidate variations
are orientation, gap (40/64/88) and small measured width sets. Same IR/tokens/font
metrics yield identical geometry; changing fonts/platform may change wrapping.

`layout.json` includes selected candidate, score components, candidate metrics and
review_flags. Score is 100 minus weighted defects and may be negative; estimated
routes, text rectangle bounds and projection are not actual rendered acceptance.
Only the winning candidate is rendered. No arbitrary semantic content is deleted.

For document/slide variants change only target in the same IR, then build separate
files. This preserves content, IDs and directed edges; no automatic summarization.
For placed JSON: `python scripts/layout_diagram.py input.json placed.json --report layout.json`.
For score: `python scripts/score_layout.py placed.json --report score.json`.

Styles are small `assets/styles/*.json` files with optional font_family,
profile_overrides, vertex_style and edge_style. Explicit per-cell style wins.
Font/shape native overrides can exceed measured assumptions: review them visually.
Extract a proposal with `python scripts/extract_style.py existing.drawio --output proposed.json`;
inspect it before adding a named preset. HTML/inherited style is not inferred.

## Legacy coordinate mode

Run `python scripts/build_diagram.py model.json output.drawio` (Python 3.10+, Pillow). Model contains `profile`, optional `profile_overrides`, `groups`, `nodes`, `edges`. This is a small content-sizing helper for **new** diagrams; arbitrary XML/native shapes can be authored independently.

Node fields: unique `id`, `title`, optional `body`, `role` (data/control/ok/note/risk), local `x/y`, optional `width/height`, `parent`, `shape` (decision/terminal or native shape name), `style` overrides. Height is at least measured content height. Width omitted uses longest title word and a sensible body width; select width deliberately for the target. Explicit width still receives text-driven height. Long unbreakable text fails; it is never clipped. Decision sizing reserves a central text region and increases height.

Groups: unique `id`, `title`, `x/y/width/height`, optional role/parent; declare ancestors first. They are actual swimlane containers. Group sizing is deliberate; check child bounds. Edges: `id/source/target`, optional `label/role/style`, `points` (intermediate `[x,y]` in common parent frame), `label_position` (-1..1 along edge) and `label_offset` (normal displacement). Coordinate-mode ports default right to left; override vertical/back edges. Edges are filed at their nearest common ancestor.

Coordinate mode does not infer placement; semantic mode does. Neither routes around obstacles. Use the external ELK/libavoid or deliberate composition; inspect after either. It does not validate arbitrary supplied style syntax or guarantee every vendor stencil. Runtime render remains required.

For portable font metrics supply `font_path` and `bold_font_path` and matching `font_family`. Defaults try system Arial then DejaVu; substitution can change wrapping, so inspect the actual export. Font files are not bundled. All profiles and colors are centralized in `assets/design-tokens.json`.

Examples: `examples/*/model.json` are reproducible authoring inputs, `.drawio` remains final editable source. After an interactive edit, do not rerun stale JSON over it without reconciling that edit.
