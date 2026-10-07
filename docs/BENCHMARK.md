# Pilot benchmark

Measured 2026-10-07 with draw.io Desktop **31.7.0**, Python/Pillow, Playwright
Chromium and the committed sources. Three matched Czech technical tasks, nominal
Word insertion width **160 mm**, equal export settings: light theme, border 16,
PNG scale 2, embedded native XML, SVG font embedding disabled. All six native
sources and SVG/PNG exports are committed. Browser audits and source findings
are in [reports](../benchmark/reports); portable hashes/settings in export
manifests; machine-readable numbers in [metrics.json](../benchmark/metrics.json).

## Method and fairness

An independent agent received the three prompts and only the official installed
JGraph skill/references. It first used Mermaid as that skill recommends, then
performed one improvement pass using the officially supported native XML route
after inspecting unsuitable initial layouts. The **improved** outputs, not the
weaker first pass, are compared here. It could choose content sizing and explicit
placement; the baseline was not artificially forced into 140×60 boxes. It did
not read the PJ implementation or benchmark conclusions.

The installed official SKILL.md exactly matched upstream commit
`eebe7def96409a15511a51fda958f4a620c2300a` (SHA-256
`3ac312c808c20357e38d2ce3506b776ece78a7b863792d9fed958c3dd05a3eb3`).
The PJ implementation received the same semantic tasks and used measured cards,
target-aware composition, export/lint/browser audit and local visual repairs.
The root then re-exported **both** selected source sets with the same adapter.
Comparison PNGs display equal widths, top-aligned, so the height difference is
visible. Reproduce: `python scripts/benchmark.py --reexport` after installing
Desktop, Python requirements and npm/browser dependencies.

Matched content:

- Process: receive image → verify exposure → usable?; yes → evaluate → save;
  no → adjust lighting → retry verification. Six nodes, six directed edges.
- Topology: camera → switch → IPC/PEKAT → MES; PLC trigger → camera;
  IPC result → PLC; service notebook ↔ switch. Conceptual, no hardware claim.
- Dense training: acquisition (optics/light), evaluation (dataset/model),
  operation (integration/diagnostics). Six title/body cards, three real groups,
  only two group-to-group arrows; individual cards are not a forced sequence.

## Measurements

| Case | Height at 160 mm, official → PJ | Smallest rendered font, official → PJ | Linear bends, official → PJ |
|---|---|---|---|
| Process | 154.8 → **54.9 mm** (−64.5%) | 14.63 → **10.81 pt** | 4 → **1** |
| Topology | 92.2 → **67.9 mm** (−26.4%) | 8.43 → **9.19 pt** | 3 → **2** |
| Dense training | 148.7 → **82.3 mm** (−44.7%) | 11.50 → **11.02 pt** | 0 → **0** |

The improvement is spatial efficiency with readable text, fewer bends and clearer
title/body hierarchy on these cases. Process and dense text are somewhat smaller
than the baseline but remain above the 9 pt document review minimum. Topology
improves the weakest font from below to above that minimum. This is **not** a
claim that every visual dimension improved or that PJ universally beats JGraph.

Both source sets are native editable cells, not flattened images. XML IDs,
terminal references and native roots passed structural checks. All SVG/PNG
exports contain native XML; the exporter verified image signatures and embeds.
PNG + source and embedded exports provide independent practical editing paths.

Browser checks found zero edge-edge crossing findings on all six exports. PJ
has no supported-range collision, text overflow, short-terminal or small-font
warnings on the three final SVGs. Every audit retains a bounds-approximation
uncertainty. Official process retains two own-label intersections and one short
terminal warning; official topology has label/node bounding contacts, own-label
intersections, a short terminal and small-font warning. These are review findings,
not all confirmed visual defects: white edge-label backgrounds intentionally mask
lines and rectangle bounds overestimate some outlines. They must not be counted
as indisputable collision totals. Dense baseline also has no such warnings.

Native source lint marks HTML estimates/automatic routing as uncertain even when
rendered QA passes. Its conservative text estimates are not used to assert a
rendered overflow. Opaque color ratios are checked there; explicit PJ palette
meets the design thresholds. Optical contrast was also reviewed in final PNGs.
Whitespace estimates are recorded, but container bounding area is not ink density
and cannot fairly rank dense grouped layouts on its own.

## Visual review

All final individual PNGs and all three side-by-side comparisons were opened and
visually reviewed. Repairs during the PJ loop: widened decision text region,
moved the yes label off the next node, cleared the no label from its vertical
line, aligned service ports, moved control labels away from lines, and removed
unnecessary bends. Meaning and terminal inventory were retained.

![Process comparison](../benchmark/process-comparison.png)
![Topology comparison](../benchmark/topology-comparison.png)
![Dense comparison](../benchmark/dense-training-comparison.png)

## Independent forward test and limits

A reviewer used the new skill on a fresh sensor/IPC/PLC decision diagram for a
16:9 slide. It created seven native nodes and five edges, exported embedded SVG/
PNG with Desktop, ran source/browser QA and inspected a 1600×900 slide-scale
preview. Projected minimum at 300 mm was **20.52 pt**. This separately exercises
the workflow beyond the three curated recipes. Installer dependency resolution
was tested in an isolated installation and corrected before publication.

The target-context gate remains **unverified**: no actual Microsoft Word or
PowerPoint document was rendered. Projected points and slide-scale PNG are useful
evidence, not Office pagination/font-substitution proof. No physical print,
projection, hardware topology test or upstream suite was performed. SVG path
sampling/rectangular bounds, complex stencils, rotated text, MathJax and asset
availability have the documented QA limits. PDF signature/export was smoke-tested;
PDF XML recovery was not independently checked. One agent-run pilot per workflow
does not establish statistically general performance or token-cost superiority.
