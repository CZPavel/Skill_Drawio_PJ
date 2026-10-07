---
name: skill-drawio-pj
description: Create, inspect, edit and polish professional editable draw.io diagrams, block diagrams, processes, topologies and technical illustrations with content sizing, document or presentation layout, routing and rendered visual QA.
---

# Skill_Drawio_PJ

Use draw.io as an editable drawing engine. Optimize the explanation at the final reading size, not just XML validity. Match the user's language. Keep the native `.drawio` alongside synchronized exports. This independent community skill builds on external JGraph tooling; it does not replace the engine.

## Decide and compose

1. State the explanation in one sentence; identify nodes, roles, directions, conditions and evidence. Never infer a physical connection from proximity or invent a gateway to simplify lines. Distinguish a conceptual topology from verified hardware behavior.
2. Choose the archetype using [diagram-types](references/diagram-types.md). Independent principles are cards without arrows; decisions have questions and labeled alternatives.
3. Establish the target surface and insertion size. If unspecified, use document/160 mm and disclose that assumption. Read [targets](references/targets.md) for Word, slide 16:9, A4 portrait/landscape and standalone output. Typography must remain readable **after scaling**.
4. Read [design](references/design.md) for sizing, tokens and layout. Measure title/body separately, choose natural wrapping, then size. Align comparable roles without forcing all nodes to the same width/height. Do not solve overflow by shrinking fonts.
5. Lay out the main narrative, groups and secondary paths. Prefer left-to-right when it fits the target. For dense content, split overview/detail or pages while preserving meaning. A grid aligns objects; it does not dictate a universal box.
6. Read [routing](references/routing.md) when connectors are nontrivial. Improve placement before adding detours. Use short orthogonal connectors, clear ports, visible arrowheads and sufficient label clearance. Encode data/control/service meaning with labels as well as restrained color/line style.

## Author with the official engine

Read [JGraph baseline](references/jgraph-baseline.md) for XML, Mermaid, shapes, Desktop CLI, ELK and libavoid. Use native XML for precise final composition; Mermaid is an optional structural input. A converted image cell is not fully editable geometry. Do not blindly inherit upstream rigid-grid, source-deletion or no-coordinate-review preferences.

Optional original helper: `python scripts/build_diagram.py model.json output.drawio` creates measured native cards, groups and edges from JSON. It is a bounded authoring helper, not a universal auto-layout engine. See [model/API](references/model-api.md). Direct XML and native vendor shapes remain supported through the engine. Tokens live in `assets/design-tokens.json`.

For existing diagrams, read [editing](references/editing.md): inspect pages/layers/IDs, patch only affected cells, preserve unknown attributes and unrelated content. Do not use the creation helper to round-trip an arbitrary existing document. Never silently delete edges or change technical meaning as “autocorrection”.

## Required QA loop

Read [QA](references/qa.md) and [coverage](references/qa-coverage.md) before final acceptance.

1. Run structural and source geometry checks: `python scripts/lint_drawio.py diagram.drawio --json diagram.qa.json --target-width-mm 160`.
2. Export the final source through Desktop: `python scripts/export_drawio.py diagram.drawio --formats svg png --output-dir previews`. This produces embedded XML, checks output signatures and writes an export manifest tied to the source.
3. Inspect exported SVG and open the PNG with an image-viewing tool. Review the whole image at target scale and details: text fit, hierarchy, whitespace, alignment, topology, crossings, labels and arrowheads. A linter pass or thumbnail is insufficient.
4. Correct locally, re-export affected pages and repeat the affected checks. Regenerate all exports after any source change. Report unresolved coverage rather than claiming an automatic pass proves visual quality.
5. When inserting into Word/PPT, render the **resulting document/slide** and inspect surrounding native objects, crop, aspect ratio, title/footer and actual reading size. Standalone preview does not verify Office layout. Say explicitly when this target-context check has not been performed.

For bulk work, complete three representative pilots before applying the style to the remaining set. Follow any user-requested style approval gate; otherwise validate pilots and continue within scope. Preserve a practical undo path without redundant copies.

## Deliver

Deliver `.drawio`, requested SVG/PNG/PDF, concise validation status and material assumptions/limits. State the renderer/version, which pages were reviewed, and whether target-document QA occurred. Keep source, exports and final state traceable. Never call unresolved lint coverage “collision-free” or claim universal superiority from one benchmark.
