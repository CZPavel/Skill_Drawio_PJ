"""Six bounded routing cases, same inputs through archived V0.2 and current V0.3."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from PIL import Image,ImageDraw
from build_diagram import build,font
from layout_diagram import layout
from export_drawio import export
from lint_drawio import style
from fanout_junction import add_junction,inventory

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline-root',type=Path,required=True)
    p.add_argument('--mcp-root',type=Path);p.add_argument('--capabilities',type=Path);p.add_argument('--render',action='store_true')
    p.add_argument('--cases',nargs='+',help='Recheck affected cases only, retaining other rows')
    a=p.parse_args();out=ROOT/'benchmark/v03';out.mkdir(parents=True,exist_ok=True)
    rows=json.loads((out/'metrics.json').read_text(encoding='utf-8')) if a.cases and (out/'metrics.json').exists() else []
    caps=json.loads(a.capabilities.read_text(encoding='utf-8')) if a.capabilities else None
    for fixture in sorted((ROOT/'examples/routing').glob('*.json')):
        case=fixture.stem;m=json.loads(fixture.read_text(encoding='utf-8'));row={'case':case,'versions':{}}
        if a.cases and case not in a.cases:continue
        rows=[r for r in rows if r['case']!=case]
        for version in ('v02','v03'):
            folder=out/version;folder.mkdir(exist_ok=True);source=folder/(case+'.drawio');report_path=folder/(case+'.layout.json')
            model=dict(m)
            if version=='v03' and caps:model['routing_capabilities']=caps
            if version=='v02':
                subprocess.run([sys.executable,str(a.baseline_root/'scripts/build_diagram.py'),str(fixture),str(source),'--report',str(report_path)],check=True)
            else:
                build(model,source,report_path)
            report=json.loads(report_path.read_text(encoding='utf-8'));selected=next((c for c in report.get('candidates',[]) if c['name']==report['selected']),None)
            route_result=None
            if version=='v03' and a.mcp_root:
                strategy=report.get('routing_strategy',{}).get('strategy')
                routed=folder/(case+'.routed.drawio')
                if strategy=='libavoid':
                    from route_drawio import route
                    route_result=route(source,routed,a.mcp_root)
                elif strategy=='elk':
                    from elk_drawio import layout_elk
                    route_result=layout_elk(source,routed,a.mcp_root,direction='vertical' if m.get('direction')=='TB' else 'horizontal')
                if route_result:source.write_bytes(routed.read_bytes());routed.unlink()
            if version=='v03' and case=='decision-retry':
                # Explicit local repair after native rendered QA: carry retry
                # outside the whole row, preserving a side (not fixed) endpoint.
                tree=ET.parse(source);cells={c.get('id'):c for c in tree.iter('mxCell')}
                boxes=[c.find('mxGeometry') for c in cells.values() if c.get('vertex')=='1']
                right=max(float(g.get('x','0'))+float(g.get('width','0')) for g in boxes)+32
                top=min(float(g.get('y','0')) for g in boxes)-32
                edge=cells['retry'];st=style(edge.get('style',''));st['sourcePortConstraint']='east'
                edge.set('style',';'.join(f'{k}={v}' for k,v in st.items())+';')
                g=edge.find('mxGeometry');arr=ET.SubElement(g,'Array',{'as':'points'})
                start=cells['no'].find('mxGeometry');end=cells['a'].find('mxGeometry')
                sy=float(start.get('y'))+float(start.get('height'))/2
                tx=float(end.get('x'))+float(end.get('width'))/2
                for x,y in ((right,sy),(right,top),(tx,top)):
                    ET.SubElement(arr,'mxPoint',{'x':str(x),'y':str(y)})
                tree.write(source,encoding='utf-8',xml_declaration=True)
                route_result={'strategy':'explicit-native-retry-corridor','visual_review_required':True}
            if version=='v03' and case=='fanout-four':
                routed=folder/(case+'.junction.drawio');route_result=add_junction(source,routed,'s')
                source.write_bytes(routed.read_bytes());routed.unlink()
            if version=='v03' and case=='one-crossing':
                # Explicit polish of a fixed-position test fixture, not an import
                # side effect of the creation helper. Only the secondary path jumps.
                from connector_policy import choose_jump_policy
                selected,flags=choose_jump_policy(m['edges'],[('main','control')])
                tree=ET.parse(source)
                for c in tree.iter('mxCell'):
                    if c.get('id') in selected:c.set('style',c.get('style','')+'jumpStyle=arc;jumpSize=10;')
                source.write_bytes(ET.tostring(tree.getroot(),encoding='utf-8',xml_declaration=True))
                route_result={'strategy':'explicit-local-crossing-polish','jump_edges':selected,'review_flags':flags}
            native=ET.parse(source).getroot();edges=[c for c in native.iter('mxCell') if c.get('edge')=='1' and c.get('pjSyntheticRoutingHelper')!='1']
            counts={'fixed_endpoints':sum(sum(k in style(c.get('style','')) for k in ('exitX','entryX')) for c in edges),
                    'jumps':sum(style(c.get('style','')).get('jumpStyle') in ('arc','gap','sharp') for c in edges)}
            result={'estimated':selected,'qa_mode':report.get('qa_mode','legacy-explicit'),'review_flags':report.get('review_flags',[]),'routing':route_result,**counts}
            if a.render:
                exported=export(source,formats=['svg','png'],output_dir=folder)
                portable={k:exported[k] for k in ('source_sha256','drawio_version','page_index')}
                portable.update(source=source.relative_to(ROOT).as_posix(),files=[{**f,'path':Path(f['path']).relative_to(ROOT).as_posix()} for f in exported['files']])
                Path(exported['manifest']).write_text(json.dumps(portable,indent=2)+'\n',encoding='utf-8')
                cmd=['node',str(ROOT/'scripts/audit_svg.cjs'),str(folder/(case+'.svg')),'--target-width-mm','160','--model',str(fixture)]
                audit=json.loads(subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=45,check=True).stdout)
                audit['source']=(folder/(case+'.svg')).relative_to(ROOT).as_posix()
                (folder/(case+'.rendered.json')).write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
                view=ET.parse(folder/(case+'.svg')).getroot().get('viewBox').split();w,h=map(float,view[2:])
                result.update(rendered=audit['post_routing'],font_pt=audit['metrics']['projected_min_font_pt'],height_mm=h/w*160)
            row['versions'][version]=result
        row['semantic_inventory_matched']=inventory(ET.parse(out/'v02'/(case+'.drawio')).getroot())==inventory(ET.parse(out/'v03'/(case+'.drawio')).getroot())
        if not row['semantic_inventory_matched']:raise ValueError('Semantic mismatch: '+case)
        if a.render:
            images=[Image.open(out/v/(case+'.png')).convert('RGB') for v in ('v02','v03')]
            for im in images:im.thumbnail((980,1400))
            canvas=Image.new('RGB',(2020,max(im.height for im in images)+70),'#F2F5F7');draw=ImageDraw.Draw(canvas)
            for x,label,im in zip((20,1030),('V0.2','V0.3'),images):draw.text((x,10),label,font=font(24,True),fill='#182B3B');canvas.paste(im,(x,60))
            canvas.save(out/(case+'-comparison.png'))
        rows.append(row);print(case,[(v,r['fixed_endpoints'],r.get('height_mm')) for v,r in row['versions'].items()],flush=True)
    (out/'metrics.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
