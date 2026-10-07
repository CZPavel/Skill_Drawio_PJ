"""Read-only extraction of dominant explicit native styles; no inferred theme."""
import argparse
from collections import Counter
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from lint_drawio import pages, style

VERTEX_KEYS = ('fontFamily', 'fontSize', 'fontColor', 'fillColor', 'strokeColor', 'strokeWidth', 'rounded', 'arcSize')
EDGE_KEYS = ('strokeColor', 'strokeWidth', 'edgeStyle', 'endArrow', 'dashed', 'jumpStyle', 'jumpSize')


def extract_style(path):
    counts = {'vertex': {}, 'edge': {}}
    cells = {'vertex': 0, 'edge': 0}
    for _, model in pages(ET.parse(path).getroot()):
        for cell in model.iter('mxCell'):
            kind = 'edge' if cell.get('edge') == '1' else 'vertex' if cell.get('vertex') == '1' else None
            if kind is None:
                continue
            cells[kind] += 1
            values = style(cell.get('style', ''))
            for key in EDGE_KEYS if kind == 'edge' else VERTEX_KEYS:
                if key in values:
                    counts[kind].setdefault(key, Counter())[values[key]] += 1
    dominant = {kind: {key: sorted(values, key=lambda v: (-values[v], v))[0]
                       for key, values in sorted(keys.items())} for kind, keys in counts.items()}
    return {'vertex_style': dominant['vertex'], 'edge_style': dominant['edge'],
            'coverage': {'cells': cells, 'explicit_properties_only': True,
                         'note': 'Frequency per property; ties use lexical order. HTML label CSS and inherited styles are not inferred.'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.resolve() == args.source.resolve():
        parser.error('Output must not overwrite the native source')
    result = json.dumps(extract_style(args.source), ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(result, encoding='utf-8')
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
