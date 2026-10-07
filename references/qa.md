# Acceptance combines checks and sight

Structural source validation, geometry checks, estimated text fit and contrast calculations establish different facts. See [coverage](qa-coverage.md) for exactly implemented checks and gaps. Warnings about unresolved routes or rich formatting are coverage limits, not proof of no defects.

Required loop: lint source → export final source to embedded SVG + PNG → inspect rendered geometry/text → open PNG → correct locally → repeat. Confirm source hash matches the export manifest; after a source change all delivered exports are stale. For multiple pages choose/export each required page (CLI page index is 1-based); PDF all-pages is a separate option, not implied by image export.

Visual rubric at the actual reading size:

| Dimension | Reject or repair when |
|---|---|
| Meaning | missing edge, reversed direction, lost exception, invented connection, misleading group |
| Text | overflow, truncation, awkward wrapping, source font looks large but insertion is unreadable |
| Composition | narrow centered strip without reason, vertical snake, dominant empty regions, weak hierarchy |
| Geometry | misaligned roles, clipped containers, inconsistent padding, node overlap |
| Routing | edge crosses foreign node/text, unnecessary bends, ambiguous end/branch/label, invisible arrowhead |
| Styling | disappearing boundary, low contrast, inconsistent family or too many colors |

Source font sizes are not the acceptance metric; projected points and actual crop matter. Contrast math assumes solid explicit colors; alpha, gradient, image backdrop, inheritance and dark themes demand additional rendered review. Overlap can be intentional (containment, callout), so inspect before changing semantics.

If composing Word/PPT, acceptance includes a render of the actual inserted result with surrounding content. Otherwise mark target-context QA unperformed. Automated SVG checks, if used, must describe path/shape/HTML coverage; do not call an approximation complete SVG lint.

For batch work use process, topology and dense training pilots first. Validate typography at insertion scale, then apply tokens. Review representative details and every changed diagram; do not substitute a contact sheet for detailed text/edge review.

## V0.2 depth and repair budget

FAST retains structure/estimated fit/projection, embedded SVG+PNG and sight;
Playwright is optional only for simple clear native routing. Layout report FULL
escalation is authoritative for unresolved routing/labels, jumps or engine repairs.
FULL adds browser/path/label inspection. One targeted
repair normally, at most two in FULL. Candidate estimates and exported paths are
separate evidence. Export only the selected candidate, optionally a close runner-up.


V0.3 SVG reports include `post_routing` screening metrics and per-edge bends/length.
Use `--model placed.json` to identify ordinary/main vs retry/secondary edges and
reading direction. Without that metadata semantic metrics are null. Strict interior
crossings exclude endpoint contacts; rectangle label/shape findings and curve/jump
sampling are approximate. Post-routing score is not candidate score or acceptance.
