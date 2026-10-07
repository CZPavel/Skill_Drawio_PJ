# Native XML QA coverage

`python scripts/lint_drawio.py diagram.drawio --json report.json --target-width-mm 160 --min-font-pt 9`

Original standard-library implementation; source is never modified. API: `lint(path, target_width_mm=None, min_font_pt=9) -> dict`. Findings contain `severity` (`error`, `warning`, `uncertain`), `code`, `cells`, `message`, `page`. Exit 2 means unreadable/invalid input, 1 means structural errors, 0 means no errors. **Exit 0 is not visual acceptance.** Warnings and uncertainty remain actionable.

| Check | Evidence and limit |
|---|---|
| XML, IDs, dangling parent/source/target, cycles, missing geometry | Native structure, including compressed multi-page mxfile, plain mxGraphModel and UserObject/object wrappers |
| Node overlap, containment, page bounds | Axis-aligned rectangles; ancestor overlap permitted, unrelated overlap flagged. Nested coordinates, relative vertices and offsets accumulated. Shapes/rotation require rendered inspection |
| Explicit colors, font, stroke width | Presence and opaque hex contrast. Inheritance, gradients, transparency and HTML colors require rendered inspection |
| Text fit | **Estimated**, character-width heuristic and conservative largest inline CSS font-size (px/pt/em/%). Does not reproduce fonts, CSS, mathematical text, shape interiors or browser wrapping |
| Target readability | Smallest source font scaled to target width over source content bounds. Unknown routed edge/label extents can change exported bounds; validate actual export and target document |
| Explicit polylines | Only unattached sourcePoint/targetPoint edges without automatic edgeStyle/curves. Segment-node/border, segment-segment, orthogonality, terminal length. Rectangles are conservative; intersections may be meaningful junctions |
| Automatic/attached edge routing | **Unresolved**: waypoints alone do not establish rendered route; emits `edge-path-unresolved` |
| Edge labels, edge-label and label-node collisions | **Unresolved**: emits `edge-label-unresolved`; require rendered SVG/PNG inspection |
| Optical alignment, meaningful arrows, role hierarchy, actual document readability | Human visual/target-document acceptance required |

`metrics.pages` contains: `page`, `nodes` (resolved vertex count), `edges`, `explicit_paths`, `bounds_px` (`[left,top,right,bottom]` of resolved nodes/explicit paths), `width_px`, `height_px`, `aspect_ratio`, `font_min_px`, `font_max_px`, `projected_min_font_pt`, `estimated_whitespace_fraction`. Whitespace is bounding rectangle area minus top-level node rectangle areas, clamped to zero; overlapping top-level nodes, labels and routed edges make this an approximation, not actual ink density. Missing values are null. `coverage.rendered_qa_required` is always true.

Regression tests use independent inline XML fixtures: Czech overflow/inline type, user wrappers, compressed multiple pages, ancestor/unrelated overlap, nested relative offsets, broken IDs/targets/cycles, explicit line collisions and unknown automatic routes. Run `python -m unittest discover -s tests -p test_lint_drawio.py`.
