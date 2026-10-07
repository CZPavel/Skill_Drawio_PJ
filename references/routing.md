# Connectors and clearance

Start by placing connected blocks near each other in reading order. Move a block or change group order before adding a long detour. Prefer orthogonal connectors with few bends, consistent stroke and clear arrowheads. A crossing is not a junction: use a visible jump or explicit junction only when the notation calls for it.

Distinguish one-way data, bidirectional communication and undirected association. For the industrial palette, data blue solid, control amber solid and service slate dashed are useful conventions **only when stated in a legend/labels**. Do not imply actual field wiring from a conceptual relation.

An explicit port (`exitX/Y`, `entryX/Y`) is useful for a clear geometric intent, multiple edges or avoiding label interference; otherwise let the native router choose. Use at least ~20 source units for the final straight run, scaled with typography. Keep labels away from bends and arrowheads; white label backgrounds cannot excuse obscuring the entire short edge.

For obstacle-aware routing use external `libavoid` after sizing/placement, then inspect exported geometry. Native orthogonal routing alone is not obstacle-aware. ELK may propose positions for large graphs but cannot certify target composition or text readability.

Waypoints and label offsets are in the edge parent's coordinate frame. Edge parent is the nearest common ancestor of both terminals. Edges to a child legitimately cross the ancestor container boundary; do not treat that as an obstacle collision. A label/node bounding box check for a diamond, cylinder or stencil is conservative; actual outlines require rendering.

If routing is changed, save the changed native source and export from it. Never apply layout only during PNG export while delivering stale `.drawio` geometry.
