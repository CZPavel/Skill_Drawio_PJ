# V0.3 consistency review

## Before implementation (V0.2 at 6bdd807)

Reviewed entrypoint, routing/design/archetype/JGraph/QA/model references, layout,
score, builder, external router, source/browser audits and architecture/decisions/
efficiency/source comparison. Existing archived benchmark descriptions remain
historical evidence; active instructions must use the policy below.

| Conflict | Authoritative V0.3 decision | Replacement |
|---|---|---|
| Optional explicit points vs universal facing midpoint and builder right/left defaults | New semantic generation chooses floating/side/fixed; fixed needs explicit intent | Remove unconditional coordinates from semantic policy; retain legacy coordinate behavior |
| Local jump advice vs jumpStyle added to every edge after any crossing | Only selected crossing edge; ambiguous or dense crossings require repair/review | Replace blanket loop with pair-aware policy |
| Desktop libavoid unsupported finding vs upstream capability | Probe actual installed version; historical observation is not universal | Separate upstream declaration, current local probe and fallback |
| ELK/libavoid sequence implicit | Alternatives; ELK can move nodes and requires movable placement | Explicit deterministic strategy; no automatic double pass |
| FAST browser optional despite route/label uncertainty | Report-driven escalation to FULL | FAST only for simple clear cases; repair/jump/critical uncertainty forces rendered QA |
| Generic archetypes imply equal automation | Tier A direct support; Tier B assisted composition | Bound capability claims in archetype reference |
| Existing diagrams vs new generation optimizer | Imported XML preserves user points/geometry unless reroute requested | Keep creation policy out of arbitrary native edits |
| Helpers could count as devices | Synthetic routing helpers must be excluded from semantic inventory | Explicit helper metadata and logical-edge identity; no implied hardware |

Design additions use existing palette and sizing: one abstraction level, consistent
shape/label grammar, restrained semantic colors, legend recommendation thresholds,
spacing and optical hierarchy. No automatic rewriting of specialist user labels.

## Final audit

Completed against final code, active references and generated benchmark evidence.

| Conflict | Final check |
|---|---|
| A floating vs fixed defaults | Semantic generation emits archetype modes; legacy coordinate input alone retains legacy defaults. Tests cover both. |
| B sparse vs blanket jumps | Pair-aware policy selects only eligible secondary edges; dense/ambiguous cases require review. One-crossing native fixture has exactly one jump. |
| C engine declaration vs runtime | Desktop 31.7.0 libavoid CLI is unsupported; external 1.6.3 libavoid and ELK are verified separately. Side bridge limitation is explicit and guarded, including compressed XML. |
| D alternatives vs chained engines | Strategy recommends one engine; benchmark executes at most one. ELK presets expose supported direction only. |
| E FAST vs unresolved findings | Report escalates uncertainty/repair to FULL; SVG metrics are post-routing and separate from candidate estimates. Unknown curves stay null. |
| F imported geometry vs creation optimizer | New semantic generation can compose; arbitrary imported XML is not regenerated. Routing/layout are explicit separate-output actions. Fixed intent is checked. |
| G helper vs semantic device | Opt-in bus node/trunk are synthetic and excluded from inventory; logical source IDs preserve original relations. Six benchmark inventories match. |

Independent reviewer reproduced the repaired failures: explicit side precedence,
fixed-port ELK rejection, compressed side guards, incompatible bus rejection,
backward ranking and SVG path normalization. Final local Python/SVG/package
checks pass. Rendered decision and fan-out corrections were inspected after
adoption. Dense topology still has a crossing; this release makes no universal
optimal-routing or automatic perfection claim. Archived V0.1/V0.2 measurements
remain historical, not active policy.
