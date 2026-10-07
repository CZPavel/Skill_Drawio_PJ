# Design decisions

1. **Keep JGraph as the engine.** Native mxGraph format and Desktop exports avoid
   maintaining a competing renderer. Layout/routing support is invoked externally.
2. **Replace fixed final boxes with content sizing.** Measured title/body text
   determines height; width is selected for role and target. A grid only aligns.
3. **Judge text at insertion scale.** Canvas font values alone are misleading;
   derive projected points from cropped export width and actual physical size.
4. **Mermaid is optional.** It is efficient for standard structure, while native
   XML better controls final geometry, technical shapes and heterogeneous cards.
5. **ELK proposes placement; libavoid routes.** Neither establishes semantic
   correctness or professional composition. Persist revised source before export.
6. **Lint and render answer different questions.** Source lint marks unresolved
   automatic routes/HTML. Rendered checks and sight remain acceptance requirements.
7. **Document and slide variants may differ.** Preserve logical inventory, adapt
   density and reading scale. Do not promise a single composition suits all media.
8. **Targeted edits preserve intent.** No inferred domain correction, automatic
   edge deletion or full regeneration for one label/connector.
9. **Original implementation, no vendored upstream code.** This keeps license and
   maintenance scope clear; separately installed tools retain their own licenses.
10. **Benchmark evidence has a narrow scope.** Matched three-task pilot with an
    independent official workflow can demonstrate improvements on those cases,
    not universal superiority across future tasks or models.
11. **One local authoring skill when requested.** Canonical name is `skill-drawio-pj`.
    V0.2 replaces older local instructions on this workstation by explicit user
    request; standalone official MCP/renderer remains. The portable installer
    never removes unrelated skills automatically.

12. **Meaning before geometry.** Minimal IR and bounded candidates remove ordinary
    coordinate/port bookkeeping; explicit native geometry remains available.
13. **Transparent heuristics.** Critical collisions and unreadable projection dominate
    softer aspect/length/whitespace costs. Compare only the same semantic graph.
14. **One selected render.** Internal candidates, FAST without Chromium only for clear simple routes, one repair;
    FULL adds rendered paths and permits two repairs.
15. **No sync infrastructure.** Agents365 reconcile/filtered views are research,
    not claimed features of this small layer.


16. **Anchoring is semantic policy.** Floating ordinary relations, side-constrained
    processes, fixed meaningful interfaces. Native explicit styles override defaults.
17. **Alternative engines.** Libavoid preserves placement; ELK can move it. Verified
    capabilities gate recommendation; no automatic ELK+libavoid double pass.
18. **Local jumps only.** One/two estimated crossing pairs may select a secondary
    edge; ambiguity/density escalates instead of adding jumps to all edges.
19. **Synthetic helpers are not systems.** Explicit eligible fan-out only, metadata
    preserves logical source and inventory. Reject fixed-source or marker semantics.
20. **Tiered claims.** Tier A deterministic support; Tier B native/JGraph assistance.
21. **Post-routing evidence.** Browser metrics report actual exported paths with
    rectangle/sampling limits. Unknown curved bend metrics remain null, not zero.
