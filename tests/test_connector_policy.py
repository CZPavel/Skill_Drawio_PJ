"""Connector policy regression contracts and serialized native XML."""
import sys
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from connector_policy import choose_jump_policy, validate_fixed
from build_diagram import build
from layout_diagram import layout
from score_layout import score_layout

class ConnectorTests(unittest.TestCase):
    def model(self,archetype='architecture',direction='LR',edge=None):
        return {'archetype':archetype,'direction':direction,'nodes':[{'id':'a','title':'A'},{'id':'b','title':'B'}], 'edges':[{'id':'e','source':'a','target':'b',**(edge or {})}]}

    def xml_style(self,model):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'a.drawio'; build(model,path)
            return next(c.get('style') for c in ET.parse(path).iter('mxCell') if c.get('id')=='e')

    def test_floating_xml_has_no_fixed_coordinates(self):
        style=self.xml_style(self.model())
        for key in ('exitX=','exitY=','entryX=','entryY=','PortConstraint='):
            self.assertNotIn(key,style)

    def test_side_process_xml_and_straight_main_flow(self):
        for direction,source,target in [('LR','east','west'),('TB','south','north')]:
            model=self.model('process-flow',direction)
            style=self.xml_style(model)
            self.assertIn('sourcePortConstraint='+source+';',style)
            self.assertIn('targetPortConstraint='+target+';',style)
            self.assertNotIn('exitX=',style)
            placed,report=layout(model)
            self.assertEqual(score_layout(placed)['main_flow_bends'],0)

    def test_fixed_explicit_perimeter_preserved_and_invalid_rejected(self):
        fixed={'connector_mode':'fixed','style':{'exitX':1,'exitY':.25,'entryX':0,'entryY':.75}}
        self.assertIn('exitY=0.25;',self.xml_style(self.model(edge=fixed)))
        for shape,x,y in [(None,.5,.5),('decision',1,1)]:
            with self.assertRaises(ValueError):
                validate_fixed({'exitX':x,'exitY':y,'entryX':0,'entryY':.5},{'shape':shape},{})
        validate_fixed({'exitX':.75,'exitY':.25,'entryX':0,'entryY':.5},{'shape':'decision'},{})
        validate_fixed({'exitX':.5,'exitY':.5,'entryX':0,'entryY':.5},{},{},True)

    def test_retry_outer_estimate_exempt_from_backward_penalty(self):
        model=self.model('process-flow',edge={'type':'retry','source':'b','target':'a'})
        placed,_=layout(model)
        metrics=score_layout(placed)
        self.assertEqual(metrics['backward_ordinary_edges'],0)
        self.assertEqual(placed['edges'][0]['style']['sourcePortConstraint'],'north')
        placed['edges'][0].pop('type')
        placed['nodes'][0]['x']=0;placed['nodes'][1]['x']=500
        self.assertEqual(score_layout(placed)['backward_ordinary_edges'],1)

    def test_decision_branches_have_distinct_side_constraints(self):
        model=self.model('decision-flow')
        model['nodes'][0]['shape']='decision'
        model['nodes'].append({'id':'c','title':'C'})
        model['edges'].append({'id':'second','source':'a','target':'c'})
        placed,_=layout(model)
        self.assertNotEqual(placed['edges'][0]['style']['sourcePortConstraint'],placed['edges'][1]['style']['sourcePortConstraint'])

    def test_local_jump_only_secondary_and_dense_or_ambiguous_reviews(self):
        edges=[{'id':'a'},{'id':'b','role':'control'},{'id':'c'}]
        selected,flags=choose_jump_policy(edges,[('a','b')])
        self.assertEqual(selected,['b']);self.assertIn('jump-insertion:rendered-review',flags)
        self.assertEqual(choose_jump_policy(edges,[('a','c')])[0],[])
        selected,flags=choose_jump_policy(edges,[('a','b'),('b','c'),('a','c')])
        self.assertEqual(selected,[]);self.assertIn('multiple-crossings:reroute-review',flags)

    def test_explicit_side_style_is_authoritative(self):
        for archetype in ('process-flow','architecture'):
            m=self.model(archetype,edge={'style':{'sourcePortConstraint':'north','targetPortConstraint':'south'}})
            s=self.xml_style(m)
            self.assertIn('sourcePortConstraint=north;',s)
            self.assertIn('targetPortConstraint=south;',s)

    def test_routing_strategy_preserves_meaningful_placement(self):
        from connector_policy import choose_routing_strategy
        metrics={'edge_node_collisions':2,'main_flow_bends':8}
        caps={'elk':{'status':'verified'},'mcp_libavoid':{'status':'verified'}}
        self.assertEqual(choose_routing_strategy({'archetype':'process-flow'},metrics,caps)['strategy'],'elk')
        self.assertEqual(choose_routing_strategy({'archetype':'process-flow','preserve_placement':True},metrics,caps)['strategy'],'libavoid')
        self.assertEqual(choose_routing_strategy({'preserve_placement':True},metrics,{'elk':True})['strategy'],'local-repair')
        self.assertEqual(choose_routing_strategy({},metrics)['strategy'],'probe-required')
        self.assertEqual(choose_routing_strategy({},{} )['strategy'],'native')
        m={'archetype':'process-flow','edges':[{'connector_mode':'side'}]}
        self.assertEqual(choose_routing_strategy(m,metrics,caps)['strategy'],'local-repair')

    def test_explicit_backward_relation_does_not_reverse_ordinary_ranking(self):
        m={'archetype':'process-flow','direction':'LR','nodes':[{'id':k,'title':k} for k in ('c','a','b')],
           'edges':[{'id':'ab','source':'a','target':'b'},{'id':'bc','source':'b','target':'c'},
                    {'id':'back','source':'c','target':'a','type':'backward'}]}
        placed,_=layout(m)
        self.assertEqual(score_layout(placed)['backward_ordinary_edges'],0)

if __name__=='__main__': unittest.main()
