# Inspect, edit, resize, restyle, reroute, polish, repair

Inspect first: page names/IDs, compressed/uncompressed form, layers, hidden cells, groups, cell IDs and terminal topology. Identify the smallest affected scope. For a single broken edge, preserve all other geometry and IDs; for a global style change, update the intended tokens/styles without changing meaning. Do not recreate the whole diagram through the JSON creation helper.

Use official page tools if available, or an XML parser preserving unknown attributes/elements. Decode compressed page text (base64 → raw DEFLATE → URI decode) when necessary; preserve other pages. Check source/target and parent IDs before and after. Wrappers can own IDs and labels. A group resize can change child-relative positions; verify absolute placement and common-ancestor edge coordinates. Generic flattening is not a lossless round trip.

Read-only inspect/lint must not alter styles as a temporary highlight. Keep a practical rollback path through Git or a single requested working copy. On restyle preserve user semantics and intentional exceptions; never automatically remove edges based on guessed domain roles.

Polish pass: alignment, role-consistent spacing, text fit, weak boundaries, label offsets, needless bends, whitespace. Restrict changes to the agreed scope. Run affected-page lint/export/visual QA, then synchronize all delivered exports from final source. Do not claim an exporter preserves unsupported metadata until round-trip inspected.
