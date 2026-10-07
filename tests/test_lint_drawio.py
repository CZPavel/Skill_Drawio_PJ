import base64
import importlib.util
from pathlib import Path
import tempfile
import unittest
import urllib.parse
import zlib

SPEC = importlib.util.spec_from_file_location('lint_drawio', Path(__file__).resolve().parents[1]/'scripts/lint_drawio.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
STYLE = 'fillColor=#EEF4FA;strokeColor=#245C91;strokeWidth=2;fontColor=#182B3B;fontFamily=Arial;fontSize=18;whiteSpace=wrap;'


def node(ident, x=20, y=20, w=200, h=80, parent='1', value='PLC', extra=''):
    return f'<mxCell id="{ident}" vertex="1" parent="{parent}" value="{value}" style="{STYLE}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" {extra} as="geometry"/></mxCell>'


def model(content):
    return '<mxGraphModel pageWidth="1000" pageHeight="800"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'+content+'</root></mxGraphModel>'


class LintTests(unittest.TestCase):
    def check_xml(self, xml, **kwargs):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'test.drawio'
            p.write_text(xml, encoding='utf-8')
            original = p.read_bytes()
            result = MODULE.lint(p, **kwargs)
            self.assertEqual(original,p.read_bytes())
            return result

    def codes(self, result):
        return {f['code'] for f in result['findings']}

    def test_clean_native_and_metrics(self):
        r = self.check_xml(model(node('a')),target_width_mm=160)
        self.assertFalse(r['findings'])
        self.assertEqual(r['metrics']['pages'][0]['width_px'],200)
        self.assertGreater(r['metrics']['pages'][0]['projected_min_font_pt'],9)

    def test_compressed_multiple_pages_and_wrapper(self):
        xml=model('<UserObject id="a" label="Český text">'+node('ignored')+'</UserObject>')
        compressor=zlib.compressobj(wbits=-15)
        encoded=base64.b64encode(compressor.compress(urllib.parse.quote(xml).encode())+compressor.flush()).decode()
        r=self.check_xml('<mxfile><diagram name="A">'+encoded+'</diagram><diagram name="B">'+xml+'</diagram></mxfile>')
        self.assertEqual(len(r['metrics']['pages']),2)
        self.assertFalse(r['findings'])

    def test_nested_relative_offset(self):
        child=node('b',.5,.5,20,20,'a',extra='relative="1"').replace('/></mxCell>','><mxPoint x="3" y="4" as="offset"/></mxGeometry></mxCell>')
        r=self.check_xml(model(node('a',100,100,400,300)+child))
        self.assertNotIn('node-overlap',self.codes(r))
        # Add unrelated rectangle exactly at resolved child coordinates.
        r=self.check_xml(model(node('a',100,100,400,300)+child+node('c',303,254,20,20)))
        self.assertIn('node-overlap',self.codes(r))

    def test_ancestor_allowed_unrelated_overlap_and_outside_child(self):
        r=self.check_xml(model(node('a',0,0,400,300)+node('b',30,30,100,80,'a')))
        self.assertNotIn('node-overlap',self.codes(r))
        r=self.check_xml(model(node('a')+node('b',30,30)+node('c',190,0,100,80,'a')))
        self.assertIn('node-overlap',self.codes(r))
        self.assertIn('container-overflow',self.codes(r))

    def test_structural_duplicate_dangling_cycle_and_missing_geometry(self):
        r=self.check_xml(model(node('a',parent='b')+node('b',parent='a')+node('a')+'<mxCell id="edge" edge="1" parent="1" target="gone"/>'))
        self.assertTrue({'id-duplicate','reference-dangling','geometry-missing'} <= self.codes(r))
        r=self.check_xml(model(node('a',parent='b')+node('b',parent='a')))
        self.assertIn('parent-cycle',self.codes(r))

    def test_czech_long_text_and_inline_size_readability(self):
        r=self.check_xml(model(node('a',w=120,h=30,value='Řízení průmyslové kamery a vyhodnocení detekovaných součástí')))
        self.assertIn('text-overflow-height-estimated',self.codes(r))
        r=self.check_xml(model(node('a',w=900,value='&lt;span style=&quot;font-size:6px&quot;&gt;Malý text&lt;/span&gt;')),target_width_mm=160)
        self.assertIn('target-font-small',self.codes(r))
        self.assertEqual(r['metrics']['pages'][0]['font_min_px'],6)
        self.assertIn('html-text-estimated',self.codes(r))

    def test_auto_routing_never_claims_coverage(self):
        edge='<mxCell id="e" edge="1" source="a" target="b" value="data"><mxGeometry relative="1" as="geometry"/></mxCell>'
        r=self.check_xml(model(node('a')+node('b',300)+edge))
        self.assertIn('edge-path-unresolved',self.codes(r))
        self.assertIn('edge-label-unresolved',self.codes(r))
        self.assertEqual(r['metrics']['pages'][0]['explicit_paths'],0)

    def test_explicit_edges_cross_nodes_each_other_short_terminal(self):
        def edge(ident,x1,y1,x2,y2):
            return f'<mxCell id="{ident}" edge="1" parent="1" style="strokeColor=#245C91;strokeWidth=2;"><mxGeometry as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" as="targetPoint"/></mxGeometry></mxCell>'
        r=self.check_xml(model(node('a',40,40,80,80)+edge('e',0,80,200,80)+edge('f',80,0,80,200)+edge('g',300,0,310,0)))
        self.assertTrue({'edge-node','edge-edge','edge-terminal'} <= self.codes(r))
        self.assertEqual(r['metrics']['pages'][0]['explicit_paths'],3)

    def test_contrast_canvas_and_invalid(self):
        r=self.check_xml(model(node('a',-20).replace('#182B3B','#EEF4FA')))
        self.assertTrue({'text-contrast','canvas-bounds'} <= self.codes(r))
        self.assertTrue(self.check_xml('<broken')['fatal'])

    def test_invalid_coordinate_and_edge_relative_label_uncertainty(self):
        r=self.check_xml(model(node('a',x='NaN')))
        self.assertIn('geometry-number',self.codes(r))
        edge='<mxCell id="e" edge="1" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>'
        r=self.check_xml(model(edge+node('label',parent='e',extra='relative="1"')))
        self.assertIn('node-geometry-unresolved',self.codes(r))
        self.assertEqual(r['metrics']['pages'][0]['nodes'],0)

    def test_html_block_boundaries_not_blank_lines(self):
        self.assertEqual(MODULE.label_text('<div>První</div><div>Druhý</div>'),'První\nDruhý')
        self.assertEqual(MODULE.label_text('<div>První<br><br>Druhý</div>'),'První\n\nDruhý')
        label='&lt;div&gt;První&lt;/div&gt;&lt;div&gt;Druhý&lt;/div&gt;'
        r=self.check_xml(model(node('a',w=200,h=49,value=label)))
        self.assertNotIn('text-overflow-height-estimated',self.codes(r))


if __name__ == '__main__':
    unittest.main()
