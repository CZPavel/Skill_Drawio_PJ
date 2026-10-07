# Target-aware composition

Compute usable surface from the actual section/slide, excluding margins, title/footer and nearby explanation. Defaults are assumptions to disclose, not verified user document geometry.

| Profile | Intended surface | Acceptance |
|---|---|---|
| document | 160 mm text width, flexible cropped height | body/edge text usually >=9 pt at insertion, deliberate hierarchy |
| presentation | 16:9 slide, diagram area below title | body/edge text usually >=18 pt on slide, low density, inspect whole slide |
| a4-portrait | 170 mm usable width, page height constrained | respect print margins; split tall detail |
| a4-landscape | 257 mm usable width | preserve enough space for caption/context |
| standalone | user-selected pixel size or aspect | establish intended viewing scale; no invented physical size |

Projected font size: `font_pt = font_source_units × inserted_width_mm × 72 / (25.4 × exported_viewBox_width)`. Use the **cropped export viewBox** including border, not just pageWidth. If height also limits insertion, use the smaller width/height scale. Never stretch axes independently.

For Word, use available text width and a reasonable height; keep caption and explanation together. For PowerPoint, simplify content before shrinking. A 16:9 canvas does not require filling every pixel: composition must fit its usable area without huge decorative whitespace. If a wide process has a low aspect ratio, embed it as one clear band with supporting context on the slide, or change its composition for the slide.

Same logical information may yield `name-document.drawio` and `name-slide.drawio`. Preserve IDs/semantic inventory where practical and compare nodes/edges/conditions, not coordinates.

After insertion, render the actual Word/PPT file and inspect the complete page/slide at normal scale. Verify the current export was embedded, original replaced graphics removed, surrounding native objects legible and no title/footer collision. Use the documents/presentations workflow available in that environment when producing those artifacts. Identify the renderer honestly; a substitute renderer is not Microsoft Office verification.

## Optional Office insertion fixture

`python scripts/qa_office.py export.png fresh-dir --target document --render`
creates a DOCX (presentation creates PPTX), then attempts available LibreOffice.
Libraries/renderer are optional; missing renderer remains explicitly unverified.
Inspect the rendered page/slide. This helper does not claim Microsoft Office QA.
