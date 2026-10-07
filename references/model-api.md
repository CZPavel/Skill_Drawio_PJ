# Optional JSON authoring helper

Run `python scripts/build_diagram.py model.json output.drawio` (Python 3.10+, Pillow). Model contains `profile`, optional `profile_overrides`, `groups`, `nodes`, `edges`. This is a small content-sizing helper for **new** diagrams; arbitrary XML/native shapes can be authored independently.

Node fields: unique `id`, `title`, optional `body`, `role` (data/control/ok/note/risk), local `x/y`, optional `width/height`, `parent`, `shape` (decision/terminal or native shape name), `style` overrides. Height is at least measured content height. Width omitted uses longest title word and a sensible body width; select width deliberately for the target. Explicit width still receives text-driven height. Long unbreakable text fails; it is never clipped. Decision sizing reserves a central text region and increases height.

Groups: unique `id`, `title`, `x/y/width/height`, optional role/parent; declare ancestors first. They are actual swimlane containers. Group sizing is deliberate; check child bounds. Edges: `id/source/target`, optional `label/role/style`, `points` (intermediate `[x,y]` in common parent frame), `label_position` (-1..1 along edge) and `label_offset` (normal displacement). Default ports connect right to left; override for vertical/back edges. Edges are filed at their nearest common ancestor.

The helper does not infer graph placement or route around obstacles. Use the external ELK/libavoid or deliberate composition; inspect after either. It does not validate arbitrary supplied style syntax or guarantee every vendor stencil. Runtime render remains required.

For portable font metrics supply `font_path` and `bold_font_path` and matching `font_family`. Defaults try system Arial then DejaVu; substitution can change wrapping, so inspect the actual export. Font files are not bundled. All profiles and colors are centralized in `assets/design-tokens.json`.

Examples: `examples/*/model.json` are reproducible authoring inputs, `.drawio` remains final editable source. After an interactive edit, do not rerun stale JSON over it without reconciling that edit.
