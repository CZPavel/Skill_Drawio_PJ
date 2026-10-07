# Context and execution efficiency

These are reproducible proxies, not measured API tokens or model-cost claims.
V0.1 entrypoint at commit 29b3964 had 5,070 characters/41 long lines. V0.2 has
approximately 4,700 characters/81 shorter lines; inspect the file for exact current
size. More lines do not mean more context. No minimum line count was imposed.

| Workflow | Loaded guidance | Candidates | Image exports | QA |
|---|---|---|---|---|
| Simple new diagram | SKILL + model/API + design (2 refs) | up to 3 | 1 SVG+PNG pass | source + PNG sight |
| Medium topology | above + routing + QA (4 refs) | up to 8 | 1; 2 if demonstrated repair | source + browser + sight |
| Complex graph | conditional refs only | up to 12 | selected only | FULL; at most 2 repairs |
| Existing diagram | SKILL + editing, other refs only as needed | no mandatory generation | affected pages | preserve native contract |

V0.1 entrypoint directed general reads of diagram-types, targets, design,
JGraph baseline, QA and coverage (6 refs), with routing/editing conditional.
V0.2 removes those unconditional reads. Typical FAST execution uses three script
invocations (build/layout report, source lint, combined SVG/PNG export) plus image
inspection. Browser audit and external libavoid each add one only when needed.
No renderer is called during candidate evaluation. In-memory font objects are
cached; tokens load once per process. There is no database or persistent cache.

The coordinate-free fixtures are the small-model acceptance proxy: an agent needs
to supply semantic IDs/content/groups/edges, not x/y, dimensions, most ports or
waypoints. Determinism and preservation are tested across all nine fixtures.
This is not an actual run of a smaller language model and does not measure its
semantic accuracy. New layouts can still need local repairs; FAST is a path for
clear simple diagrams, not permission to skip evidence of a visible defect.

Run `python scripts/benchmark_v02.py` for bounded offline candidates, or add
`--render` for selected Desktop/browser exports. `--mcp-root PATH` optionally uses
the external JGraph router. Benchmark layout_seconds are local observations and
should not be compared across different hosts as performance claims.


## V0.3 delta

The simple path still reads SKILL + model/API + design (two references), evaluates
at most 3/8/12 candidates in memory, exports the selected native once and performs
FAST sight checks. Routing reference is conditional. Engine recommendation and
FAST/FULL escalation are script decisions; the probe is explicit/session-only.
No new dependencies, persistent database or per-diagram network research.
FULL adds one browser audit; a justified routing repair adds an engine pass and
re-export. Fan-out is opt-in. Entry-point growth is tracked at release; character
counts are a context proxy, not measured tokenizer/API cost. Tier B may require
more context; there is no claim of equal automation for every diagram type.

Release entrypoint: V0.2 4701 characters; V0.3 4905 characters (+204, 4.3%). Counts use decoded text, not tokens.
