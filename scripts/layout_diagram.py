"""Small deterministic semantic IR placement above native draw.io routing."""
import argparse
import copy
import json
import math
from pathlib import Path
from score_layout import absolute_boxes, edge_path, score_layout
from lint_drawio import overlap


def validate_ir(model):
    from build_diagram import TOKENS
    if model.get('direction','auto') not in ('auto','LR','TB'):
        raise ValueError('direction must be auto, LR or TB')
    if model.get('target',model.get('profile','document')) not in TOKENS['profiles']:
        raise ValueError('Unknown target/profile')
    items = model.get('groups',[])+model.get('nodes',[])
    ids = {'0','1'}
    for i,item in enumerate(items+model.get('edges',[])):
        key = item.get('id',f'edge-{i-len(items)+1}' if i >= len(items) else None)
        if not isinstance(key,str) or not key or key in ids:
            raise ValueError(f'Duplicate, missing or reserved id: {key}')
        ids.add(key)
        if item.get('role','data') not in TOKENS['roles']:
            raise ValueError('Unknown semantic role')
        for field in ('width','height','preferred_width','padding'):
            if field in item and (not isinstance(item[field],(int,float)) or not math.isfinite(item[field]) or item[field] <= 0):
                raise ValueError(f'Invalid {field}')
    groups = {g['id']:g for g in model.get('groups',[])}
    for item in items:
        if not isinstance(item.get('title'),str):
            raise ValueError('Node/group title must be a string')
        parent = item.get('parent',item.get('group','1'))
        seen = {item['id']}
        while parent != '1':
            if parent not in groups or parent in seen:
                raise ValueError('Unknown parent or parent cycle')
            seen.add(parent)
            parent = groups[parent].get('parent',groups[parent].get('group','1'))
    terminals = {item['id'] for item in items}
    for edge in model.get('edges',[]):
        if edge.get('source') not in terminals or edge.get('target') not in terminals:
            raise ValueError('Unknown edge terminal')
    return model


def choose_card_width(node, profile, model=None, widths=None):
    from build_diagram import measure, TOKENS, font
    model = model or {}
    widths = [node['width']] if 'width' in node else [node['preferred_width']] if 'preferred_width' in node else widths or [220,260,300,340,380]
    if 'width' not in node and 'preferred_width' not in node:
        pad = node.get('padding',TOKENS['padding'])
        longest = max([font(profile['title'],True,model.get('bold_font_path')).getlength(w) for w in node['title'].split()] +
                      [font(profile['body'],False,model.get('font_path')).getlength(w) for w in node.get('body','').split()] + [0])
        required = (longest+2*pad+4)*(2 if node.get('shape')=='decision' else 1)
        if required > max(widths):
            widths = list(widths)+[math.ceil(required/4)*4]
    choices = []
    for width in widths:
        try:
            decision = node.get('shape') == 'decision'
            _,_,height = measure(node['title'],node.get('body',''),width/2 if decision else width,profile,
                                 model.get('font_path'),model.get('bold_font_path'),node.get('padding',TOKENS['padding']))
            height = max(node.get('height',0),height*(2 if decision else 1))
            choices.append((width*height+height*height*.6,width,height))
        except ValueError:
            continue
    if not choices:
        raise ValueError(f"Text does not fit candidate widths: {node['id']}; supply width")
    _,width,height = min(choices)
    return width,height


def automatic_ports(source, target, override=None):
    dx = target[0]+target[2]/2-source[0]-source[2]/2
    dy = target[1]+target[3]/2-source[1]-source[3]/2
    a,b = ('right','left') if dx >= 0 else ('left','right')
    if abs(dy) > abs(dx):
        a,b = ('bottom','top') if dy >= 0 else ('top','bottom')
    sides = {'left':(0,.5),'right':(1,.5),'top':(.5,0),'bottom':(.5,1)}
    if override:
        a,b = override.get('source',a),override.get('target',b)
    if a not in sides or b not in sides:
        raise ValueError('ports require left/right/top/bottom')
    return dict(exitX=sides[a][0],exitY=sides[a][1],entryX=sides[b][0],entryY=sides[b][1])


def _labels(model, boxes, profile, paths=None):
    """Place labels against estimated or supplied absolute polylines keyed by edge ID.

    Explicit label_position/label_offset remain authoritative; remove generated values
    before a post-routing repair when their geometry is stale.
    """
    from build_diagram import font
    occupied, flags, collisions = [], [], 0
    for e in model.get('edges',[]):
        if not e.get('label'):
            continue
        path = paths.get(e['id'],edge_path(e,boxes)) if paths is not None else edge_path(e,boxes)
        if len(path) < 2 or any(len(p) != 2 or not all(math.isfinite(v) for v in p) for p in path):
            flags.append(f"label:{e['id']}:invalid-path-review")
            continue
        lengths = [math.dist(a,b) for a,b in zip(path,path[1:])]
        total = sum(lengths)
        w = max(font(profile['edge'],path=model.get('font_path')).getlength(line) for line in e['label'].split('\n'))+12
        h = len(e['label'].split('\n'))*profile['edge']*1.2+8
        choices = []
        for fraction in (.5,.3,.7,.1,.9):
            distance = total*fraction
            for index,(a,b) in enumerate(zip(path,path[1:])):
                if distance <= lengths[index] or index == len(lengths)-1:
                    ratio = distance/lengths[index] if lengths[index] else 0
                    x,y = a[0]+(b[0]-a[0])*ratio,a[1]+(b[1]-a[1])*ratio
                    break
                distance -= lengths[index]
            # A vertical segment needs horizontal clearance based on label width.
            extent = h if a[1] == b[1] else w
            offsets = dict.fromkeys((-18,18,-36,36,-(extent/2+12),extent/2+12))
            for offset in offsets:
                # mxGraph label offsets are normal to the local segment.
                nx,ny = ((0,-1) if b[0]>=a[0] else (0,1)) if a[1]==b[1] else ((1,0) if b[1]>=a[1] else (-1,0))
                rect = (x+nx*offset-w/2,y+ny*offset-h/2,w,h)
                cost = sum(overlap(rect,r) for r in list(boxes.values()) if r not in [boxes[g['id']] for g in model.get('groups',[])])
                cost += sum(overlap(rect,r) for r in occupied)
                cost += sum(rect[0] <= p[0] <= rect[0]+w and rect[1] <= p[1] <= rect[1]+h for p in path[1:])
                choices.append((cost,fraction,offset,rect))
        cost,fraction,offset,rect = min(choices,key=lambda c:(c[0],abs(c[2])))
        if 'label_position' not in e and 'label_offset' not in e:
            e.update(label_position=round(2*fraction-1,3),label_offset=offset)
            occupied.append(rect)
            collisions += cost
            if cost:
                flags.append(f"label:{e['id']}:collision-review")
        else:
            flags.append(f"label:{e['id']}:explicit-placement-review")
    model['_label_collisions'] = collisions
    return flags


def layout(model):
    from build_diagram import TOKENS, effective_profile, font, load_preset
    validate_ir(model)
    base = copy.deepcopy(model)
    base['profile'] = base.get('target',base.get('profile','document'))
    for n in base.get('groups',[])+base.get('nodes',[]):
        n['parent'] = n.get('parent',n.get('group','1'))
    for i,e in enumerate(base.get('edges',[])):
        e.setdefault('id',f'edge-{i+1}')
    profile = effective_profile(base)
    count = len(base.get('nodes',[]))
    limit = 3 if count <= 6 else 8 if count <= 18 else 12
    options = [('LR',64,1),('LR',40,0),('TB',64,1),('TB',40,0),('LR',88,2),('TB',88,2),('LR',64,2),('TB',64,2),('LR',40,2),('TB',40,2),('LR',88,0),('TB',88,0)]
    direction = base.get('direction','auto')
    if direction != 'auto':
        options = [o for o in options if o[0] == direction]
    candidates = []
    for orientation,gap,width_mode in options[:limit]:
        # Short inter-node gaps cannot carry a wide edge label. Reserve its
        # measured span before placement instead of compensating with offsets.
        label_spans = [max(font(profile['edge'],path=base.get('font_path')).getlength(line)
                           for line in e['label'].split('\n')) if orientation == 'LR'
                       else len(e['label'].split('\n'))*profile['edge']*1.2
                       for e in base.get('edges',[]) if e.get('label')]
        if label_spans:
            gap = max(gap,math.ceil(max(label_spans)+32))
        placed = copy.deepcopy(base)
        items = placed.get('groups',[])+placed.get('nodes',[])
        by_id = {n['id']:n for n in items}
        for n in placed.get('nodes',[]):
            n['width'],n['height'] = choose_card_width(n,profile,placed,[[220,260,300],[260,300,340,380],[300,340,380,440]][width_mode])
        ordered = []
        def arrange(parent):
            grouped = placed.get('archetype') in ('grouped-training','training','cards')
            local_orientation = 'TB' if grouped and parent != '1' else orientation
            children = [n for n in items if n['parent'] == parent]
            for child in children:
                if child in placed.get('groups',[]):
                    arrange(child['id'])
            # Stable DAG levels; back/retry edges do not force unbounded ranking.
            ranks = {n['id']:0 for n in children}
            index = {n['id']:i for i,n in enumerate(children)}
            if placed.get('archetype','process-flow') not in ('comparison','grouped-training','training','cards'):
                def direct_child(key):
                    while key in by_id and key not in index:
                        key = by_id[key]['parent']
                    return key
                links = []
                for edge in placed.get('edges',[]):
                    source,target = direct_child(edge['source']),direct_child(edge['target'])
                    secondary = placed.get('archetype') == 'network-topology' and edge.get('role','data') in ('control','note','service')
                    if source in index and target in index and source != target and edge.get('type') not in ('retry','feedback') and not secondary:
                        links.append((source,target))
                remaining = list(ranks)
                processed = set()
                while remaining:
                    ready = [key for key in remaining if not any(b==key and a not in processed for a,b in links)]
                    # Cycles get a stable break; semantics and all edges remain intact.
                    if not ready:
                        ready = [remaining[0]]
                    for key in ready:
                        predecessors = [a for a,b in links if b==key and a in processed]
                        ranks[key] = max((ranks[p]+1 for p in predecessors),default=0)
                        processed.add(key)
                        remaining.remove(key)
            elif children:
                columns = max(1,math.ceil(math.sqrt(len(children)*profile['canvas_width']/profile['canvas_height'])))
                ranks = {n['id']:i%columns for i,n in enumerate(children)}
            if grouped and parent != '1':
                ranks = {n['id']:i for i,n in enumerate(children)}
            main = 28
            for rank in sorted(set(ranks.values())):
                lane = [n for n in children if ranks[n['id']] == rank]
                cross = 88 if parent != '1' else 28
                for n in lane:
                    n['x'],n['y'] = (main,cross) if local_orientation=='LR' else (cross,main+(60 if parent!='1' else 0))
                    cross += n['height' if local_orientation=='LR' else 'width']+gap
                main += max(n['width' if local_orientation=='LR' else 'height'] for n in lane)+gap
            if parent != '1':
                group = by_id[parent]
                group.setdefault('width',max(max((n['x']+n['width'] for n in children),default=200)+28, math.ceil(font(profile['title'],True,placed.get('bold_font_path')).getlength(group['title'])+40)))
                group.setdefault('height',max((n['y']+n['height'] for n in children),default=100)+28)
                ordered.append(group)
        arrange('1')
        # Ancestors before descendants in native builder.
        placed['groups'] = sorted(ordered,key=lambda g: _depth(g,by_id))
        boxes = absolute_boxes(placed)
        flags = []
        for e in placed.get('edges',[]):
            e['style'] = {**automatic_ports(boxes[e['source']],boxes[e['target']],e.get('ports')),**e.get('style',{})}
            if e.pop('points',None):
                flags.append(f"edge:{e['id']}:stale-waypoints-cleared")
        flags += _labels(placed,boxes,profile)
        metrics = score_layout(placed,profile)
        if metrics['edge_node_collisions'] or metrics['crossings']:
            flags.append('native-routing-review')
        if metrics['penalties']['containment']:
            flags.append('explicit-group-containment-review')
        sensitive = {'fontSize','fontFamily','spacing','spacingLeft','spacingRight','spacingTop','spacingBottom','whiteSpace','html','shape','startSize','rotation','overflow'}
        preset = load_preset(placed)
        if any(sensitive & set(n.get('style',{})) for n in items+placed.get('edges',[])) or any(sensitive & set(preset.get(k,{})) for k in ('vertex_style','edge_style')):
            flags.append('native-geometry-text-style-overrides:measurement-review')
        if metrics['penalties']['small_font']:
            flags.append('target-font-review:split-or-recompose')
        name = f'{orientation}-gap{gap}-width{width_mode}'
        candidates.append((placed,dict(name=name,**metrics),flags))
    best = max(candidates,key=lambda c:c[1]['score'])
    if best[1]['crossings']:
        for edge in best[0].get('edges',[]):
            edge['style'].setdefault('jumpStyle','arc')
            edge['style'].setdefault('jumpSize',10)
    report = dict(selected=best[1]['name'],candidates=[c[1] for c in candidates],review_flags=best[2],
                  routing='native orthogonal; score uses estimated paths, not final renderer geometry')
    return best[0],report


def _depth(group, items):
    depth = 0
    while group['parent'] != '1':
        depth += 1
        group = items[group['parent']]
    return depth


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--report',type=Path)
    args = parser.parse_args()
    placed,report = layout(json.loads(args.model.read_text(encoding='utf-8-sig')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(placed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
