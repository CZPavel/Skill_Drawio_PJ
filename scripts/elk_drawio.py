"""Bounded ELK adapter to external official @drawio/mcp layoutXml.

This interface exposes direction only. Compact is a disclosed clean-flow alias;
no spacing/crossing/port options are silently invented or injected.
"""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from lint_drawio import pages, style
from route_drawio import has_side_constraints

PRESETS={'elk-flow-clean':'Official layered flow','elk-flow-compact':'Limited alias of clean; interface exposes no spacing options','elk-hierarchy':'Official layered flow; hierarchy by directed layers'}

def semantic_contract(text):
    result=[]
    managed={'curved','edgeStyle','noEdgeStyle','rounded','orthogonalLoop','jettySize','exitX','exitY','entryX','entryY','exitDx','exitDy','entryDx','entryDy','exitPerimeter','entryPerimeter'}
    for name,model in pages(ET.fromstring(text)):
        cells=[]
        for item in model.find('root'):
            c=item if item.tag=='mxCell' else item.find('mxCell')
            if c is None:raise ValueError('Unsupported native root item')
            attrs=dict(c.attrib)
            if c.get('edge')=='1':attrs['style']=str(sorted((k,v) for k,v in style(c.get('style','')).items() if k not in managed))
            g=c.find('mxGeometry')
            # Placement and routed edges may change. Shape sizes stay authoritative.
            size=None if g is None or c.get('edge')=='1' else (g.get('width'),g.get('height'))
            cells.append((item.tag,{k:v for k,v in item.attrib.items() if item.tag!='mxCell'},attrs,size))
        result.append((name,dict(model.attrib),cells))
    return result

def layout_elk(source,output,mcp_root,preset='elk-flow-clean',direction='horizontal'):
    if preset not in PRESETS:raise ValueError('Unknown ELK preset')
    if direction not in ('horizontal','vertical'):raise ValueError('ELK direction must be horizontal or vertical')
    source,output=Path(source),Path(output)
    if source.resolve()==output.resolve():raise ValueError('Layout to a separate native source')
    module=Path(mcp_root).resolve()/'src/elk-pass.js'
    if not module.is_file():raise ValueError('External @drawio/mcp src/elk-pass.js missing')
    original=source.read_text(encoding='utf-8-sig')
    if has_side_constraints(original):
        raise ValueError('External layoutXml side constraints are unverified; use native sides or explicitly floating input')
    js="const fs=require('node:fs');const {pathToFileURL}=require('node:url');(async()=>{const m=await import(pathToFileURL(process.argv[1]).href);process.stdout.write(await m.layoutXml(fs.readFileSync(process.argv[2],'utf8'),{direction:process.argv[3]}));})().catch(e=>{console.error(e);process.exit(1)});"
    run=subprocess.run(['node','-e',js,str(module),str(source.resolve()),direction],capture_output=True,text=True,encoding='utf-8',timeout=60,check=True)
    revised=run.stdout
    if semantic_contract(original)!=semantic_contract(revised):raise ValueError('External ELK changed native semantic or shape size contract')
    # The official bridge may replace attachment coordinates. A meaningful fixed
    # interface is semantic intent, not disposable routing geometry.
    for (_,before),(_,after) in zip(pages(ET.fromstring(original)),pages(ET.fromstring(revised))):
        after_cells={c.get('id'):c for c in after.iter('mxCell')}
        for c in before.iter('mxCell'):
            old=style(c.get('style',''))
            if c.get('edge')=='1' and any(k in old for k in ('exitX','exitY','entryX','entryY')):
                new=style(after_cells[c.get('id')].get('style',''))
                keys=('exitX','exitY','entryX','entryY','exitPerimeter','entryPerimeter')
                if any(old.get(k)!=new.get(k) for k in keys):
                    raise ValueError('External ELK changed explicit fixed attachments; use retained-placement routing')
    changed=original.strip()!=revised.strip()
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(revised,encoding='utf-8')
    return {'status':'laid-out-review-required' if changed else 'unchanged-unverified','changed':changed,'engine':'external @drawio/mcp ELK layoutXml','preset':preset,'preset_scope':PRESETS[preset],'direction':direction,'positions_may_change':True,'visual_review_required':True}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--mcp-root',required=True,type=Path);p.add_argument('--preset',choices=PRESETS,default='elk-flow-clean');p.add_argument('--direction',choices=['horizontal','vertical'],default='horizontal')
    a=p.parse_args();print(json.dumps(layout_elk(a.source,a.output,a.mcp_root,a.preset,a.direction),indent=2))
