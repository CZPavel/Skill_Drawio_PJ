"""Semantic-input acceptance: tooling supplies geometry without content loss."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from layout_diagram import layout, validate_ir, automatic_ports, choose_card_width
from build_diagram import build, TOKENS, measure

FIXTURES=Path(__file__).resolve().parents[1]/'examples/ir'

class SemanticLayoutTests(unittest.TestCase):
    def test_fixtures_deterministic_bounded_and_semantically_preserved(self):
        fixtures=sorted(FIXTURES.glob('*.json'))
        self.assertEqual(len(fixtures),9)
        for fixture in fixtures:
            with self.subTest(fixture=fixture.name):
                source=json.loads(fixture.read_text(encoding='utf-8'))
                original=copy.deepcopy(source)
                for item in source['nodes']+source['groups']:
                    self.assertNotIn('x',item); self.assertNotIn('y',item)
                placed,report=layout(source)
                self.assertEqual(source,original,'Layout must not mutate semantic input')
                self.assertEqual(layout(source),(placed,report))
                self.assertGreaterEqual(len(report['candidates']),2)
                self.assertLessEqual(len(report['candidates']),12)
                self.assertIn(report['selected'],[c['name'] for c in report['candidates']])
                for kind in ('nodes','edges'):
                    output={item['id']:item for item in placed[kind]}
                    for item in source[kind]:
                        for key in ('title','body','source','target','label','role'):
                            if key in item: self.assertEqual(output[item['id']][key],item[key])
                with tempfile.TemporaryDirectory() as tmp:
                    path=Path(tmp)/'diagram.drawio'; build(source,path)
                    cells={c.get('id'):c for c in ET.parse(path).iter('mxCell')}
                    for edge in source['edges']:
                        self.assertEqual(cells[edge['id']].get('source'),edge['source'])
                        self.assertEqual(cells[edge['id']].get('target'),edge['target'])

    def test_group_autosizing_contains_direct_children(self):
        source=json.loads((FIXTURES/'nested-groups.json').read_text(encoding='utf-8'))
        placed,_=layout(source)
        groups={g['id']:g for g in placed['groups']}
        for item in placed['groups']+placed['nodes']:
            parent=item.get('parent')
            if parent in groups:
                group=groups[parent]
                self.assertGreaterEqual(item['x'],0); self.assertGreaterEqual(item['y'],0)
                self.assertLessEqual(item['x']+item['width'],group['width'])
                self.assertLessEqual(item['y']+item['height'],group['height'])

    def test_card_width_meets_measured_long_text_height(self):
        source=json.loads((FIXTURES/'long-czech.json').read_text(encoding='utf-8'))
        node=source['nodes'][0]; profile=TOKENS['profiles']['document']
        width,height=choose_card_width(node,profile,source)
        self.assertGreater(width,0)
        required=measure(node['title'],node['body'],width,profile)[2]
        self.assertGreaterEqual(height,required)

    def test_ports_follow_relative_geometry_and_override(self):
        source=(0,0,100,100)
        for target,expected in [((200,0,100,100),(1,.5,0,.5)),((-200,0,100,100),(0,.5,1,.5)),((0,200,100,100),(.5,1,.5,0)),((0,-200,100,100),(.5,0,.5,1))]:
            ports=automatic_ports(source,target)
            self.assertEqual(tuple(float(ports[k]) for k in ('exitX','exitY','entryX','entryY')),expected)
        ports=automatic_ports(source,(200,0,100,100),{'source':'bottom','target':'top'})
        self.assertEqual(float(ports['exitY']),1); self.assertEqual(float(ports['entryY']),0)

    def test_explicit_orientation_is_respected(self):
        for direction in ('LR','TB'):
            placed,report=layout(json.loads((FIXTURES/('process-'+direction.lower()+'.json')).read_text(encoding='utf-8')))
            self.assertTrue(report['selected'].startswith(direction))
            first,last=placed['nodes'][0],placed['nodes'][-1]
            self.assertGreater(last['x' if direction=='LR' else 'y'],first['x' if direction=='LR' else 'y'])

    def test_validation_rejects_broken_semantic_references(self):
        valid={'nodes':[{'id':'a','title':'A'}],'edges':[]}
        validate_ir(valid)
        for patch in [dict(nodes=[{'id':'a','title':'A'},{'id':'a','title':'B'}]),dict(edges=[{'source':'a','target':'missing'}]),dict(direction='diagonal'),dict(nodes=[{'id':'a','title':'A','group':'missing'}])]:
            with self.subTest(patch=patch),self.assertRaises(ValueError): validate_ir({**valid,**patch})

class ScoreContractTests(unittest.TestCase):
    def test_critical_overlap_penalty_exceeds_minor_spacing_penalty(self):
        from score_layout import score_layout
        model={'nodes':[{'id':'a','title':'A','x':0,'y':0,'width':100,'height':100},
                        {'id':'b','title':'B','x':200,'y':0,'width':100,'height':100}], 'edges':[]}
        clean=score_layout(model)
        crowded=copy.deepcopy(model); crowded['nodes'][1]['x']=50
        bad=score_layout(crowded)
        self.assertEqual(clean['node_overlaps'],0); self.assertEqual(bad['node_overlaps'],1)
        self.assertLess(bad['score'],clean['score'])
        self.assertGreater(bad['penalties']['node_overlaps'],sum(value for key,value in bad['penalties'].items() if key in ('aspect','whitespace','bends','edge_length')))

    def test_edge_crossing_unrelated_node_is_reported(self):
        from score_layout import score_layout
        model={'nodes':[{'id':name,'title':name,'x':x,'y':0,'width':100,'height':100} for name,x in [('a',0),('obstacle',200),('b',400)]],
               'edges':[{'source':'a','target':'b'}]}
        result=score_layout(model)
        self.assertEqual(result['edge_node_collisions'],1)
        self.assertGreater(result['penalties']['edge_node_collisions'],0)


class TargetProjectionRegressionTests(unittest.TestCase):
    def test_standalone_has_no_physical_projection(self):
        placed,report=layout({'target':'standalone','nodes':[{'id':'a','title':'A'}]})
        self.assertIsNone(report['candidates'][0]['projected_min_font_pt'])

    def test_presentation_projection_is_height_bounded(self):
        from score_layout import score_layout
        model={'target':'presentation','nodes':[{'id':'a','title':'A','x':0,'y':0,'width':300,'height':1496}]}
        report=score_layout(model)
        self.assertEqual(report['projection_constraint'],'height')
        self.assertLess(report['projected_min_font_pt'],11)
        self.assertAlmostEqual(report['target_height_mm'],168.75)

    def test_grouped_cards_stack_independently_of_root(self):
        model={'archetype':'grouped-training','direction':'LR','groups':[{'id':'g','title':'Group'}],
               'nodes':[{'id':key,'title':key,'group':'g'} for key in ('a','b')]}
        placed,_=layout(model)
        a,b=placed['nodes']
        self.assertEqual(a['x'],b['x'])
        self.assertLess(a['y']+a['height'],b['y'])

    def test_network_secondary_links_do_not_precede_primary_camera(self):
        model={'archetype':'network-topology','direction':'LR','nodes':[{'id':key,'title':key} for key in ('camera','switch','plc')],
               'edges':[{'source':'camera','target':'switch'},{'source':'plc','target':'camera','role':'control'}]}
        placed,_=layout(model)
        camera,switch,plc=placed['nodes']
        self.assertEqual(camera['x'],plc['x'])
        self.assertLess(camera['x'],switch['x'])


class RoutedLabelRepairTests(unittest.TestCase):
    def test_long_label_reserves_horizontal_gap(self):
        model={'direction':'LR','nodes':[{'id':'a','title':'A'},{'id':'b','title':'B'}],
               'edges':[{'source':'a','target':'b','label':'Dlouhy popisek spojeni'}]}
        placed,_=layout(model)
        a,b=placed['nodes']
        from build_diagram import font
        required=font(TOKENS['profiles']['document']['edge']).getlength(model['edges'][0]['label'])
        self.assertGreaterEqual(b['x']-a['x']-a['width'],required+32)

    def test_actual_polyline_bounds_offset_and_reports_obstructed_label(self):
        from layout_diagram import _labels
        profile={**TOKENS['profiles']['document'],'edge':40}
        model={'nodes':[{'id':'obstacle'}],'edges':[{'id':'e','source':'a','target':'b','label':'Route'}]}
        boxes={'a':(0,0,20,20),'b':(280,0,20,20),'obstacle':(100,70,100,80)}
        paths={'e':[(20,110),(280,110)]}
        flags=_labels(model,boxes,profile,paths)
        self.assertIn('label:e:collision-review',flags)
        self.assertGreater(model['_label_collisions'],0)
        self.assertLessEqual(abs(model['edges'][0]['label_offset']),40*1.2/2+16)

    def test_supplied_path_preserves_explicit_label_override(self):
        from layout_diagram import _labels
        model={'edges':[{'id':'e','source':'a','target':'b','label':'OK','label_position':.2,'label_offset':80}]}
        flags=_labels(model,{'a':(0,0,20,20),'b':(200,0,20,20)},TOKENS['profiles']['document'],{'e':[(20,10),(200,10)]})
        self.assertEqual(model['edges'][0]['label_offset'],80)
        self.assertIn('label:e:explicit-placement-review',flags)

