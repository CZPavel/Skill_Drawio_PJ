"""Optional adapter to an externally installed JGraph @drawio/mcp routeXml pass.

No router code is bundled. Requires the package directory via --mcp-root.
Preserves source; rejects changes beyond edge styles/geometries.
"""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from lint_drawio import pages, style

def contract(text):
    result=[]
    for name,model in pages(ET.fromstring(text)):
        cells=[]
        for item in model.find('root'):
            c=item if item.tag=='mxCell' else item.find('mxCell')
            if c is None:raise ValueError('Unsupported native root item')
            attrs=dict(c.attrib)
            if c.get('edge')=='1':
                managed={'edgeStyle','noEdgeStyle','rounded','libavoidRouting','orthogonalLoop','jettySize'}
                attrs['style']=str(sorted((k,v) for k,v in style(attrs.get('style','')).items() if k not in managed))
            cells.append((item.tag,{k:v for k,v in item.attrib.items() if item.tag!='mxCell'},attrs,
                          None if c.get('edge')=='1' else ET.tostring(c.find('mxGeometry')) if c.find('mxGeometry') is not None else None))
        result.append((name,dict(model.attrib),cells))
    return result

def route(source,output,mcp_root):
    source,output=Path(source),Path(output)
    if source.resolve()==output.resolve():raise ValueError('Route to a separate native source')
    module=Path(mcp_root).resolve()/'src/libavoid-pass.js'
    if not module.is_file():raise ValueError('External @drawio/mcp src/libavoid-pass.js missing')
    original=source.read_text(encoding='utf-8-sig')
    # Engine may catch failures and return unchanged XML; report that explicitly.
    js="const fs=require('node:fs');const {pathToFileURL}=require('node:url');(async()=>{const m=await import(pathToFileURL(process.argv[1]).href);process.stdout.write(await m.routeXml(fs.readFileSync(process.argv[2],'utf8')));})().catch(e=>{console.error(e);process.exit(1)});"
    result=subprocess.run(['node','-e',js,str(module),str(source.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=60,check=True)
    revised=result.stdout
    if contract(original)!=contract(revised):raise ValueError('External router changed native semantic or node contract')
    changed=original.strip()!=revised.strip()
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(revised,encoding='utf-8')
    return {'changed':changed,'status':'routed-review-required' if changed else 'unchanged-unverified','engine':'external @drawio/mcp libavoid routeXml','visual_review_required':True}

def repair_generated_labels(source, ir):
    """One bounded local repair for generated IR, never an arbitrary XML round-trip.

    Reuses label placement against external router waypoints. Explicit IR label
    positions remain authoritative. Writes only edge label geometry x/y.
    """
    from layout_diagram import layout, _labels
    from score_layout import absolute_boxes, edge_path
    from build_diagram import effective_profile
    model,_=layout(ir);boxes=absolute_boxes(model)
    original={e.get('id',f'edge-{i+1}'):e for i,e in enumerate(ir.get('edges',[]))}
    for e in model.get('edges',[]):
        if not any(k in original[e['id']] for k in ('label_position','label_offset')):
            e.pop('label_position',None);e.pop('label_offset',None)
    tree=ET.parse(source);root=tree.getroot();paths={};native={}
    if len(root.findall('diagram'))!=1 or root.find('diagram/mxGraphModel') is None:
        raise ValueError('Generated label repair requires one uncompressed page')
    expected={n['id']:n for n in model.get('nodes',[])+model.get('groups',[])}
    for c in root.iter('mxCell'):
        if c.get('vertex')=='1':
            n=expected.get(c.get('id'));g=c.find('mxGeometry')
            if n is None or g is None or c.get('parent','1')!=n.get('parent','1') or any(abs(float(g.get(k,'0'))-n[k])>.01 for k in ('x','y','width','height')):
                raise ValueError('Reconcile manual geometry before generated label repair')
    for c in root.iter('mxCell'):
        if c.get('edge')!='1':continue
        native[c.get('id')]=c
        e=next(e for e in model.get('edges',[]) if e['id']==c.get('id'))
        if c.get('value','')!=e.get('label',''):raise ValueError('Reconcile changed edge labels before reusing IR')
        e['style']=style(c.get('style',''))
        start,end=edge_path(e,boxes)[0],edge_path(e,boxes)[-1]
        parent=boxes.get(c.get('parent'),(0,0,0,0))
        points=[(float(p.get('x','0'))+parent[0],float(p.get('y','0'))+parent[1]) for p in c.findall('mxGeometry/Array/mxPoint')]
        path=[start]+points+[end];paths[e['id']]=[p for i,p in enumerate(path) if i==0 or p!=path[i-1]]
    flags=_labels(model,boxes,effective_profile(model),paths=paths)
    for e in model.get('edges',[]):
        if any(k in original[e['id']] for k in ('label_position','label_offset')):continue
        if e.get('label'):
            g=native[e['id']].find('mxGeometry');g.set('x',str(e['label_position']));g.set('y',str(e['label_offset']))
    ET.indent(root);tree.write(source,encoding='utf-8',xml_declaration=True)
    return {'label_repair_flags':flags,'coverage':'Router waypoints are estimates of final rendered paths; visual review required'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--mcp-root',required=True,type=Path)
    p.add_argument('--ir',type=Path,help='Optional original generation IR for one label repair; rejects changed node geometry')
    a=p.parse_args();result=route(a.source,a.output,a.mcp_root)
    if a.ir:result.update(repair_generated_labels(a.output,json.loads(a.ir.read_text(encoding='utf-8-sig'))))
    print(json.dumps(result,indent=2))
