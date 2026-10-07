"""Lightweight semantic design recommendations; never rewrites supplied labels."""
from collections import defaultdict


def semantic_inventory(model):
    """Routing helpers have no device meaning; logical edge IDs remain authoritative."""
    return {'nodes': sorted(n['id'] for n in model.get('nodes', [])
                            if not n.get('synthetic_routing_helper')),
            'edges': sorted({e.get('logical_edge_id', e.get('id', f'edge-{i+1}'))
                             for i,e in enumerate(model.get('edges', []))
                             if not e.get('synthetic_routing_helper')})}


def review_design(model):
    warnings=[]
    nodes=[n for n in model.get('nodes',[]) if not n.get('synthetic_routing_helper')]
    levels={n['abstraction_level'] for n in nodes if n.get('abstraction_level')}
    if len(levels)>1 and not model.get('mixed_abstraction_reason'):
        warnings.append('design:abstraction-levels:overview-detail-recommended')
    shapes=defaultdict(set)
    for n in nodes:
        kind=n.get('kind')
        if kind:
            shapes[kind].add(n.get('shape','process'))
        label=n.get('title','').strip()
        if kind=='action' and len(label.split())<2:
            warnings.append(f"design:{n['id']}:action-verb-object-recommended")
        if (kind=='decision' or n.get('shape')=='decision') and not label.endswith('?') and not n.get('condition'):
            warnings.append(f"design:{n['id']}:decision-question-or-condition-recommended")
    for kind,values in sorted(shapes.items()):
        if len(values)>1:
            warnings.append(f'design:shape-consistency:{kind}')
    edges=model.get('edges',[])
    styles={(e.get('style',{}).get('dashed',0),e.get('style',{}).get('endArrow','block'),
             e.get('style',{}).get('startArrow','none')) for e in edges}
    colors={n.get('role','data') for n in nodes}|{e.get('role','data') for e in edges}
    if not model.get('legend') and (len(styles)>=3 or (len(colors)>=3 and not model.get('color_meanings_labeled'))
                                  or len(model.get('abbreviations',{}))>=3 or model.get('specialized_notation')):
        warnings.append('design:legend-recommended')
    return warnings
