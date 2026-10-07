# Content, sizing and visual system

Central defaults: `assets/design-tokens.json`; select profile before using values. They are starting values, not universal typography or a corporate standard. Override for actual media. Default palette: blue data/devices, amber control/decisions, green operational result, slate service/notes, red risks. Pair color with wording, shape or line style.

Measure a title in the selected bold font and body in the selected regular font. The optional helper uses Pillow font advances, wraps at spaces and preserves meaningful paragraph breaks. Height = title lines × title line height + body lines × body line height + title/body gap + padding. Browser-rendered HTML may differ, so measurement remains a sizing aid. Long unbreakable identifiers require wider boxes or deliberately chosen breaks; never silently clip them. The helper fails instead of truncating.

Choose width from the available surface, role and longest meaningful phrase. A short device label and an explanatory card should not inherit identical geometry. Prefer wider rectangles, align shared baselines and comparable role heights; diamonds need substantially more width/height because the text fits in the central region. A group needs a separate header band and inner clearance (default 28 units). Real parent-child coordinates establish containment.

Use one font family and restrained title/body hierarchy. Short labels may be centered; paragraphs align left/top. Explicitly set fillColor, strokeColor, strokeWidth, fontColor and fontFamily. Do not use a shadow as a substitute for a visible boundary. Target text/fill ratio >=4.5; essential stroke/background and connector/background >=3. Ratios apply to actual adjacent colors, not just white. Gradients, opacity, images and dark themes need rendered review.

Layout sequence: content → target → size → place → route → style → inspect. Prefer an obvious dominant reading direction. Use grid snapping for alignment, not fixed width. Secondary paths belong near the relevant branch and may use perimeter corridors. Avoid high empty boxes, narrow centered compositions, paragraph text floating in a tall box, unnecessary bends and large whitespace introduced solely for a detour.

When a readable layout no longer fits, remove redundant wording with semantic care, widen within the target, split overview/detail or create separate document/slide variants. Do not turn independent principles into a sequence. Preserve all required exceptions and record meaningful editorial changes.

## Deterministic width selection

Semantic layout measures a small set of widths and trades height against target
aspect/available width. It never clips text or shrinks font to hide overflow.
Explicit dimensions take precedence; insufficient containers need review.
Presets merge into base tokens. Extracted styles are proposals, not design approval.
