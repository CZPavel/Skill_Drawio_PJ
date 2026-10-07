# Choose the visual grammar

| Archetype | Composition and semantic checks |
|---|---|
| technical-block | functional blocks, explicit interfaces, dominant signal direction; distinguish device/function/data |
| process-flow | action verbs, one dominant flow; wrap to a second row only if reading order remains obvious |
| decision-flow | one condition per diamond, explicit alternatives and retry/end states; reserve branch corridors |
| network-topology | sources → transport → processing → higher systems; service/control around main path; distinguish association vs directed data |
| architecture/deployment | real boundaries with parent-child hierarchy; external systems outside; name abstraction level and deployment assumptions |
| data-flow | name payloads and producers/consumers, don't imply temporal execution from spatial order |
| swimlane | lane = actor/responsibility, stage axis separate; connections cross boundaries intentionally; keep headers clear |
| comparison | panels/matrix with matched criteria; independent cards need no decorative arrows |
| annotated-ui | retain screenshot aspect/provenance, numbered callouts outside important UI, no invented interaction state |
| sequence | lifelines/messages with time direction; native shapes or editable Mermaid conversion; don't repurpose as deployment |

Shared tokens do not imply shared geometry. Use native electrical/network/cloud/BPMN symbols when notation matters; a rectangle labeled PLC may be perfectly adequate in a conceptual block diagram. Search shapes only when domain symbols improve understanding. A vendor icon does not certify device capability, protocol compatibility or physical wiring.

For dense training material start with overview + subsystem detail. Use separate pages when one reading scale cannot preserve important detail. Maintain an inventory of nodes/edges/branch conditions to prevent semantic loss during redesign.
