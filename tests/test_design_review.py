import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from design_review import review_design,semantic_inventory

class DesignTests(unittest.TestCase):
    def test_recommendations_preserve_text_and_simple_graph_has_no_legend(self):
        m={'nodes':[{'id':'a','kind':'action','title':'Kontrola'},
                    {'id':'b','shape':'decision','title':'Kontrola OK'}]}
        flags=review_design(m)
        self.assertIn('design:a:action-verb-object-recommended',flags)
        self.assertIn('design:b:decision-question-or-condition-recommended',flags)
        self.assertNotIn('design:legend-recommended',flags)
        self.assertEqual(m['nodes'][0]['title'],'Kontrola')

    def test_explicit_levels_shapes_and_legend_threshold(self):
        m={'nodes':[{'id':'a','kind':'device','shape':'rectangle','role':'data','abstraction_level':'system'},
                    {'id':'b','kind':'device','shape':'ellipse','role':'control','abstraction_level':'port'},
                    {'id':'c','role':'note'}]}
        self.assertIn('design:legend-recommended',review_design(m))
        self.assertIn('design:shape-consistency:device',review_design(m))
        self.assertIn('design:abstraction-levels:overview-detail-recommended',review_design(m))
        m.update(legend=True,mixed_abstraction_reason='Detail callout')
        self.assertNotIn('design:legend-recommended',review_design(m))

    def test_synthetic_helpers_excluded(self):
        m={'nodes':[{'id':'a'},{'id':'helper','synthetic_routing_helper':True}],
           'edges':[{'id':'trunk','synthetic_routing_helper':True},
                    {'id':'branch','logical_edge_id':'original'}]}
        self.assertEqual(semantic_inventory(m),{'nodes':['a'],'edges':['original']})
