import sys
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from probe_drawio import SMOKE,desktop_smoke,probe

class ProbeTests(unittest.TestCase):
    def test_missing_installation_is_unavailable(self):
        with patch('probe_drawio.discover_drawio',side_effect=ValueError('missing')):
            result=probe(mcp_root='missing-package')
        self.assertEqual(result['desktop_libavoid']['status'],'unavailable');self.assertEqual(result['elk']['status'],'unavailable')
    def test_unknown_layout_is_unsupported(self):
        with patch('probe_drawio.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='',stderr='Unknown layout: libavoid')):
            self.assertEqual(desktop_smoke('drawio','source',Path('missing'),'libavoid')['status'],'unsupported')
    def test_unchanged_success_does_not_verify(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.drawio';out.write_text(SMOKE)
            with patch('probe_drawio.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='',stderr='')):
                self.assertEqual(desktop_smoke('drawio','source',out,'libavoid')['status'],'unverified')
    def test_libavoid_node_move_not_verified(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.drawio';out.write_text(SMOKE.replace('x="400"','x="200"'))
            with patch('probe_drawio.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='',stderr='')):
                self.assertEqual(desktop_smoke('drawio','source',out,'libavoid')['status'],'unverified')
