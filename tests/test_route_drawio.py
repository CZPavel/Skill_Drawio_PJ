import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from route_drawio import route
from route_drawio import has_side_constraints

XML='<mxfile><diagram name="P"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="a" parent="1" vertex="1" value="Kamera"><mxGeometry x="0" y="0" width="100" height="80" as="geometry"/></mxCell><mxCell id="e" parent="1" edge="1" source="a" target="a" value="Zpět"><mxGeometry relative="1" as="geometry"/></mxCell></root></mxGraphModel></diagram></mxfile>'
class RouteAdapterTests(unittest.TestCase):
    def test_side_constraints_detected_in_compressed_pages(self):
        import base64,zlib
        from urllib.parse import quote
        from xml.sax.saxutils import escape
        graph='<mxGraphModel><root><mxCell id="e" edge="1" style="sourcePortConstraint=north;"/></root></mxGraphModel>'
        compressor=zlib.compressobj(wbits=-15)
        payload=base64.b64encode(compressor.compress(quote(graph).encode())+compressor.flush()).decode()
        self.assertTrue(has_side_constraints('<mxfile><diagram>'+payload+'</diagram></mxfile>'))
        self.assertTrue(has_side_constraints('<mxfile><diagram>'+graph+'</diagram></mxfile>'))
        self.assertFalse(has_side_constraints(XML))
    def exercise(self,returned):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'src').mkdir();(p/'src/libavoid-pass.js').write_text('external stub')
            source=p/'input.drawio';source.write_text(XML,encoding='utf-8');out=p/'output.drawio'
            with patch('route_drawio.subprocess.run',return_value=SimpleNamespace(stdout=returned)):
                result=route(source,out,p)
            self.assertEqual(source.read_text(encoding='utf-8'),XML)
            return result
    def test_unchanged_engine_fallback_is_unverified(self):
        self.assertEqual(self.exercise(XML)['status'],'unchanged-unverified')
    def test_edge_geometry_change_permitted(self):
        changed=XML.replace('relative="1"','relative="1" x="0.2"')
        self.assertTrue(self.exercise(changed)['changed'])
    def test_semantic_or_node_change_rejected(self):
        for changed in (XML.replace('Kamera','PLC'),XML.replace('width="100"','width="200"'),
                        XML.replace('id="e" parent','id="e" style="endArrow=none;" parent'),
                        XML.replace('<mxGraphModel>','<mxGraphModel pageWidth="999">')):
            with self.assertRaises(ValueError):self.exercise(changed)
