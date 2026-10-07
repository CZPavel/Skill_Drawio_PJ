# Connector and routing policy

For newly generated semantic diagrams, `connector_policy.py` is authoritative.
Imported native XML preserves explicit ports, points and routing unless reroute/
polish is requested. Never regenerate an arbitrary imported file through IR.

## Anchoring

- **floating**: ordinary architecture/network relationship. Omit exitX/exitY/
  entryX/entryY; native router chooses perimeter attachments.
- **side**: process/decision main flow, LR right to left, TB bottom to top.
  `sourcePortConstraint=east;targetPortConstraint=west` (or south/north) constrains
  sides without midpoint coordinates. Branches/retry can use other sides.
- **fixed**: meaningful technical port/interface or explicitly necessary stable
  point. Use exitX/Y and entryX/Y plus perimeter flags; validate boundary points.
  Interior attachments require explicit reason/opt-in. Shape perimeter projection
  differs from rectangle coordinates, so inspect nonrectangular shapes.

Use semantic `connector_mode` and `ports` hints; native style overrides remain
available. Exact contract and examples are in [model/API](model-api.md). No model
reasoning is needed to choose routine attributes. Explicit modes take precedence.
Existing coordinate JSON retains its documented legacy defaults for compatibility;
that is not the policy for new semantic input or arbitrary imported diagrams.

## Engine choice

1. Sparse clear routes: native orthogonal routing.
2. Deliberately placed topology/architecture with edge-node conflicts: libavoid,
   preserving node geometry. Use only a locally verified available capability.
3. Movable hierarchical/process placement with placement/routing problems: an
   official ELK preset may move nodes. Never use it when placement carries meaning.
4. No suitable verified engine: local composition repair and disclose limitation.

ELK and libavoid are alternatives. A second engine pass requires rendered evidence
of a concrete remaining defect and measured improvement, not a default chain.
`probe_drawio.py` is an explicit/session diagnostic; do not run it for each graph.
See [JGraph baseline](jgraph-baseline.md) for upstream vs local evidence and commands.
No engine is bundled, forked or reimplemented.

## Crossings, hierarchy and order

A crossing is not a junction. Zero crossings: no automatic jump. One or two local
crossing pairs: select the secondary control/service/exception edge. If priority
is ambiguous, flag review instead of guessing. More crossings: repair placement/
routing instead of broad jumps. A jump never certifies a clear final route.
Main flow should remain optically clean; secondary paths use restrained weight/
color/dashes. Preserve explicit styles and native paint order on imported diagrams.
New generated secondary connectors are painted behind main flow and foreground nodes;
keep all connectors clear of text and unintended node interiors.

Retry/feedback uses an outer corridor and is exempt from ordinary backward-edge
penalties. The estimated corridor is not a guaranteed native route. Preserve edge
conditions, labels and arrowheads. Keep labels off bends/arrowheads and reserve
space before adding offsets. White label backgrounds do not excuse hidden text.

Waypoint coordinates are in the edge parent's frame; edge parent is the nearest
common ancestor. Crossing an ancestor boundary to reach its child is legitimate.
Bounding rectangles overestimate diamonds/cylinders/stencils. Rendered review is
required for actual outlines and endpoint behavior.

Optional fan-out helpers are explicit, synthetic routing aids, never devices.
Keep logical original source/edge identity in metadata; exclude helpers from semantic
inventory. Use only eligible same-direction fan-out, not every branch.

## QA escalation

Layout reports decide FAST/FULL: unresolved edge-node/label flags, crossing/jump
insertion, or libavoid/ELK repair requires rendered browser QA plus PNG sight.
Simple clear native diagrams retain FAST. Candidate scores are cheap estimates.
FULL records post-routing SVG crossings, bends, length, foreign-node/label bounds
and projected font; sampled curves/jumps remain approximate. Inspect final arrowheads
and branch identity. Save adopted native output first, then export that source.


Opt-in helper command: `python scripts/fanout_junction.py input.drawio output.drawio --source-id ipc --direction LR`.
Supports one uncompressed page, sibling terminals, >=3 identical connector styles,
and sufficient forward space. Rejects fixed source/target coordinates, incompatible side constraints, source arrow markers,
feedback and incompatible styles. It preserves original input and logical inventory;
rerender and inspect final fan-out. Native helper/trunk carry pjSyntheticRoutingHelper.


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
