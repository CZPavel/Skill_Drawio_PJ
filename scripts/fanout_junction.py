"""Opt-in waypoint for same-direction native fan-out; retains logical identity.

Only flat, uncompressed, single-page generated diagrams are supported. The input
is preserved. This is a routing helper, not an electrical contact or new device.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def inventory(root):
    nodes=[];edges=[]
    for c in root.iter('mxCell'):
        if c.get('pjSyntheticRoutingHelper')=='1':continue
        if c.get('vertex')=='1':nodes.append(c.get('id'))
        if c.get('edge')=='1':edges.append((c.get('id'),c.get('pjLogicalSource',c.get('source')),c.get('target'),c.get('value','')))
    return sorted(nodes),sorted(edges)


def add_junction(source,output,source_id,direction='LR'):
    source,output=Path(source),Path(output)
    if source.resolve()==output.resolve():raise ValueError('Use a separate output')
    if direction not in ('LR','TB'):raise ValueError('direction must be LR or TB')
    tree=ET.parse(source);root=tree.getroot();before=inventory(root)
    if len(root.findall('diagram'))!=1 or root.find('diagram/mxGraphModel/root') is None:
        raise ValueError('Helper requires one uncompressed page')
    native=root.find('diagram/mxGraphModel/root');cells={c.get('id'):c for c in native.findall('mxCell')}
    node=cells[source_id];parent=node.get('parent','1')
    edges=[c for c in cells.values() if c.get('edge')=='1' and c.get('source')==source_id]
    if len(edges)<3 or len({(c.get('pjRole','data'),c.get('pjType','')) for c in edges})!=1:
        raise ValueError('Requires at least three similar outgoing relations')
    if any(c.get('pjType') in ('retry','feedback','backward') for c in edges):
        raise ValueError('Feedback cannot use a forward fan-out junction')
    from lint_drawio import style
    edge_styles=[style(e.get('style','')) for e in edges]
    if any(e.get('pjType')=='technical-interface' or any(k in s for k in ('exitX','exitY','exitDx','exitDy','entryX','entryY','entryDx','entryDy'))
           or s.get('startArrow','none')!='none' for e,s in zip(edges,edge_styles)):
        raise ValueError('Helper cannot merge fixed source interfaces or source markers')
    if any(s!=edge_styles[0] for s in edge_styles[1:]):
        raise ValueError('Helper requires identical connector styles')
    expected_source,expected_target=('east','west') if direction=='LR' else ('south','north')
    if any(s.get('sourcePortConstraint',expected_source)!=expected_source or s.get('targetPortConstraint',expected_target)!=expected_target
           for s in edge_styles):
        raise ValueError('Helper cannot replace explicit attachment side intent')
    if style(node.get('style','')).get('portConstraint',expected_source)!=expected_source or any(
            style(cells[e.get('target')].get('style','')).get('portConstraint',expected_target)!=expected_target for e in edges):
        raise ValueError('Terminal side constraints conflict with fan-out direction')
    def box(c):
        g=c.find('mxGeometry')
        if g is None or c.get('parent','1')!=parent:raise ValueError('Helper requires sibling terminals')
        return tuple(float(g.get(k,'0')) for k in ('x','y','width','height'))
    x,y,w,h=box(node);targets=[box(cells[e.get('target')]) for e in edges]
    if direction=='LR':
        near=min(t[0] for t in targets)
        if near<x+w+48:raise ValueError('Insufficient forward corridor')
        jx,jy=x+w+16,y+h/2
    else:
        near=min(t[1] for t in targets)
        if near<y+h+48:raise ValueError('Insufficient forward corridor')
        jx,jy=x+w/2,y+h+16
    helper=source_id+'-routing-junction';trunk=helper+'-trunk'
    if helper in cells or trunk in cells:raise ValueError('Helper ID already exists')
    c=ET.SubElement(native,'mxCell',id=helper,parent=parent,vertex='1',value='',
        pjSyntheticRoutingHelper='1',style='shape=waypoint;size=4;fillColor=none;strokeColor=none;')
    ET.SubElement(c,'mxGeometry',x=str(jx-2),y=str(jy-2),width='4',height='4',**{'as':'geometry'})
    base=style(edges[0].get('style',''))
    for key in list(base):
        if key.startswith(('exit','entry')) or key in ('sourcePortConstraint','targetPortConstraint','jumpStyle','jumpSize','libavoidRouting'):
            base.pop(key)
    base.update(edgeStyle='orthogonalEdgeStyle',endArrow='none')
    base['sourcePortConstraint']=expected_source
    trunk_cell=ET.SubElement(native,'mxCell',id=trunk,parent=parent,edge='1',source=source_id,target=helper,
        pjSyntheticRoutingHelper='1',style=';'.join(k+'='+str(v) for k,v in base.items())+';')
    ET.SubElement(trunk_cell,'mxGeometry',relative='1',**{'as':'geometry'})
    for e,target_box in zip(edges,targets):
        e.set('pjLogicalSource',source_id);e.set('source',helper)
        opts=style(e.get('style',''))
        for key in list(opts):
            if key.startswith('exit') or key in ('sourcePortConstraint','libavoidRouting'):opts.pop(key)
        opts.update(edgeStyle='none',noEdgeStyle=1,targetPortConstraint='west' if direction=='LR' else 'north')
        e.set('style',';'.join(k+'='+str(v) for k,v in opts.items())+';')
        g=e.find('mxGeometry')
        for points in list(g.findall('Array')):g.remove(points)
        tx,ty,tw,th=target_box
        point=(jx,ty+th/2) if direction=='LR' else (tx+tw/2,jy)
        array=ET.SubElement(g,'Array',**{'as':'points'})
        ET.SubElement(array,'mxPoint',x=str(point[0]),y=str(point[1]))
        # Label the branch arm near the target, not the shared vertical/horizontal
        # bus. These are explicit composition waypoints, not an obstacle router.
        arm=tx-jx if direction=='LR' else ty-jy
        bus=abs(point[1]-jy) if direction=='LR' else abs(point[0]-jx)
        g.set('x',str(2*(bus+arm/2)/(bus+arm)-1));g.set('y','18')
    if inventory(root)!=before:raise ValueError('Semantic inventory changed')
    output.parent.mkdir(parents=True,exist_ok=True);ET.indent(root)
    output.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
    return {'helper':helper,'branches':len(edges),'semantic_inventory_preserved':True,'requires_rendered_qa':True}


if __name__=='__main__':
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('output');p.add_argument('--source-id',required=True);p.add_argument('--direction',choices=['LR','TB'],default='LR')
    a=p.parse_args();print(json.dumps(add_junction(a.source,a.output,a.source_id,a.direction),indent=2))
