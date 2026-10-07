import base64
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.parse
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from extract_style import extract_style

class ExtractStyleTests(unittest.TestCase):
    def test_explicit_dominance_ties_and_compressed_pages(self):
        xml='<mxGraphModel><root><mxCell id="a" vertex="1" style="fillColor=#FFFFFF;fontSize=20;"/><mxCell id="b" vertex="1" style="fillColor=#000000;fontSize=20;"/><mxCell id="e" edge="1" style="strokeColor=#123456;dashed=1;"/></root></mxGraphModel>'
        compressed=zlib.compressobj(wbits=-15)
        data=compressed.compress(urllib.parse.quote(xml).encode())+compressed.flush()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'native.drawio'
            path.write_text('<mxfile><diagram>'+base64.b64encode(data).decode()+'</diagram></mxfile>')
            before=path.read_bytes(); result=extract_style(path)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(result['vertex_style'],{'fillColor':'#000000','fontSize':'20'})
            self.assertEqual(result['edge_style']['dashed'],'1')
            self.assertEqual(result['coverage']['cells'],{'vertex':2,'edge':1})
    def test_no_invented_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'native.drawio'; path.write_text('<mxGraphModel><root><mxCell vertex="1"/></root></mxGraphModel>')
            self.assertEqual(extract_style(path)['vertex_style'],{})
