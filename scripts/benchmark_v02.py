"""Bounded V0.2 no-coordinate acceptance and matched archived pilot comparison."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from build_diagram import build, font
from layout_diagram import layout
from export_drawio import export

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',action='store_true',help='Render selected layouts only; requires Desktop/browser')
    parser.add_argument('--mcp-root',type=Path,help='Optional external @drawio/mcp package for libavoid routing')
    parser.add_argument('--cases',nargs='+',help='Recheck only changed cases, retaining other measured rows')
    args=parser.parse_args()
    out=ROOT/'benchmark/v02';out.mkdir(exist_ok=True)
    models=[]
    # Same semantics and fonts as V0.1; remove geometry and old routing overrides.
    for case in ('process','topology','dense-training'):
        m=json.loads((ROOT/f'examples/{case}/model.json').read_text(encoding='utf-8'))
        m.update(semantic=True,direction='auto',archetype='grouped-training' if case=='dense-training' else 'network-topology' if case=='topology' else 'process-flow')
        for n in m.get('groups',[])+m['nodes']:
            for k in ('x','y','width','height'):n.pop(k,None)
        for e in m.get('edges',[]):
            for k in ('points','style','label_position','label_offset'):e.pop(k,None)
            if case=='process' and e['id']=='p6':e['type']='retry'
        models.append((case,m,True))
    for path in sorted((ROOT/'examples/ir').glob('*.json')):
        models.append((path.stem,json.loads(path.read_text(encoding='utf-8')),False))
    rows=json.loads((out/'metrics.json').read_text(encoding='utf-8')) if args.cases and (out/'metrics.json').exists() else []
    for case,m,matched in models:
        if args.cases and case not in args.cases:continue
        rows=[r for r in rows if r['case']!=case]
        start=time.perf_counter();placed,report=layout(m);elapsed=time.perf_counter()-start
        selected=next(c for c in report['candidates'] if c['name']==report['selected'])
        source=out/f'{case}.drawio';ir=out/f'{case}.ir.json'
        ir.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        build(m,source)
        row=dict(case=case,matched=matched,candidates=len(report['candidates']),selected=report['selected'],estimated=selected,review_flags=report['review_flags'],layout_seconds=round(elapsed,4),render_passes=0)
        if args.mcp_root and 'native-routing-review' in report['review_flags']:
            from route_drawio import route, repair_generated_labels
            routed=out/f'{case}.routed.drawio'
            row['routing']=route(source,routed,args.mcp_root)
            source.write_bytes(routed.read_bytes());routed.unlink()
            row['label_repair']=repair_generated_labels(source,m)
        (out/f'{case}.layout.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        if args.render:
            exported=export(source,formats=['svg','png'],output_dir=out)
            portable={k:exported[k] for k in ('source_sha256','drawio_version','page_index')}
            portable['source']=source.relative_to(ROOT).as_posix()
            portable['files']=[{**f,'path':Path(f['path']).relative_to(ROOT).as_posix()} for f in exported['files']]
            Path(exported['manifest']).write_text(json.dumps(portable,indent=2)+'\n',encoding='utf-8')
            width=m.get('profile_overrides',{}).get('target_width_mm',300 if m.get('target',m.get('profile'))=='presentation' else 160)
            cmd=['node',str(ROOT/'scripts/audit_svg.cjs'),str(out/f'{case}.svg'),'--target-width-mm',str(width)]
            result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=45,check=True)
            audit=json.loads(result.stdout);audit['source']=(out/f'{case}.svg').relative_to(ROOT).as_posix()
            (out/f'{case}.rendered.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
            view=ET.parse(out/f'{case}.svg').getroot().get('viewBox').split();w,h=map(float,view[2:])
            row.update(render_passes=1,rendered=audit['metrics'],findings=dict(Counter(x['code'] for x in audit['findings'])),height_at_target_mm=h/w*width)
        rows.append(row)
        print(case,report['selected'],selected['score'],row.get('height_at_target_mm'))
    (out/'metrics.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    if args.render:
        for case in ('process','topology','dense-training'):
            images=[]
            for directory in ('official','pj','v02'):
                im=Image.open(ROOT/f'benchmark/{directory}/{case}.png').convert('RGB');im.thumbnail((700,1600));images.append(im)
            canvas=Image.new('RGB',(2220,max(im.height for im in images)+90),'#F2F5F7');draw=ImageDraw.Draw(canvas)
            for x,label,im in zip((20,760,1500),('Official archived','PJ V0.1 curated','PJ V0.2 no coordinates'),images):
                draw.text((x,20),label,font=font(25,True),fill='#182B3B');canvas.paste(im,(x,75))
            canvas.save(out/f'{case}-comparison.png')
if __name__=='__main__':main()
