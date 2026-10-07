"""Transparent source-geometry scoring; native routing still requires rendered QA."""
import math
from itertools import combinations
from lint_drawio import overlap, segment_rect, segments_intersect


def absolute_boxes(model):
    items = {n['id']: n for n in model.get('groups', []) + model.get('nodes', [])}
    result = {}
    def resolve(key):
        if key not in result:
            n = items[key]
            p = resolve(n['parent']) if n.get('parent', '1') != '1' else (0, 0, 0, 0)
            result[key] = (p[0]+n['x'], p[1]+n['y'], n['width'], n['height'])
        return result[key]
    for key in items:
        resolve(key)
    return result


def edge_path(edge, boxes):
    a, b = boxes[edge['source']], boxes[edge['target']]
    s = edge.get('style', {})
    from connector_policy import facing_sides, POINTS, SIDES
    source_side,target_side = facing_sides(a,b)
    inverse = {v:k for k,v in SIDES.items()}
    source_side = inverse.get(s.get('sourcePortConstraint'),source_side)
    target_side = inverse.get(s.get('targetPortConstraint'),target_side)
    sx,sy = POINTS[source_side]; tx,ty = POINTS[target_side]
    if not edge.get('connector_mode') and not s:
        sx,sy,tx,ty = 1,.5,0,.5
    start = (a[0]+a[2]*float(s.get('exitX', sx)), a[1]+a[3]*float(s.get('exitY', sy)))
    end = (b[0]+b[2]*float(s.get('entryX', tx)), b[1]+b[3]*float(s.get('entryY', ty)))
    if edge.get('type') in ('retry','feedback','backward') and edge.get('connector_mode') == 'side':
        if source_side == target_side == 'top':
            corridor = min(box[1] for box in boxes.values())-32
            return [start,(start[0],corridor),(end[0],corridor),end]
        if source_side == target_side == 'left':
            corridor = min(box[0] for box in boxes.values())-32
            return [start,(corridor,start[1]),(corridor,end[1]),end]
    # A proxy for native orthogonal routing, never serialized as authoritative waypoints.
    if start[0] == end[0] or start[1] == end[1]:
        return [start, end]
    if float(s.get('exitX',sx)) in (0, 1):
        mid = (start[0]+end[0])/2
        return [start, (mid, start[1]), (mid, end[1]), end]
    mid = (start[1]+end[1])/2
    return [start, (start[0], mid), (end[0], mid), end]


def score_layout(model, profile=None):
    from build_diagram import effective_profile
    profile = profile or effective_profile(model)
    boxes = absolute_boxes(model)
    nodes = model.get('nodes', [])
    top = [n for n in model.get('groups', [])+nodes if n.get('parent', '1') == '1']
    width = max((n['x']+n['width'] for n in top), default=1)-min((n['x'] for n in top), default=0)
    height = max((n['y']+n['height'] for n in top), default=1)-min((n['y'] for n in top), default=0)
    width, height = max(width, 1), max(height, 1)
    paths = [(e, edge_path(e, boxes)) for e in model.get('edges', [])]
    collisions = sum(overlap(boxes[a['id']], boxes[b['id']]) for a,b in combinations(nodes, 2))
    edge_nodes = sum(any(segment_rect(a,b,boxes[n['id']]) for a,b in zip(path,path[1:]))
                     for e,path in paths for n in nodes if n['id'] not in (e['source'],e['target']))
    crossings = sum(any(segments_intersect(a,b,c,d) for a,b in zip(p,p[1:]) for c,d in zip(q,q[1:]))
                    for (e,p),(f,q) in combinations(paths,2) if not {e['source'],e['target']} & {f['source'],f['target']})
    crossing_pairs = [(e.get('id',str(i)),f.get('id',str(j)))
                      for (i,(e,p)),(j,(f,q)) in combinations(enumerate(paths),2)
                      if not {e['source'],e['target']} & {f['source'],f['target']}
                      and any(segments_intersect(a,b,c,d) for a,b in zip(p,p[1:]) for c,d in zip(q,q[1:]))]
    oriented = model.get('archetype','process-flow') in ('process-flow','decision-flow','pipeline','hierarchy')
    from connector_policy import BACKWARD_TYPES, SECONDARY_ROLES
    ordinary = [(e,p) for e,p in paths if e.get('type') not in BACKWARD_TYPES and e.get('role') not in SECONDARY_ROLES]
    main_bends = sum(max(0,len(p)-2) for e,p in ordinary if e.get('type') not in ('branch','exception')) if oriented else 0
    axis = 1 if model.get('_layout_direction',model.get('direction')) == 'TB' else 0
    backward = sum(boxes[e['target']][axis]+boxes[e['target']][axis+2]/2 < boxes[e['source']][axis]+boxes[e['source']][axis+2]/2 for e,p in ordinary) if oriented else 0
    bends = sum(max(0,len(p)-2) for _,p in paths)
    length = sum(math.dist(a,b) for _,p in paths for a,b in zip(p,p[1:]))
    target_width = profile.get('target_width_mm')
    target = model.get('target',model.get('profile','document'))
    target_height = target_width*profile['canvas_height']/profile['canvas_width'] if target_width and target in ('presentation','a4-portrait','a4-landscape') else None
    width_scale = target_width/width if target_width else None
    height_scale = target_height/height if target_height else None
    scale = min(width_scale,height_scale) if height_scale else width_scale
    projected = min(profile[k] for k in ('title','body','edge'))*scale*72/25.4 if scale else None
    minimum = profile.get('min_font_pt') or 0
    small = max(0,minimum-projected) if projected is not None else 0
    target_height_at_width = height*width_scale if width_scale else None
    document_height_penalty = max(0,(target_height_at_width-200)/10) if target == 'document' and target_height_at_width else 0
    aspect = width/height
    target_aspect = profile['canvas_width']/profile['canvas_height']
    whitespace = max(0,1-sum(n['width']*n['height'] for n in nodes)/(width*height))
    containment = sum(n['x'] < 0 or n['y'] < 60 or n['x']+n['width'] > boxes[n['parent']][2] or n['y']+n['height'] > boxes[n['parent']][3]
                      for n in model.get('groups',[])+nodes if n.get('parent','1') != '1')
    penalties = dict(node_overlaps=collisions*100, edge_node_collisions=edge_nodes*80,
                     containment=containment*100, document_height=document_height_penalty, small_font=small*12, crossings=crossings*8,
                     main_flow_bends=main_bends*2, backward_ordinary_edges=backward*15, bends=bends*.5, edge_length=length/1000, aspect=abs(math.log(aspect/target_aspect))*5,
                     whitespace=whitespace*3, label_collisions=model.get('_label_collisions',0)*20)
    return dict(score=round(100-sum(penalties.values()),3), penalties=penalties,
                crossings=crossings,crossing_pairs=crossing_pairs,main_flow_bends=main_bends,backward_ordinary_edges=backward,total_edge_length=round(length,3),node_overlaps=collisions,edge_node_collisions=edge_nodes,bends=bends,
                projected_min_font_pt=round(projected,3) if projected else None, aspect_ratio=round(aspect,3),
                target_height_mm=target_height, height_at_target_width_mm=target_height_at_width,
                projection_constraint='height' if height_scale and height_scale < width_scale else 'width' if width_scale else None,
                width_px=width,height_px=height,whitespace_fraction=round(whitespace,3),
                coverage='Estimated orthogonal paths and labels; rendered routing/font QA required')


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path,help='Placed model from layout_diagram.py')
    parser.add_argument('--report',type=Path)
    args = parser.parse_args()
    result = score_layout(json.loads(args.model.read_text(encoding='utf-8-sig')))
    payload = json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(payload,encoding='utf-8')
    else:
        print(payload,end='')
