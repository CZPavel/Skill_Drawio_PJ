"""Small semantic connector policy; no routing engine or imported XML mutation."""
import math

SIDES = {'left':'west','right':'east','top':'north','bottom':'south'}
POINTS = {'left':(0,.5),'right':(1,.5),'top':(.5,0),'bottom':(.5,1)}
BACKWARD_TYPES = {'retry','feedback','backward'}
SECONDARY_ROLES = {'service','control','exception','note'}
FIXED_KEYS = ('exitX','exitY','entryX','entryY')


def facing_sides(a,b):
    dx,dy = b[0]+b[2]/2-a[0]-a[2]/2,b[1]+b[3]/2-a[1]-a[3]/2
    return (('bottom','top') if dy >= 0 else ('top','bottom')) if abs(dy)>abs(dx) else (('right','left') if dx>=0 else ('left','right'))


def choose_connector_mode(model, edge):
    mode = edge.get('connector_mode')
    if mode is None:
        mode = 'fixed' if any(k in edge.get('style',{}) for k in FIXED_KEYS) or edge.get('type') == 'technical-interface' else 'side' if model.get('archetype','process-flow') in ('process-flow','decision-flow','hierarchy','pipeline') else 'floating'
        if mode!='fixed' and any(k in edge.get('style',{}) for k in ('sourcePortConstraint','targetPortConstraint')):
            mode='side'
    if mode not in ('floating','side','fixed'):
        raise ValueError('connector_mode must be floating, side or fixed')
    return mode


def validate_fixed(style, source, target, allow_interior=False):
    for prefix,node in (('exit',source),('entry',target)):
        try:
            x,y = (float(style[prefix+k]) for k in ('X','Y'))
        except (KeyError,TypeError,ValueError):
            raise ValueError('fixed requires complete exitX/Y and entryX/Y') from None
        if not all(math.isfinite(v) and 0<=v<=1 for v in (x,y)):
            raise ValueError('fixed points must be normalized finite coordinates')
        shape = node.get('style',{}).get('shape',node.get('shape'))
        if shape in ('decision','rhombus'):
            perimeter = math.isclose(abs(x-.5)+abs(y-.5),.5,abs_tol=1e-8)
        elif shape in (None,'rectangle','terminal'):
            perimeter = x in (0,1) or y in (0,1)
        elif shape == 'ellipse':
            perimeter = math.isclose((2*x-1)**2+(2*y-1)**2,1,abs_tol=1e-8)
        else:
            raise ValueError('fixed perimeter for this shape is unverified; use a supported shape')
        if not perimeter and not allow_interior:
            raise ValueError('fixed point must lie on shape perimeter; explicit allow_interior_port required')
        style.setdefault(prefix+'Perimeter',0 if allow_interior and not perimeter else 1)


def connector_style(model,edge,boxes,nodes,direction):
    result = dict(edge.get('style',{}))
    mode = choose_connector_mode(model,edge)
    edge['connector_mode'] = mode
    if mode != 'fixed':
        if any(k in result for k in FIXED_KEYS):
            raise ValueError('floating/side cannot contain fixed coordinates')
        if mode == 'floating':
            for k in ('sourcePortConstraint','targetPortConstraint'):
                result.pop(k,None)
            return result
    a,b = facing_sides(boxes[edge['source']],boxes[edge['target']])
    if model.get('archetype','process-flow') in ('process-flow','decision-flow','hierarchy','pipeline'):
        a,b = ('right','left') if direction=='LR' else ('bottom','top')
        if edge.get('type') in BACKWARD_TYPES:
            a=b='top' if direction=='LR' else 'left'
        elif edge.get('type') in ('branch','exception'):
            a,b = facing_sides(boxes[edge['source']],boxes[edge['target']])
    if mode == 'side' and nodes[edge['source']].get('shape') == 'decision' and edge.get('type') not in BACKWARD_TYPES:
        branches = [e for e in model.get('edges',[]) if e['source']==edge['source'] and e.get('type') not in BACKWARD_TYPES]
        index = next(i for i,e in enumerate(branches) if e['id']==edge['id'])
        if index in (1,2):
            a = ('bottom','top')[index-1] if direction=='LR' else ('right','left')[index-1]
    ports = edge.get('ports',{})
    a,b = ports.get('source',a),ports.get('target',b)
    if a not in SIDES or b not in SIDES:
        raise ValueError('ports require left/right/top/bottom')
    if mode == 'side':
        if 'source' in ports:result['sourcePortConstraint']=SIDES[a]
        else:result.setdefault('sourcePortConstraint',SIDES[a])
        if 'target' in ports:result['targetPortConstraint']=SIDES[b]
        else:result.setdefault('targetPortConstraint',SIDES[b])
    else:
        if not any(k in result for k in FIXED_KEYS):
            raise ValueError('fixed requires explicit exitX/Y and entryX/Y')
        validate_fixed(result,nodes[edge['source']],nodes[edge['target']],edge.get('allow_interior_port',False))
    return result


def choose_jump_policy(edges,pairs):
    """Estimated crossing pairs only. Every jump requires rendered confirmation."""
    by_id = {e['id']:e for e in edges}
    selected,flags = set(),[]
    if len(pairs)>2:
        return [],['multiple-crossings:reroute-review']
    for a,b in pairs:
        secondary = [key for key in (a,b) if by_id[key].get('role') in SECONDARY_ROLES or by_id[key].get('type') in BACKWARD_TYPES|{'exception'}]
        if len(secondary)==1:
            selected.add(secondary[0])
        else:
            flags.append(f'crossing:{a}:{b}:jump-selection-review')
    if selected:
        flags.append('jump-insertion:rendered-review')
    return sorted(selected),flags


def choose_routing_strategy(model,metrics,capabilities=None):
    """Recommend one engine; never run a probe or mutate placement implicitly."""
    conflict = any(metrics.get(k,0) for k in ('edge_node_collisions','node_overlaps','backward_ordinary_edges')) or metrics.get('crossings',0)>2
    if not conflict:
        return {'strategy':'native','reason':'simple estimated routes; confirm export'}
    process = model.get('archetype','process-flow') in ('process-flow','decision-flow','pipeline','hierarchy')
    movable = not model.get('preserve_placement',False)
    placement_problem = metrics.get('node_overlaps',0) or metrics.get('backward_ordinary_edges',0) or metrics.get('main_flow_bends',0)>4
    prefer = 'elk' if process and movable and placement_problem else 'libavoid'
    def verified(key):
        v=(capabilities or {}).get(key,{})
        return v is True or isinstance(v,dict) and v.get('status')=='verified'
    if capabilities is None:
        return {'strategy':'probe-required','preferred':prefer,'reason':'capability not supplied; explicit diagnostic once per session'}
    libavoid=verified('desktop_libavoid') or verified('mcp_libavoid')
    elk=verified('elk') or verified('desktop_elk')
    constrained=any(e.get('connector_mode')=='side' or any(k in e.get('style',{}) for k in ('sourcePortConstraint','targetPortConstraint'))
                    for e in model.get('edges',[]))
    constrained=constrained or any('portConstraint' in n.get('style',{}) for n in model.get('nodes',[])+model.get('groups',[]))
    if constrained:
        def side_capable(key):
            v=capabilities.get(key,{})
            return verified(key) and isinstance(v,dict) and v.get('supports_side_constraints') is True
        libavoid=side_capable('desktop_libavoid') or side_capable('mcp_libavoid')
        elk=side_capable('elk') or side_capable('desktop_elk')
    if prefer=='elk' and elk:
        return {'strategy':'elk','preset':'elk-flow-clean','positions_may_change':True}
    if libavoid:
        return {'strategy':'libavoid','positions_may_change':False}
    if process and movable and elk:
        return {'strategy':'elk','preset':'elk-flow-clean','positions_may_change':True}
    return {'strategy':'local-repair','reason':'no verified appropriate engine; preserve placement and review'}
