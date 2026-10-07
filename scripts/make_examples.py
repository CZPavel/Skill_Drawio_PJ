"""Reproduce the three curated PJ pilot compositions from matched benchmark prompts."""
import json
from pathlib import Path
from build_diagram import build

ROOT = Path(__file__).resolve().parents[1]


def examples():
    process = {
        "id": "process", "name": "Kontrola snímku", "profile": "document",
        "profile_overrides": {"canvas_width": 1500, "canvas_height": 650, "title": 36, "body": 32, "edge": 34},
        "nodes": [
            {"id": "receive", "title": "Přijmout\nsnímek", "x": 30, "y": 70, "width": 205, "shape": "terminal"},
            {"id": "exposure", "title": "Ověřit\nexpozici", "x": 305, "y": 70, "width": 205},
            {"id": "usable", "title": "Snímek\npoužitelný?", "x": 580, "y": 30, "width": 460, "shape": "decision", "role": "control", "padding": 8},
            {"id": "evaluate", "title": "Vyhodnotit\nmodel", "x": 1160, "y": 70, "width": 245},
            {"id": "save", "title": "Uložit\nvýsledek", "x": 1160, "y": 340, "width": 245, "role": "ok", "shape": "terminal"},
            {"id": "light", "title": "Upravit\nosvětlení", "x": 670, "y": 340, "width": 280, "role": "control"}
        ],
        "edges": [
            {"id": "p1", "source": "receive", "target": "exposure"},
            {"id": "p2", "source": "exposure", "target": "usable"},
            {"id": "p3", "source": "usable", "target": "evaluate", "label": "Ano", "label_offset": 26},
            {"id": "p4", "source": "evaluate", "target": "save", "style": {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0}},
            {"id": "p5", "source": "usable", "target": "light", "label": "Ne", "label_offset": -42, "role": "control", "style": {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0}},
            {"id": "p6", "source": "light", "target": "exposure", "role": "control", "points": [[407.5, 404]], "style": {"exitX": 0, "exitY": 0.5, "entryX": 0.5, "entryY": 1}}
        ]
    }
    topology = {
        "id": "topology", "name": "Koncepční topologie strojového vidění", "profile": "document",
        "profile_overrides": {"canvas_width": 1700, "canvas_height": 800, "title": 40, "body": 34, "edge": 34},
        "groups": [{"id": "cell", "title": "Výrobní pracoviště", "x": 24, "y": 24, "width": 1150, "height": 660}],
        "nodes": [
            {"id": "camera", "title": "Kamera", "body": "GigE snímky", "parent": "cell", "x": 32, "y": 230, "width": 245},
            {"id": "switch", "title": "Switch", "body": "Ethernet", "parent": "cell", "x": 385, "y": 230, "width": 245},
            {"id": "ipc", "title": "IPC", "body": "PEKAT Vision", "parent": "cell", "x": 738, "y": 230, "width": 350},
            {"id": "plc", "title": "PLC", "body": "Trigger a výsledek", "role": "control", "parent": "cell", "x": 385, "y": 455, "width": 350},
            {"id": "service", "title": "Servisní notebook", "role": "note", "parent": "cell", "x": 307.5, "y": 95, "width": 400},
            {"id": "mes", "title": "MES", "body": "Vyšší systém", "x": 1360, "y": 254, "width": 290, "role": "ok"}
        ],
        "edges": [
            {"id": "t1", "source": "camera", "target": "switch"},
            {"id": "t2", "source": "switch", "target": "ipc"},
            {"id": "t3", "source": "ipc", "target": "mes", "label": "Data", "role": "ok", "label_position": 0.5, "label_offset": 28},
            {"id": "t4", "source": "service", "target": "switch", "role": "note", "style": {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0, "dashed": 1, "startArrow": "block"}},
            {"id": "t5", "source": "plc", "target": "camera", "label": "HW trigger", "label_offset": 38, "role": "control", "points": [[154.5, 528]], "style": {"exitX": 0, "exitY": 0.5, "entryX": 0.5, "entryY": 1}},
            {"id": "t6", "source": "ipc", "target": "plc", "label": "Výsledek", "label_offset": 38, "role": "control", "points": [[913, 528]], "style": {"exitX": 0.5, "exitY": 1, "entryX": 1, "entryY": 0.5}}
        ]
    }
    training = {
        "id": "training", "name": "Od akvizice k provozu", "profile": "document",
        "profile_overrides": {"canvas_width": 1500, "canvas_height": 1100, "title": 40, "body": 36, "edge": 34},
        "groups": [], "nodes": [], "edges": []
    }
    content = [
        ("acquisition", "Akvizice", "data", [("optics", "Optika", "Zorné pole, pracovní vzdálenost a hloubka ostrosti."), ("lighting", "Světlo", "Stabilní osvětlení a krátká expozice potlačí rozmazání.")]),
        ("evaluation", "Vyhodnocení", "control", [("dataset", "Dataset", "Reprezentativní OK/NOK příklady a nezávislá validační sada."), ("model", "Model", "Prah rozhodnutí vychází z měřených chyb na validaci.")]),
        ("operation", "Provoz", "ok", [("integration", "Integrace", "PLC dostává výsledek i stav připravenosti."), ("diagnostics", "Diagnostika", "Uchovat snímek, čas a verzi modelu pro dohledání.")])
    ]
    for index, (identifier, title, role, cards) in enumerate(content):
        training["groups"].append({"id": identifier, "title": title, "role": role, "x": 24 + index * 500, "y": 24, "width": 430, "height": 710})
        y = 94
        for cid, ctitle, body in cards:
            training["nodes"].append({"id": cid, "title": ctitle, "body": body, "role": role, "parent": identifier, "x": 26, "y": y, "width": 378})
            y += 298
    training["edges"] = [{"id": "g1", "source": "acquisition", "target": "evaluation"}, {"id": "g2", "source": "evaluation", "target": "operation"}]
    return {"process": process, "topology": topology, "dense-training": training}


if __name__ == "__main__":
    for name, model in examples().items():
        directory = ROOT / "examples" / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "model.json").write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        build(model, directory / f"{name}.drawio")
