import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from probe_drawio import SMOKE
from elk_drawio import layout_elk

class ElkAdapterTests(unittest.TestCase):
    def exercise(self,returned,**kwargs):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'src').mkdir();(p/'src/elk-pass.js').write_text('external stub')
            source=p/'in.drawio';source.write_text(SMOKE);out=p/'out.drawio'
            with patch('elk_drawio.subprocess.run',return_value=SimpleNamespace(stdout=returned)) as run:
                result=layout_elk(source,out,p,**kwargs)
            self.assertEqual(source.read_text(),SMOKE)
            return result,run.call_args.args[0]
    def test_unchanged_unverified(self):
        self.assertEqual(self.exercise(SMOKE)[0]['status'],'unchanged-unverified')
    def test_placement_moves_but_semantics_preserved(self):
        self.assertTrue(self.exercise(SMOKE.replace('x="400"','x="122"'))[0]['changed'])
    def test_no_invented_compact_options(self):
        result,args=self.exercise(SMOKE,preset='elk-flow-compact',direction='vertical')
        self.assertIn('Limited alias',result['preset_scope']);self.assertEqual(args[-1],'vertical')
    def test_reject_semantics_sizes_or_hierarchy_changes(self):
        for text in (SMOKE.replace('value="A"','value="Other"'),SMOKE.replace('width="80"','width="81"'),SMOKE.replace('source="a"','source="b"'),SMOKE.replace('parent="1" vertex','parent="a" vertex')):
            with self.assertRaises(ValueError):self.exercise(text)
    def test_reject_unknown_preset(self):
        with self.assertRaises(ValueError):self.exercise(SMOKE,preset='arbitrary')
    def test_fixed_attachment_change_is_rejected_before_output(self):
        original=SMOKE.replace('edgeStyle=orthogonalEdgeStyle;', 'exitX=1;exitY=0.25;entryX=0;entryY=0.75;edgeStyle=orthogonalEdgeStyle;')
        revised=original.replace('exitY=0.25','exitY=0.5')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'src').mkdir();(p/'src/elk-pass.js').write_text('external stub')
            source=p/'in.drawio';source.write_text(original);out=p/'out.drawio'
            with patch('elk_drawio.subprocess.run',return_value=SimpleNamespace(stdout=revised)):
                with self.assertRaisesRegex(ValueError,'fixed attachments'):layout_elk(source,out,p)
            self.assertFalse(out.exists())
