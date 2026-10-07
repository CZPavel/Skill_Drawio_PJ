import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_diagram import build
from fanout_junction import add_junction,inventory

class FanoutTests(unittest.TestCase):
    def test_explicit_helper_keeps_logical_nodes_edges_labels(self):
        m={'semantic':True,'archetype':'network-topology','direction':'LR','nodes':[{'id':'s','title':'Source','x':0,'y':200,'width':220}]+[
            {'id':'n'+str(i),'title':'Target','x':600,'y':i*130,'width':220} for i in range(4)],
           'edges':[{'id':'e'+str(i),'source':'s','target':'n'+str(i),'label':'Data'} for i in range(4)]}
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'in.drawio';out=Path(d)/'out.drawio';build(m,source);original=source.read_bytes()
            result=add_junction(source,out,'s')
            self.assertEqual(source.read_bytes(),original)
            self.assertEqual(inventory(ET.parse(source).getroot()),inventory(ET.parse(out).getroot()))
            self.assertEqual(result['branches'],4)
            helpers=ET.parse(out).findall('.//mxCell[@pjSyntheticRoutingHelper="1"]')
            self.assertEqual(len(helpers),2)
            with self.assertRaises(ValueError):add_junction(source,source,'s')
            tree=ET.parse(source)
            edge=tree.find('.//mxCell[@id="e0"]')
            edge.set('style',edge.get('style')+'exitX=1;exitY=0.25;')
            tree.write(source)
            with self.assertRaises(ValueError):add_junction(source,out,'s')
