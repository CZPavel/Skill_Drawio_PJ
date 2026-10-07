# Source comparison — Skill_Drawio_PJ

This is the research-stage snapshot, written before implementation. The new-skill
matrix column deliberately records the plan at that point. Final implemented
coverage and measured results are in [ARCHITECTURE](ARCHITECTURE.md),
[BENCHMARK](BENCHMARK.md), [native QA](../references/qa-coverage.md) and
[rendered QA](../references/rendered-qa.md); those later results do not retroactively
turn upstream static inspection into runtime verification.

Research completed before implementation, 2026-10-07. The supplied local specification is the product authority; upstream projects provide technical evidence and design ideas, not acceptance criteria. All eight requested default branches were cloned outside this public repository. This document summarizes direct inspection of skill instructions, references and implementation files, not only README claims. Machine-readable pinned identities, inspected paths, file digests and permanent links are in [source-evidence.json](source-evidence.json).

Evidence scope: **S** = implemented in inspected source; **G** = explicit guidance/workflow, not an automatic guarantee; **P** = partial/conditional implementation; **U** = unknown or not established by inspected files; **A** = absent in the inspected bounded package. Absence is not a claim about every historical branch or third-party extension. No upstream runtime suite was executed. A recent commit, reachable repository or non-archived state does not prove maintenance quality or runtime compatibility.

## Pinned source and license inventory

| Source | Inspected default-branch commit | Commit date | Last GitHub push | License |
|---|---|---|---|---|
| [JGraph](https://github.com/jgraph/drawio-mcp) | [`eebe7def9640`](https://github.com/jgraph/drawio-mcp/commit/eebe7def96409a15511a51fda958f4a620c2300a) | 2026-10-03T21:14:01+02:00 | 2026-10-03T19:17:40Z | Apache-2.0 |
| [Softaworks](https://github.com/softaworks/agent-toolkit) | [`3027f20f3181`](https://github.com/softaworks/agent-toolkit/commit/3027f20f3181758385a1bb8c022d4041dfb4de84) | 2026-03-05T13:46:24-03:00 | 2026-03-05T16:46:24Z | MIT |
| [Sunwood](https://github.com/Sunwood-ai-labs/draw-io-skill) | [`131921b2039b`](https://github.com/Sunwood-ai-labs/draw-io-skill/commit/131921b2039b02fc8ee16b23bdb951b1fbb59594) | 2026-06-04T01:29:31+09:00 | 2026-06-03T16:29:40Z | MIT |
| [SHALINS](https://github.com/SHALINS428/Codex-drawio-skill) | [`1f3acc7c002e`](https://github.com/SHALINS428/Codex-drawio-skill/commit/1f3acc7c002eab30e3858a9ea2bf514a6659e01a) | 2026-05-15T14:55:45+08:00 | 2026-05-15T06:55:53Z | MIT |
| [JMO808](https://github.com/jmo808/drawio_plugin) | [`170c000af0b8`](https://github.com/jmo808/drawio_plugin/commit/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e) | 2026-07-20T22:01:14-06:00 | 2026-07-21T04:01:15Z | MIT |
| [lgazo](https://github.com/lgazo/drawio-mcp-server) | [`afbd4bedef50`](https://github.com/lgazo/drawio-mcp-server/commit/afbd4bedef50b117889d4c0f47692d311df5b71e) | 2026-09-14T17:02:06+02:00 | 2026-09-15T20:08:16Z | MIT |
| [abossard](https://github.com/abossard/drawio-mcp) | [`9a1992ec6109`](https://github.com/abossard/drawio-mcp/commit/9a1992ec610911b35433e0f7e7f69b8c8f512c3a) | 2026-02-12T23:41:08+01:00 | 2026-05-09T04:37:55Z | MIT |
| [yohasacura](https://github.com/yohasacura/drawio-mcp) | [`036573d746e1`](https://github.com/yohasacura/drawio-mcp/commit/036573d746e1720e121701dfe0b3b570c4895e2a) | 2026-02-09T19:50:00+02:00 | 2026-02-09T17:50:13Z | MIT |

All eight repositories reported `archived=false` and `main` as default branch during this review. Dates above are exact API/Git observations; push time can differ from default-branch commit time (notably abossard). The root license files were read, not inferred only from GitHub labels. JGraph also contains a separately licensed vendored libavoid component: its inspected LICENSE is LGPL version 2.1. Root licenses do not blanket-license vendor symbols, fonts or assets.

## Feature matrix

Skill_Drawio_PJ column is an implementation **plan**, not a claim of delivered behavior. It must be updated against actual tests and the benchmark after implementation. `Plan G` means a workflow rule; `Plan S` means intended local tooling; `External` delegates to installed JGraph tooling. No matrix cell asserts runtime verification.

| Function / principle | JGraph | Softaworks | Sunwood | SHALINS | JMO808 | lgazo | abossard | yohasacura | Skill_Drawio_PJ |
|---|---|---|---|---|---|---|---|---|---|
| `.drawio` source of truth | P: native, source deleted after image delivery | G | G | G: always paired | S | S: live document | S | S | Plan G: retain source |
| Mermaid | G/S conversion path | U | G via JGraph workflow | A | U | U | U | U | External, conditional |
| XML generation | S/G | G | G | S: starter | S | S: editor operations | S | S | Plan S |
| Content-driven sizing | P: reference prescribes fixed grid | G: enlarge before shrink | G | G | S/P: builder sizing | U | P: layout dimensions | P | Plan S |
| Target-aware layout | U | G: PDF/slides | G | G: A4/column | U | U | U | P: page format | Plan S/G |
| Auto-layout | S: ELK | A in skill package | G via engine | A in package | S: ELK | U | S: snake layout | S: several strategies | External + own bounded layout |
| Orthogonal routing | S: libavoid/ELK | G | G | G/S: starter waypoints | S/G | S: waypoints | S/P | S: A* obstacle routing | External + Plan S/G |
| Collision detection | P: routing avoids obstacles | G: visual checks | S: SVG linter | G: visual checks | S: validator | U | S: routing/layout issues | S: overlap analysis | Plan S |
| Text overflow detection | U | G: visual checks | S: estimates + companion XML | G: visual checks | U | U | U | U | Plan S: estimates + render |
| Contrast QA | U | U | S: linter ratio checks | G: print/readability | U | U | U | U | Plan S |
| Visual QA | G: open result, limited explicit acceptance | G: inspect PNG | G: export/lint/review | G: page readability gate | G | P: live editor | S/G: screenshot tool | U | Plan G: mandatory preview review |
| Word/PPT targeting | U | G: presentation/PDF | G: docs/presentations | P: A4 paper, excludes slide authoring | U | U | U | P: page format | Plan S/G: document/presentation |
| Layers | G/S | U | U | U | P: parent model | S | U | S | Plan G/P: preserve |
| Templates / presets | G: reference examples | G: architecture examples | G/S: aesthetic samples | S/G: figure starter/types | S/G: domain patterns | P: loaded libraries | S: styles | S: themes/shape/edge presets | Plan S/G: archetypes/tokens |
| Live targeted editing | P: pages/XML operations | G: XML edit | G: XML edit | G | S/P: round-trip import | S | S: bridge + file edits | S: in-memory edits/load/save | Plan G/S: local targeted edits |
| Cleanup / polish | P: layout/routing passes | G | G | G | S: correction passes | U | P: layout/validation | S: polish action | Plan S/G: bounded corrections |
| Source/export synchronization | P: embedded delivery replaces source | G | G | G: paired output required | U | P: save current document | P: file watch | U | Plan S: export from final source |

## Findings and adoption decisions

### JGraph — technical baseline

Inspected Codex skill `plugins/codex/drawio/skills/drawio/SKILL.md`; shared XML/style/Mermaid references; shape search and Mermaid/ELK modules; tool-server `index.js`, `elk-pass.js`, `libavoid-pass.js`; and vendored libavoid license. Permanent links are listed below and in the evidence JSON.

Strengths: native mxGraph XML and styles, documented Desktop CLI export with embedded XML, Mermaid-to-native conversion, optional ELK and orthogonal libavoid passes, shape-library search and a common engine across integrations. The implementation imports layout/routing passes and page helpers rather than being only a prompt.

Limits relevant to this project: `shared/xml-reference.md` prescribes a rigid grid with 140×60 rectangles, discourages coordinate rechecking and explicit waypoints. The Codex skill's export workflow deletes `.drawio` after delivering an embedded image. These conflict with the supplied sizing/QA/source-retention requirements. CLI documentation and references are version-sensitive; local Desktop help and runtime behavior still need independent verification. Opening an output is weaker than a mandatory visual acceptance gate.

Adopt the external engine, native format, style contract, shape search and export/ELK/libavoid capabilities. Write original guidance and adapters. Do not copy rigid-grid rules, deletion workflow, upstream text, code or logos. Apache-2.0 permits reuse with its terms, but this project chooses no source copying. External use avoids redistributing the LGPL libavoid payload; dependencies retain their own licenses.

### Softaworks — practical editing and layout guidance

Inspected `skills/draw-io/SKILL.md`, its layout reference and README. Strengths include explicit font styles, larger PDF-readable text, grouping, container margins, connector/label clearance and required visual PNG overflow inspection. The layout reference is concise and largely AWS-oriented; it is guidance, not a generic geometry/contrast engine. No automatic lint engine or general-purpose adaptive sizing implementation was established in this bounded skill package. Progressive disclosure is useful as a general authoring principle, but a specialized implemented diagram decomposition mechanism was not established.

Adopt consistent typography, semantic grouping, margins and visual inspection as original rules. Avoid assuming AWS grouping or Japanese font choices are universal. MIT permits copying with notices, but only principles will be adopted. The inspected March commit remains reachable; this alone does not establish ongoing maintenance.

### Sunwood — export, lint, visual review

Inspected `SKILL.md`, `scripts/export-drawio.mjs`, `scripts/check-drawio-svg-overlaps.mjs`, layout guidance and contrast/overflow fixtures. This is substantive QA code: SVG geometry checks include edge contacts, node/border contacts and label interactions; companion `.drawio` information enables estimated text width/height and text contrast checks. The workflow explicitly combines export, lint, review and repair. Fixtures exist, but were inspected rather than executed in this review.

Limits: the linter warns that text-overflow, text-contrast, text-emphasis and label-rect checks are skipped without a companion `.drawio`. Text metrics and supported shapes/paths are approximations, not browser text-layout proof. Lint acceptance cannot certify overall composition or readability. The skill also includes blended upstream guidance: a root MIT label is not sufficient provenance for copying arbitrary inherited text/assets.

Adopt the categories of geometry/typography/contrast checks and the export → lint → visual review loop using original implementation. Report approximation limits and unsupported cases. Do not copy the parser, heuristics, fixtures, templates or reference prose. MIT allows licensed reuse with notices, but clean original implementation is the chosen lower-maintenance path.

### SHALINS — publication-oriented composition

Inspected `skill/drawio/SKILL.md`, academic style and figure-type references, starter and PNG-export PowerShell scripts. Strengths: paired editable source/PNG delivery, A4 normal-scale readability, distinct architecture/roadmap/process composition, explicit anchors and bend points, and avoiding box/text compression.

Limits: it mandates 26px diagram text by default and focuses on academic paper figures; this is not an appropriate universal size for Word, slides and all canvas scales. The starter demonstrates generation, not automatic collision/text/contrast QA. Its scope explicitly excludes slide-deck authoring, although its diagram readability principles transfer.

Adopt type-specific composition, normal-scale review and synchronized source/export delivery. Replace fixed typography with parameterized target tokens and avoid mandatory waypoints when a simple direct orthogonal edge is clearer. MIT permits reuse with notices; only original restatement of principles is planned.

### JMO808 — builder, validation and domain corrections

Inspected `scripts/diagram-builder.js`, `validate.js`, design-quality/network/AWS validators, ELK integration and skill. Strengths: concrete builder abstraction, XML import/round-trip path, containment/sizing, collision/out-of-bounds/waypoint validation, design spacing warnings and domain-specific validators/correctors.

Limits: architecture and domain assumptions are deeply coupled to the builder. Some correction logic infers platform/node type from labels and even removes selected edges (for example load-balancer-to-broker relationships). Such automatic semantic correction is unsuitable for arbitrary technical diagrams without an explicit domain contract. Import support does not establish lossless round-trip preservation of every draw.io construct. Generic warnings do not replace rendered text/contrast measurement.

Adopt small deterministic validation and explicit domain-rule selection as concepts. Do not copy the builder or transplant broad domain inference, silent semantic edge removal or a competing engine. MIT reuse is permitted with notices; principles only are selected.

### lgazo — rich live document editing

Inspected tool definitions for edge editing, parent assignment, layers/pages and shape lookup, plus plugin-side `drawio-tools.ts`. Strengths: targeted edit operations, optional edge waypoints, pages/layers, parent/group operations and access to the current diagram's loaded shape libraries. Server schemas and plugin execution are distinct parts of the system.

Limits: the live editor/plugin/transport must be connected; tool availability alone is not runtime verification. Library lookup concerns available/loaded libraries, not a guarantee that every vendor stencil is licensed or installed. No general text-overflow/contrast/automatic polish system was established in inspected tools.

Adopt preserving IDs, parent hierarchy, pages, layers and unrelated cells during targeted edits. Prefer optional live integration over making it a mandatory local dependency. MIT permits reuse with notices; no server/plugin source or stencil assets will be redistributed.

### abossard — visual feedback and undo/redo

Inspected `src/index.ts`, `drawio.ts`, `sidecar.ts` and the VS Code bridge extension. Strengths: file-based targeted node/edge changes, file watch, operation history, undo/redo, layout/routing diagnostics and a screenshot tool for visual feedback.

Limits: screenshot capture requires an open diagram in VS Code with its companion bridge connected. Undo/redo of MCP file operations is explicitly separate from editor undo. The code's fallback highlighting temporarily mutates styles when no companion exists; do not introduce this into a read-only inspect workflow. GitHub push time is later than the pinned main commit, so activity must not be inferred from push time alone.

Adopt local incremental changes and preview feedback; use Git/diff or controlled local snapshots where necessary rather than adding another bridge/history stack. MIT permits reuse with notices; principles only.

### yohasacura — presets and explicit cleanup strategies

Inspected models, server, styles, layout, layout_engine and validation Python modules. Strengths: native model serialization, groups/layers/pages, vertex/edge/theme presets, layout strategies, overlap analysis/resolution, compact/alignment actions and a polish workflow. `route_edges_around_obstacles` implements orthogonal A* routing over a visibility grid built from node bounds, excluding the current edge endpoints.

Limits: automatic cleanup can move user-authored geometry. Bounding-box routing/overlap detection does not prove shape-outline accuracy, label clearance, contrast or optimal composition. A theme alone does not ensure adequate contrast. No runtime guarantee is inferred from catalog descriptions.

Adopt semantic tokens, bounded cleanup stages and clear separation of layout/routing/inspection. Do not copy its engine or make blanket polish alter existing diagrams without a reviewed scope. MIT permits copying with notices; no source copying is planned.

## License and implementation boundary

The new project's original code and prose can use MIT, provided implementation follows this no-copy decision. This review is not a redistribution inventory for arbitrary dependencies: external installed draw.io Desktop/JGraph tooling remains separately licensed. Do not vendor upstream engines, WASM, stencil images, logos, fonts, samples or reference prose. Shape identifiers and interoperable XML/style syntax are used as format contracts; vendor asset rights remain with their owners.

If later work copies any upstream protectable material, stop that copy path and record the exact files, license, required attribution/notices and compatibility before including it. Apache-2.0 and MIT permit substantial reuse subject to their conditions; LGPL vendored components require a separate compliance assessment if redistributed. A root MIT label does not relicense third-party assets. `THIRD_PARTY_NOTICES.md` should identify external tooling and inspiration honestly, without claiming upstream code was incorporated.

## Implementation priorities derived from evidence

1. Keep native `.drawio` as persistent source and export only from its finalized state.
2. Use external JGraph format/export/layout/routing capabilities; do not fork an engine.
3. Size content before placement; select document/presentation target before sizing.
4. Keep typography, colors, padding and arrows in original central tokens, with diagram-specific archetypes.
5. Separate structural validation, geometric/estimated text/contrast lint and mandatory rendered visual review. State what each check actually establishes.
6. Make existing-diagram operations targeted and preserve IDs, pages/layers/groups, unknown styles and unrelated content.
7. Fix node placement before routing complexity; use libavoid as a final routing aid. No automatic domain-semantic correction.
8. Demonstrate quality with matched prompts and measured previews against the pinned official workflow. This comparison itself does not establish benchmark superiority.

## Verification performed and remaining gates

Performed: authenticated GitHub metadata reads without printing credentials; successful HTTPS Git clone of all eight sources; exact default-branch commit/date capture; direct license and implementation/reference inspection; all 55 evidence paths exist at their pinned commits and returned HTTP 200 from their permanent raw-file URLs. File SHA-256 values identify inspected evidence, not policy validity. Repository web pages were also opened for JGraph, Sunwood, lgazo and yohasacura. No source files, prose excerpts or assets were copied into this project.

Remaining: upstream runtime tests, local JGraph/CLI version compatibility, actual new-skill feature tests, installed-skill test, visual review and comparative benchmark. Those are implementation acceptance work, not outcomes claimed by this static review. No additional repository was needed to establish the requested baseline; all eight mandatory sources are covered.

## Permanent inspected-file links

### JGraph

- [LICENSE](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/LICENSE)
- [plugins/codex/drawio/skills/drawio/SKILL.md](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/plugins/codex/drawio/skills/drawio/SKILL.md)
- [shared/xml-reference.md](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/xml-reference.md)
- [shared/style-reference.md](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/style-reference.md)
- [shared/mermaid-reference.md](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/mermaid-reference.md)
- [shared/shape-search.js](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/shape-search.js)
- [shared/mermaid-elk.js](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/shared/mermaid-elk.js)
- [mcp-tool-server/src/index.js](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/mcp-tool-server/src/index.js)
- [mcp-tool-server/src/elk-pass.js](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/mcp-tool-server/src/elk-pass.js)
- [mcp-tool-server/src/libavoid-pass.js](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/mcp-tool-server/src/libavoid-pass.js)
- [mcp-tool-server/vendor/libavoid/LICENSE](https://github.com/jgraph/drawio-mcp/blob/eebe7def96409a15511a51fda958f4a620c2300a/mcp-tool-server/vendor/libavoid/LICENSE)

### Softaworks

- [LICENSE](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/LICENSE)
- [skills/draw-io/SKILL.md](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/draw-io/SKILL.md)
- [skills/draw-io/references/layout-guidelines.md](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/draw-io/references/layout-guidelines.md)
- [skills/draw-io/README.md](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/draw-io/README.md)

### Sunwood

- [LICENSE](https://github.com/Sunwood-ai-labs/draw-io-skill/blob/131921b2039b02fc8ee16b23bdb951b1fbb59594/LICENSE)
- [SKILL.md](https://github.com/Sunwood-ai-labs/draw-io-skill/blob/131921b2039b02fc8ee16b23bdb951b1fbb59594/SKILL.md)
- [scripts/check-drawio-svg-overlaps.mjs](https://github.com/Sunwood-ai-labs/draw-io-skill/blob/131921b2039b02fc8ee16b23bdb951b1fbb59594/scripts/check-drawio-svg-overlaps.mjs)
- [scripts/export-drawio.mjs](https://github.com/Sunwood-ai-labs/draw-io-skill/blob/131921b2039b02fc8ee16b23bdb951b1fbb59594/scripts/export-drawio.mjs)
- [references/layout-guidelines.en.md](https://github.com/Sunwood-ai-labs/draw-io-skill/blob/131921b2039b02fc8ee16b23bdb951b1fbb59594/references/layout-guidelines.en.md)
- [scripts/verify-text-contrast-fixture.mjs](https://github.com/Sunwood-ai-labs/draw-io-skill/blob/131921b2039b02fc8ee16b23bdb951b1fbb59594/scripts/verify-text-contrast-fixture.mjs)
- [scripts/verify-shape-text-overflow-fixture.mjs](https://github.com/Sunwood-ai-labs/draw-io-skill/blob/131921b2039b02fc8ee16b23bdb951b1fbb59594/scripts/verify-shape-text-overflow-fixture.mjs)

### SHALINS

- [LICENSE](https://github.com/SHALINS428/Codex-drawio-skill/blob/1f3acc7c002eab30e3858a9ea2bf514a6659e01a/LICENSE)
- [skill/drawio/SKILL.md](https://github.com/SHALINS428/Codex-drawio-skill/blob/1f3acc7c002eab30e3858a9ea2bf514a6659e01a/skill/drawio/SKILL.md)
- [skill/drawio/references/academic-diagram-style.md](https://github.com/SHALINS428/Codex-drawio-skill/blob/1f3acc7c002eab30e3858a9ea2bf514a6659e01a/skill/drawio/references/academic-diagram-style.md)
- [skill/drawio/references/figure-types.md](https://github.com/SHALINS428/Codex-drawio-skill/blob/1f3acc7c002eab30e3858a9ea2bf514a6659e01a/skill/drawio/references/figure-types.md)
- [skill/drawio/scripts/new-drawio-figure.ps1](https://github.com/SHALINS428/Codex-drawio-skill/blob/1f3acc7c002eab30e3858a9ea2bf514a6659e01a/skill/drawio/scripts/new-drawio-figure.ps1)
- [skill/drawio/scripts/export-drawio-png.ps1](https://github.com/SHALINS428/Codex-drawio-skill/blob/1f3acc7c002eab30e3858a9ea2bf514a6659e01a/skill/drawio/scripts/export-drawio-png.ps1)

### JMO808

- [LICENSE](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/LICENSE)
- [skills/drawio/SKILL.md](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/skills/drawio/SKILL.md)
- [scripts/diagram-builder.js](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/scripts/diagram-builder.js)
- [scripts/validate.js](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/scripts/validate.js)
- [scripts/validators/design-quality.js](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/scripts/validators/design-quality.js)
- [scripts/validators/network.js](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/scripts/validators/network.js)
- [scripts/validators/aws.js](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/scripts/validators/aws.js)
- [scripts/elk-layout.js](https://github.com/jmo808/drawio_plugin/blob/170c000af0b8212e5ff8a2d2dfeec6d332cc6c2e/scripts/elk-layout.js)

### lgazo

- [LICENSE.md](https://github.com/lgazo/drawio-mcp-server/blob/afbd4bedef50b117889d4c0f47692d311df5b71e/LICENSE.md)
- [packages/drawio-mcp-server/src/tools/edit-edge.ts](https://github.com/lgazo/drawio-mcp-server/blob/afbd4bedef50b117889d4c0f47692d311df5b71e/packages/drawio-mcp-server/src/tools/edit-edge.ts)
- [packages/drawio-mcp-server/src/tools/create-layer.ts](https://github.com/lgazo/drawio-mcp-server/blob/afbd4bedef50b117889d4c0f47692d311df5b71e/packages/drawio-mcp-server/src/tools/create-layer.ts)
- [packages/drawio-mcp-server/src/tools/create-page.ts](https://github.com/lgazo/drawio-mcp-server/blob/afbd4bedef50b117889d4c0f47692d311df5b71e/packages/drawio-mcp-server/src/tools/create-page.ts)
- [packages/drawio-mcp-server/src/tools/set-cell-parent.ts](https://github.com/lgazo/drawio-mcp-server/blob/afbd4bedef50b117889d4c0f47692d311df5b71e/packages/drawio-mcp-server/src/tools/set-cell-parent.ts)
- [packages/drawio-mcp-server/src/tools/get-shape-by-name.ts](https://github.com/lgazo/drawio-mcp-server/blob/afbd4bedef50b117889d4c0f47692d311df5b71e/packages/drawio-mcp-server/src/tools/get-shape-by-name.ts)
- [packages/drawio-mcp-plugin/src/drawio-tools.ts](https://github.com/lgazo/drawio-mcp-server/blob/afbd4bedef50b117889d4c0f47692d311df5b71e/packages/drawio-mcp-plugin/src/drawio-tools.ts)

### abossard

- [LICENSE](https://github.com/abossard/drawio-mcp/blob/9a1992ec610911b35433e0f7e7f69b8c8f512c3a/LICENSE)
- [src/index.ts](https://github.com/abossard/drawio-mcp/blob/9a1992ec610911b35433e0f7e7f69b8c8f512c3a/src/index.ts)
- [src/drawio.ts](https://github.com/abossard/drawio-mcp/blob/9a1992ec610911b35433e0f7e7f69b8c8f512c3a/src/drawio.ts)
- [src/sidecar.ts](https://github.com/abossard/drawio-mcp/blob/9a1992ec610911b35433e0f7e7f69b8c8f512c3a/src/sidecar.ts)
- [vscode-drawio-mcp-bridge/src/extension.ts](https://github.com/abossard/drawio-mcp/blob/9a1992ec610911b35433e0f7e7f69b8c8f512c3a/vscode-drawio-mcp-bridge/src/extension.ts)

### yohasacura

- [LICENSE](https://github.com/yohasacura/drawio-mcp/blob/036573d746e1720e121701dfe0b3b570c4895e2a/LICENSE)
- [src/drawio_mcp/server.py](https://github.com/yohasacura/drawio-mcp/blob/036573d746e1720e121701dfe0b3b570c4895e2a/src/drawio_mcp/server.py)
- [src/drawio_mcp/models.py](https://github.com/yohasacura/drawio-mcp/blob/036573d746e1720e121701dfe0b3b570c4895e2a/src/drawio_mcp/models.py)
- [src/drawio_mcp/styles.py](https://github.com/yohasacura/drawio-mcp/blob/036573d746e1720e121701dfe0b3b570c4895e2a/src/drawio_mcp/styles.py)
- [src/drawio_mcp/layout.py](https://github.com/yohasacura/drawio-mcp/blob/036573d746e1720e121701dfe0b3b570c4895e2a/src/drawio_mcp/layout.py)
- [src/drawio_mcp/layout_engine.py](https://github.com/yohasacura/drawio-mcp/blob/036573d746e1720e121701dfe0b3b570c4895e2a/src/drawio_mcp/layout_engine.py)
- [src/drawio_mcp/validation.py](https://github.com/yohasacura/drawio-mcp/blob/036573d746e1720e121701dfe0b3b570c4895e2a/src/drawio_mcp/validation.py)
