"""Acceptance inventory for the requested pilot semantics, independent of layout."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class PilotSemantics(unittest.TestCase):
    def cells(self, case):
        return ET.parse(ROOT / f"examples/{case}/{case}.drawio").findall(".//mxCell")

    def test_process_has_both_outcomes_and_retry(self):
        cells = self.cells("process")
        edges = {c.get('id'): c for c in cells if c.get('edge') == '1'}
        self.assertEqual({(c.get('source'), c.get('target')) for c in edges.values()}, {
            ('receive','exposure'), ('exposure','usable'), ('usable','evaluate'),
            ('evaluate','save'), ('usable','light'), ('light','exposure')})
        self.assertEqual(edges['p3'].get('value'), 'Ano')
        self.assertEqual(edges['p5'].get('value'), 'Ne')

    def test_topology_keeps_control_and_service(self):
        edges = [c for c in self.cells('topology') if c.get('edge') == '1']
        self.assertEqual({(c.get('source'), c.get('target')) for c in edges}, {
            ('camera','switch'), ('switch','ipc'), ('ipc','mes'),
            ('service','switch'), ('plc','camera'), ('ipc','plc')})

    def test_training_does_not_invent_card_sequence(self):
        cells = self.cells('dense-training')
        edges = [c for c in cells if c.get('edge') == '1']
        self.assertEqual({(c.get('source'),c.get('target')) for c in edges}, {
            ('acquisition','evaluation'), ('evaluation','operation')})
        self.assertEqual({c.get('id') for c in cells if c.get('parent') in {'acquisition','evaluation','operation'}},
                         {'optics','lighting','dataset','model','integration','diagnostics'})


if __name__ == '__main__':
    unittest.main()
