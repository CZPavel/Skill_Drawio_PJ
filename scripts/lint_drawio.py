"""Read-only, conservative QA of native draw.io XML. No renderer is simulated."""
import argparse
import base64
import html
import json
import math
from pathlib import Path
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zlib


def style(value):
    return dict(part.split('=', 1) for part in value.split(';') if '=' in part)


def number(value, default=0):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (ValueError, TypeError):
        return default


def pages(root):
    if root.tag == 'mxGraphModel':
        return [('page-1', root)]
    if root.tag != 'mxfile':
        raise ValueError('Expected mxfile or mxGraphModel')
    result = []
    for index, diagram in enumerate(root.findall('diagram')):
        model = diagram.find('mxGraphModel')
        if model is None:
            payload = (diagram.text or '').strip()
            if payload.startswith('<'):
                model = ET.fromstring(payload)
            else:
                model = ET.fromstring(urllib.parse.unquote(zlib.decompress(base64.b64decode(payload), -15).decode('utf-8')))
        if model.tag != 'mxGraphModel':
            raise ValueError('Diagram payload is not mxGraphModel')
        result.append((diagram.get('name') or diagram.get('id') or str(index + 1), model))
    if not result:
        raise ValueError('mxfile contains no diagrams')
    return result


def contrast(a, b):
    def lum(color):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', color or ''):
            return None
        rgb = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
        return sum(w*(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4) for w, v in zip((.2126, .7152, .0722), rgb))
    x, y = lum(a), lum(b)
    return None if x is None or y is None else (max(x, y)+.05)/(min(x, y)+.05)


def overlap(a, b):
    return min(a[0]+a[2], b[0]+b[2]) > max(a[0], b[0]) and min(a[1]+a[3], b[1]+b[3]) > max(a[1], b[1])


def label_text(label):
    """Block boundaries separate lines; explicit br pairs preserve empty lines."""
    if '<' not in label:
        return html.unescape(label)
    text = re.sub(r'<br\s*/?>', '\ue000', label, flags=re.I)
    text = re.sub(r'</?(?:div|p)\b[^>]*>', '\n', text, flags=re.I)
    text = re.sub('<[^>]+>', '', text)
    text = re.sub(r'\n[ \t\r\n]*', '\n', text).strip('\n')
    return html.unescape(text.replace('\ue000', '\n'))


def segment_rect(a, b, r):
    # Liang-Barsky clipping; includes border contact, deliberately conservative.
    lo, hi = 0., 1.
    for p, q in ((a[0]-b[0], a[0]-r[0]), (b[0]-a[0], r[0]+r[2]-a[0]),
                 (a[1]-b[1], a[1]-r[1]), (b[1]-a[1], r[1]+r[3]-a[1])):
        if p == 0:
            if q < 0:
                return False
        elif p < 0:
            lo = max(lo, q/p)
        else:
            hi = min(hi, q/p)
    return lo <= hi


def segments_intersect(a, b, c, d):
    def cross(p, q, r):
        return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    if max(min(a[0], b[0]), min(c[0], d[0])) > min(max(a[0], b[0]), max(c[0], d[0])) or max(min(a[1], b[1]), min(c[1], d[1])) > min(max(a[1], b[1]), max(c[1], d[1])):
        return False
    return cross(a,b,c)*cross(a,b,d) <= 0 and cross(c,d,a)*cross(c,d,b) <= 0


def lint(path, target_width_mm=None, min_font_pt=9):
    report = {'source': str(path), 'findings': [], 'metrics': {'pages': []}, 'coverage': {'text_measurement': 'estimated character widths, not browser font metrics', 'rendered_qa_required': True}}
    def add(severity, code, cells, message, page=None):
        report['findings'].append(dict(severity=severity, code=code, cells=cells, message=message, page=page))
    try:
        models = pages(ET.parse(path).getroot())
    except (ET.ParseError, ValueError, OSError, zlib.error) as exc:
        add('error', 'xml-invalid', [], str(exc))
        report['fatal'] = True
        return report
    for page, model in models:
        raw = model.find('root')
        if raw is None:
            add('error', 'root-missing', [], 'mxGraphModel has no root', page)
            continue
        cells = {}
        for item in raw:
            cell = item if item.tag == 'mxCell' else item.find('mxCell')
            if cell is None:
                continue
            attrs = dict(cell.attrib)
            if item is not cell:
                attrs['id'] = item.get('id') or attrs.get('id')
                attrs['value'] = item.get('label', item.get('value', attrs.get('value', '')))
            ident = attrs.get('id')
            if not ident:
                add('error', 'id-missing', [], 'Cell has no ID', page)
                continue
            if ident in cells:
                add('error', 'id-duplicate', [ident], 'Duplicate cell ID', page)
            cells[ident] = (attrs, cell.find('mxGeometry'))
        def ancestors(ident):
            seen = set()
            while ident in cells:
                ident = cells[ident][0].get('parent')
                if ident in seen:
                    break
                seen.add(ident)
            return seen
        for ident, (attrs, geo) in cells.items():
            for key in ('parent', 'source', 'target'):
                if attrs.get(key) and attrs[key] not in cells:
                    add('error', 'reference-dangling', [ident, attrs[key]], 'Missing '+key+' cell', page)
            if ident in ancestors(ident):
                add('error', 'parent-cycle', [ident], 'Parent hierarchy contains a cycle', page)
            if attrs.get('vertex') == '1' or attrs.get('edge') == '1':
                if geo is None:
                    add('error', 'geometry-missing', [ident], 'Visible cell has no geometry', page)
                else:
                    for element in geo.iter():
                        for key in ('x', 'y', 'width', 'height'):
                            if key in element.attrib:
                                try:
                                    valid = math.isfinite(float(element.get(key)))
                                except ValueError:
                                    valid = False
                                if not valid:
                                    add('error', 'geometry-number', [ident], 'Nonfinite or invalid geometry '+key, page)
        rects, resolving = {}, set()
        def rect(ident):
            if ident in rects:
                return rects[ident]
            if ident not in cells or ident in resolving:
                return None
            attrs, geo = cells[ident]
            if geo is not None and geo.get('relative') == '1' and cells.get(attrs.get('parent'), ({},None))[0].get('edge') == '1':
                return None  # Relative edge labels use path positions, not parent rectangles.
            resolving.add(ident)
            parent = rect(attrs.get('parent')) if attrs.get('parent') in cells else (0,0,0,0)
            resolving.remove(ident)
            if parent is None or (geo is None and attrs.get('vertex') == '1'):
                return None
            if geo is None:
                value = parent
            else:
                x, y = number(geo.get('x')), number(geo.get('y'))
                if geo.get('relative') == '1' and attrs.get('vertex') == '1':
                    x, y = x*parent[2], y*parent[3]
                offset = geo.find("mxPoint[@as='offset']")
                value = (parent[0]+x+(number(offset.get('x')) if offset is not None else 0), parent[1]+y+(number(offset.get('y')) if offset is not None else 0), number(geo.get('width')), number(geo.get('height')))
            rects[ident] = value
            return value
        nodes = {i: rect(i) for i, (a,g) in cells.items() if a.get('vertex') == '1'}
        for ident, value in nodes.items():
            if value is None:
                add('uncertain', 'node-geometry-unresolved', [ident], 'Node position cannot be resolved from parent rectangles (cycle, missing geometry or edge-relative label)', page)
        nodes = {i:r for i,r in nodes.items() if r is not None}
        fonts, paths, source_font_min = [], {}, []
        for ident, (attrs, geo) in cells.items():
            vertex, edge = attrs.get('vertex') == '1', attrs.get('edge') == '1'
            if not (vertex or edge):
                continue
            s = style(attrs.get('style', ''))
            if attrs.get('visible') == '0' or attrs.get('collapsed') == '1' or s.get('opacity') not in (None, '100'):
                add('uncertain','visibility-unresolved',[ident], 'Hidden/collapsed/transparent state requires rendered inspection; source geometry is still checked',page)
            for token in (('strokeColor', 'strokeWidth') + (('fillColor',) if vertex else ()) + (('fontColor','fontFamily','fontSize') if attrs.get('value') else ())):
                if token not in s:
                    add('warning', 'style-explicit', [ident], 'Set explicit '+token, page)
            if 'strokeWidth' in s and number(s['strokeWidth']) <= 0:
                add('warning', 'stroke-invisible', [ident], 'Stroke width is not positive', page)
            label = attrs.get('value', '')
            font = number(s.get('fontSize'), 12)
            # Inline HTML can override mxCell typography. Account for px, pt, em and %.
            inline = []
            for value, unit in re.findall(r'font-size\s*:\s*([\d.]+)\s*(px|pt|em|%)', label, re.I):
                n = float(value)
                inline.append(n*4/3 if unit.lower() == 'pt' else n*font if unit.lower() == 'em' else n*font/100 if unit == '%' else n)
            sizes = [font]+inline
            if label:
                fonts.extend(sizes)
                source_font_min.append(min(sizes))
            if vertex and ident in nodes:
                r = nodes[ident]
                if r[2] <= 0 or r[3] <= 0:
                    add('error', 'geometry-size', [ident], 'Node dimensions must be positive', page)
                parent = attrs.get('parent')
                if parent in nodes:
                    p = nodes[parent]
                    if r[0] < p[0] or r[1] < p[1] or r[0]+r[2] > p[0]+p[2] or r[1]+r[3] > p[1]+p[3]:
                        add('warning', 'container-overflow', [ident,parent], 'Child exceeds ancestor rectangle', page)
                if number(s.get('rotation')) or s.get('shape') not in (None, 'rectangle') or s.get('ellipse') == '1':
                    add('uncertain', 'shape-bounds', [ident], 'Collision checks use axis-aligned rectangle, not rendered shape', page)
                if label:
                    text = label_text(label)
                    padding = number(s.get('spacing'), 2)
                    available = max(1, r[2]-2*padding-number(s.get('spacingLeft'))-number(s.get('spacingRight')))
                    largest = max(sizes)
                    widths = [sum(.3 if c in ' il.,:;' else .85 if c in 'MW@' else .55 for c in line)*largest for line in text.splitlines() or ['']]
                    wrapped = sum(max(1, math.ceil(w/available)) for w in widths) if s.get('whiteSpace') == 'wrap' else len(widths)
                    if max(widths, default=0) > available and s.get('whiteSpace') != 'wrap':
                        add('warning','text-overflow-width-estimated',[ident], 'Estimated text width exceeds node interior',page)
                    if wrapped*largest*1.25 > r[3]-2*padding-number(s.get('spacingTop'))-number(s.get('spacingBottom')):
                        add('warning','text-overflow-height-estimated',[ident], 'Estimated text height exceeds node interior',page)
                    if '<' in label:
                        add('uncertain','html-text-estimated',[ident], 'Rich text, mixed fonts and CSS require rendered inspection; inline sizes included conservatively',page)
                    ratio = contrast(s.get('fontColor'), s.get('fillColor'))
                    if ratio is None:
                        add('uncertain','text-contrast-unknown',[ident], 'Text/background color cannot be resolved as opaque hex',page)
                    elif ratio < 4.5:
                        add('warning','text-contrast',[ident], f'Text contrast {ratio:.2f}:1 below 4.5:1',page)
                ratio = contrast(s.get('strokeColor'), s.get('fillColor'))
                if ratio is not None and ratio < 3:
                    add('warning','border-contrast',[ident], f'Border/fill contrast {ratio:.2f}:1 below 3:1',page)
            if edge:
                if label:
                    add('uncertain','edge-label-unresolved',[ident], 'Edge-label position/extent requires rendered export QA',page)
                origin = rect(attrs.get('parent')) or (0,0,0,0)
                def point(name):
                    p = geo.find("mxPoint[@as='"+name+"']") if geo is not None else None
                    return (number(p.get('x'))+origin[0], number(p.get('y'))+origin[1]) if p is not None else None
                start, end = point('sourcePoint'), point('targetPoint')
                if start is None or end is None or attrs.get('source') or attrs.get('target') or s.get('curved') == '1' or s.get('edgeStyle') not in (None, 'none'):
                    add('uncertain','edge-path-unresolved',[ident], 'Automatic/attached/routed path requires rendered export; source waypoints are not final segments',page)
                    continue
                mid = geo.findall("Array[@as='points']/mxPoint")
                points = [start]+[(number(p.get('x'))+origin[0], number(p.get('y'))+origin[1]) for p in mid]+[end]
                paths[ident] = points
                if any(a[0] != b[0] and a[1] != b[1] for a,b in zip(points,points[1:])):
                    add('warning','edge-nonorthogonal',[ident], 'Explicit polyline includes diagonal segment',page)
                if len(points)>1 and math.dist(points[-2],points[-1]) < 20:
                    add('warning','edge-terminal',[ident], 'Final explicit segment shorter than 20 source pixels',page)
                for node,r in nodes.items():
                    if node in ancestors(ident):
                        continue
                    if any(segment_rect(a,b,r) for a,b in zip(points,points[1:])):
                        add('warning','edge-node',[ident,node], 'Explicit edge intersects node rectangle or border',page)
        for i,(a,r) in enumerate(nodes.items()):
            for b,q in list(nodes.items())[i+1:]:
                if a not in ancestors(b) and b not in ancestors(a) and overlap(r,q):
                    add('warning','node-overlap',[a,b], 'Unrelated node rectangles overlap',page)
        for i,(a,p) in enumerate(paths.items()):
            for b,q in list(paths.items())[i+1:]:
                if any(segments_intersect(x,y,u,v) for x,y in zip(p,p[1:]) for u,v in zip(q,q[1:])):
                    add('warning','edge-edge',[a,b], 'Explicit edge segments intersect or overlap',page)
        all_points = [(r[0],r[1]) for r in nodes.values()]+[(r[0]+r[2],r[1]+r[3]) for r in nodes.values()]+[p for ps in paths.values() for p in ps]
        bounds = [min(p[0] for p in all_points), min(p[1] for p in all_points), max(p[0] for p in all_points),max(p[1] for p in all_points)] if all_points else [0,0,0,0]
        width,height = bounds[2]-bounds[0],bounds[3]-bounds[1]
        page_w,page_h = number(model.get('pageWidth')),number(model.get('pageHeight'))
        if bounds[0] < 0 or bounds[1] < 0 or (page_w and bounds[2]>page_w) or (page_h and bounds[3]>page_h):
            add('warning','canvas-bounds',[], 'Source bounds exceed nonnegative configured page rectangle',page)
        projected = min(fonts)*target_width_mm/width*72/25.4 if target_width_mm and width and fonts else None
        if projected is not None and projected < min_font_pt:
            add('warning','target-font-small',[], f'Estimated smallest font at target width: {projected:.2f} pt < {min_font_pt} pt',page)
        top_area = sum(r[2]*r[3] for i,r in nodes.items() if not any(a in nodes for a in ancestors(i)))
        report['metrics']['pages'].append(dict(page=page,nodes=len(nodes),edges=sum(a.get('edge')=='1' for a,g in cells.values()),explicit_paths=len(paths),bounds_px=bounds,width_px=width,height_px=height,aspect_ratio=width/height if height else None,font_min_px=min(fonts) if fonts else None,font_max_px=max(fonts) if fonts else None,projected_min_font_pt=projected,estimated_whitespace_fraction=max(0,1-top_area/(width*height)) if width*height else None))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file')
    parser.add_argument('--json', type=Path)
    parser.add_argument('--target-width-mm', type=float)
    parser.add_argument('--min-font-pt', type=float, default=9)
    args = parser.parse_args()
    if (args.target_width_mm is not None and args.target_width_mm <= 0) or args.min_font_pt <= 0:
        parser.error('Dimensions and minimum font must be positive')
    result = lint(args.file,args.target_width_mm,args.min_font_pt)
    payload = json.dumps(result,ensure_ascii=False,indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(payload+'\n',encoding='utf-8')
    print(payload)
    return 2 if result.get('fatal') else 1 if any(f['severity']=='error' for f in result['findings']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
