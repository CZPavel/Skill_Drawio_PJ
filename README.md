# Skill_Drawio_PJ V0.3

Profesionální editovatelné diagramy v draw.io: **content-driven sizing + target-aware layout + rendered visual QA**.

Nezávislý komunitní projekt, nikoli oficiální produkt JGraph/draw.io. Používá nativní
`.drawio` a externí oficiální engine. Vznikl kvůli praktickým vadám automatických
schémat: stejné čtvercové boxy, malé písmo v dokumentu, nevyužitá šířka, složité
objížďky a slabé ohraničení. Zdrojový `.drawio` se zachovává vedle exportů.

## Instalace pro Codex

```powershell
git clone https://github.com/CZPavel/Skill_Drawio_PJ.git
cd Skill_Drawio_PJ
python -m pip install -r requirements.txt
.\install.ps1
```

Výchozí lokální instalace: `$CODEX_HOME/skills/skill-drawio-pj`, jinak
`$USERPROFILE/.codex/skills/skill-drawio-pj`, podle prostředí použitého při vývoji.
Aktuální [oficiální dokumentace](https://learn.chatgpt.com/docs/build-skills)
uvádí také uživatelské `~/.agents/skills`; pro tento discovery root použijte
`.\install.ps1 -SkillsRoot "$env:USERPROFILE\.agents\skills"`. Nevytvářejte dvě
kopie stejného skillu v současně skenovaných kořenech. Aktualizace spravované
instalace: `git pull --ff-only`, poté `.\install.ps1 -Update` se stejným kořenem.
Instalátor jiné skilly automaticky nemaže; nahrazení starších instrukcí je samostatný explicitní krok. V novém chatu vyvolejte **`$skill-drawio-pj`**.
Instalace souborů není důkazem automatického výběru skillu v již otevřeném chatu.
`npx skills` není pro tuto instalaci nutný; nepředpokládáme jeho podporu konkrétním hostem.

## Požadavky a použití

Python 3.10+, Pillow, draw.io Desktop pro SVG/PNG/PDF export. Technický pilot byl
ověřen s Desktop 31.7.0 na Windows. Oficiální MCP je volitelný: page editing,
shape search, Mermaid/ELK/libavoid zůstávají schopnostmi externího JGraph toolingu.
Skill obsahuje postupy pro blokové a procesní diagramy, rozhodování, topologie,
architektury/deployment, data flow, swimlane, comparison a screenshot callouts.
Je to univerzální pracovní postup; pomocný JSON builder má záměrně užší rozsah.

Příklady zadání:

> Použij $skill-drawio-pj. Nakresli kameru, switch, IPC a MES pro Word na šířku 160 mm. Odděl data, trigger a servis. Zachovej editovatelný zdroj a proveď vizuální QA.

> Použij $skill-drawio-pj. Uprav v existujícím .drawio pouze routing dvou hran. Zachovej ostatní IDs, stránky, vrstvy a obsah.

> Použij $skill-drawio-pj. Připrav document a presentation variantu stejného procesu. Pokud by písmo bylo malé, rozděl přehled a detail.

Profily: document, presentation (16:9), a4-portrait, a4-landscape, standalone.
Tokeny jsou parametrizovatelné; jejich hodnoty nejsou náhradou kontroly měřítka.

```powershell
python scripts/build_diagram.py examples/process/model.json process.drawio
python scripts/lint_drawio.py process.drawio --target-width-mm 160 --json process.qa.json
python scripts/export_drawio.py process.drawio --formats svg png --output-dir previews
```

Volitelná kontrola skutečného SVG v browseru:

```powershell
npm ci
npx playwright install chromium
node scripts/audit_svg.cjs previews/process.svg --json previews/process.svg.qa.json --target-width-mm 160
```

Pro tuto kontrolu také z **instalovaného skillu** spusťte `.\install.ps1 -Update -WithRenderedQa`.
Instaluje Node závislosti do kořene instalovaného skillu a Chromium do cache.
Samotné `npm ci` v klonu neinstaluje závislosti do kopie skillu. Python/Pillow
musí být dostupné v interpreteru, kterým se pomocné skripty spouštějí.

FAST QA: source lint → SVG/PNG → vizuální kontrola. FULL přidává browser audit.
Při nalezené vadě následuje cílená oprava a nový export. Při vložení do Word/PPT je nutné vyrenderovat výsledný
dokument/snímek; samostatný preview tuto kontrolu neprokazuje. Přesné automatické
pokrytí a limity: [native QA](references/qa-coverage.md), [rendered QA](references/rendered-qa.md).

## Ukázky a srovnání

Tři piloty: proces, průmyslová topologie, hustší výuková ilustrace. Nativní zdroje
a authoring JSON: [examples](examples). Výstupy proti nezávislému oficiálnímu
workflow, metriky a omezení: [BENCHMARK](docs/BENCHMARK.md).

![Proces: oficiální workflow a PJ](benchmark/process-comparison.png)
![Topologie: oficiální workflow a PJ](benchmark/topology-comparison.png)
![Výuková ilustrace: oficiální workflow a PJ](benchmark/dense-training-comparison.png)

Rešerše osmi projektů s pinned verzemi a licencemi:
[SOURCE_COMPARISON](docs/SOURCE_COMPARISON.md). Architektura a rozhodnutí:
[ARCHITECTURE](docs/ARCHITECTURE.md), [DESIGN_DECISIONS](docs/DESIGN_DECISIONS.md).
Zdroje inspirovaly zásady; upstream kód ani assets nejsou vendored.

## Ověření a limity

```powershell
python -m unittest discover -s tests -v
npm run test:svg
```

CI ověřuje pomocné nástroje a rendered SVG fixtures. Desktop export a vizuální
posouzení pilotů jsou lokální runtime evidence, nikoli automatický důkaz Office
kompatibility. Linter umí přiznat `uncertain`; exit 0 není vizuální přejímka.
Nepodporované tvary, průhlednosti, math text, vendor assets nebo nestandardní
metadata vyžadují cílenou kontrolu. Benchmark není obecná garance kvality.

MIT pro vlastní obsah; externí závislosti viz [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).

## Nové ve V0.2

Model zadává významový JSON bez souřadnic; nástroje změří text, porovnají několik
rozložení a vyberou porty. Původní JSON s x/y zůstává podporovaný.

```powershell
python scripts/build_diagram.py examples/ir/process-lr.json process.drawio --report layout.json
python scripts/layout_diagram.py --help
python scripts/extract_style.py --help
python scripts/qa_office.py --help
```

IR: [model/API](references/model-api.md). Úspornost: [EFFICIENCY](docs/EFFICIENCY.md).
Změny: [CHANGELOG](CHANGELOG.md). Agents365 inspirovalo oddělení významu/geometrie,
orientační kandidáty, skóre a omezený repair loop; jeho kód nebyl převzat.


## V0.3 routing update

New semantic diagrams choose floating/side/fixed anchoring deterministically.
Explicit technical ports are validated; existing native documents keep manual
routing. Local crossing pairs choose secondary-edge jumps; dense conflicts request
routing repair. Reports declare FAST/FULL and recommend one appropriate engine.

Explicit diagnostics (once when needed):
`python scripts/probe_drawio.py --mcp-root PATH_TO_OFFICIAL_PACKAGE --json capabilities.json`.
Pass the resulting object as optional `routing_capabilities` in semantic IR for a
verified routing recommendation. No diagnostic runs during ordinary generation.
ELK presets use the installed official interface; compact is currently a limited
alias, not custom tuning. ELK can move nodes and refuses changed fixed attachments.

Optional fan-out: `python scripts/fanout_junction.py input.drawio output.drawio --source-id ipc`.
Only >=3 same-style sibling forward relations qualify; fixed source interfaces and
source markers are rejected. The helper carries synthetic metadata and preserves
logical inventory. Follow with FULL QA; it does not represent electrical contact.

See [V0.3 review](docs/V03_CONSISTENCY_REVIEW.md), [routing](references/routing.md),
[benchmark](docs/BENCHMARK.md) and [baseline capabilities](references/jgraph-baseline.md).
