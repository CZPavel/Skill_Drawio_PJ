"""Explicit, one-run diagnostics; no persistent capability database."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from route_drawio import route
from export_drawio import discover_drawio

SMOKE = '''<mxfile><diagram name="Probe"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="a" parent="1" vertex="1" value="A"><mxGeometry x="0" y="100" width="80" height="60" as="geometry"/></mxCell><mxCell id="b" parent="1" vertex="1" value="B"><mxGeometry x="400" y="100" width="80" height="60" as="geometry"/></mxCell><mxCell id="obstacle" parent="1" vertex="1" value="Obstacle"><mxGeometry x="180" y="70" width="100" height="120" as="geometry"/></mxCell><mxCell id="e" parent="1" edge="1" source="a" target="b" style="edgeStyle=orthogonalEdgeStyle;html=1;"><mxGeometry relative="1" as="geometry"/></mxCell></root></mxGraphModel></diagram></mxfile>'''

def desktop_smoke(executable, source, output, layout):
    run=subprocess.run([str(executable),'--disable-gpu','-x','-f','xml','-u','--layout',layout,'-o',str(output),str(source)],capture_output=True,text=True,encoding='utf-8',timeout=60)
    message=(run.stdout+'\n'+run.stderr).strip()
    if run.returncode or not output.is_file():
        return {'status':'unsupported' if re.search(r'unknown|invalid|unsupported|not found',message,re.I) else 'unverified','detail':message[-1800:]}
    revised=output.read_text(encoding='utf-8-sig')
    # Serialized geometry equality alone is whitespace-sensitive. Compare attributes/points.
    def snapshot(text,kind):
        from lint_drawio import pages
        return [(c.get('id'),[(e.tag,dict(e.attrib)) for e in c.find('mxGeometry').iter()]) for _,m in pages(ET.fromstring(text)) for c in m.iter('mxCell') if c.get(kind)=='1']
    nodes_changed=snapshot(SMOKE,'vertex')!=snapshot(revised,'vertex')
    edges_changed=snapshot(SMOKE,'edge')!=snapshot(revised,'edge')
    verified=(edges_changed and not nodes_changed) if layout=='libavoid' else nodes_changed
    return {'status':'verified' if verified else 'unverified','nodes_changed':nodes_changed,'edge_geometry_changed':edges_changed,'detail':message[-1800:]}

def probe(drawio=None,mcp_root=None):
    report={'desktop_version':None,'desktop_layout_help':None,'desktop_libavoid':{'status':'unavailable'},'desktop_elk':{'status':'unavailable'},'mcp_libavoid':{'status':'unavailable'},'elk':{'status':'unavailable'}}
    with tempfile.TemporaryDirectory(prefix='drawio-probe-') as temp:
        base=Path(temp);source=base/'probe.drawio';source.write_text(SMOKE,encoding='utf-8')
        try:
            exe=discover_drawio(drawio)
            version=subprocess.run([str(exe),'--version'],capture_output=True,text=True,timeout=20)
            report['desktop_version']=version.stdout.strip()
            help_run=subprocess.run([str(exe),'--help'],capture_output=True,text=True,timeout=20)
            report['desktop_layout_help']=next((s.strip() for s in help_run.stdout.splitlines() if '--layout' in s),None)
            for key,layout in [('desktop_libavoid','libavoid'),('desktop_elk','horizontalFlow')]:
                try: report[key]=desktop_smoke(exe,source,base/(key+'.drawio'),layout)
                except (OSError,ValueError,ET.ParseError,subprocess.SubprocessError) as error: report[key]={'status':'unverified','detail':str(error)}
        except (OSError,ValueError,subprocess.SubprocessError) as error:
            report['desktop_detail']=str(error)
        if mcp_root:
            for key,module in [('mcp_libavoid','libavoid-pass.js'),('elk','elk-pass.js')]:
                if not (Path(mcp_root)/'src'/module).is_file():continue
                try:
                    if key=='mcp_libavoid':
                        result=route(source,base/'mcp.drawio',mcp_root)
                        revised=(base/'mcp.drawio').read_text(encoding='utf-8')
                        points=[(float(p.get('x')),float(p.get('y'))) for p in ET.fromstring(revised).findall('.//Array/mxPoint')]
                        detour=bool(points) and any(y<70 or y>190 for x,y in points)
                        report[key]={'status':'verified' if result['changed'] and detour else 'unverified','obstacle_detour':detour,'result':result}
                    else:
                        from elk_drawio import layout_elk
                        result=layout_elk(source,base/'elk.drawio',mcp_root)
                        revised=(base/'elk.drawio').read_text(encoding='utf-8')
                        def positions(text):
                            return [(c.get('id'),dict(c.find('mxGeometry').attrib)) for c in ET.fromstring(text).iter('mxCell') if c.get('vertex')=='1']
                        moved=positions(SMOKE)!=positions(revised)
                        report[key]={'status':'verified' if moved else 'unverified','nodes_changed':moved,'result':result}
                except (OSError,ValueError,ET.ParseError,subprocess.SubprocessError) as error:report[key]={'status':'unverified','detail':str(error)}
    # Current PJ external adapters do not expose/test side masks through these
    # official interfaces. Successful floating routing is not side support.
    for key in ('desktop_libavoid','desktop_elk','mcp_libavoid','elk'):
        report[key]['supports_side_constraints']=False
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--drawio');parser.add_argument('--mcp-root');parser.add_argument('--json',type=Path)
    args=parser.parse_args();result=probe(args.drawio,args.mcp_root);text=json.dumps(result,indent=2,ensure_ascii=False)
    if args.json:args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(text,encoding='utf-8')
    print(text)
