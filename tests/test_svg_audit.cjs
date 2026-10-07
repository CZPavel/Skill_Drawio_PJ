const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {audit}=require('../scripts/audit_svg.cjs');

const svg=body=>`<svg xmlns="http://www.w3.org/2000/svg" width="600" height="300">${body}</svg>`;
async function fixture(body,options={}) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'svg-qa-')),file=path.join(dir,'fixture.svg');
  const source=svg(body);fs.writeFileSync(file,source);
  try { const report=await audit(file,options);assert.equal(fs.readFileSync(file,'utf8'),source);return report; }
  finally {fs.rmSync(dir,{recursive:true,force:true});}
}
const codes=r=>new Set(r.findings.map(f=>f.code));
test('actual DOM: text bounds, HTML clipping and crossed text/node',async()=>{
  const r=await fixture(`<g data-cell-id="node"><rect x="50" y="50" width="100" height="60" fill="white" stroke="black"/><foreignObject x="60" y="60" width="80" height="40"><div xmlns="http://www.w3.org/1999/xhtml" style="font-size:20px;width:80px;height:30px;overflow:hidden;white-space:nowrap">Příliš dlouhý český nadpis</div></foreignObject></g><g data-cell-id="edge"><path d="M 0 75 L 250 75" fill="none" stroke="black"/></g>`);
  assert.ok(codes(r).has('html-scroll-overflow'));
  assert.ok(codes(r).has('text-node-overflow'));
  assert.ok(codes(r).has('edge-node'));
  assert.ok(codes(r).has('edge-label'));
  assert.equal(r.metrics.edges,1);
});
test('benign containment and endpoint attachment excluded; crossing edges found',async()=>{
  const r=await fixture(`<g data-cell-id="container"><rect x="10" y="10" width="300" height="240" fill="white" stroke="black"/></g><g data-cell-id="child"><rect x="50" y="50" width="70" height="50" fill="white" stroke="black"/></g><g data-cell-id="a"><path d="M 120 75 L 200 75" stroke="black" fill="none"/></g><g data-cell-id="b"><path d="M 160 30 L 160 130" stroke="black" fill="none"/></g>`);
  assert.ok(!codes(r).has('node-overlap'));
  assert.ok(!codes(r).has('edge-node'));
  assert.ok(codes(r).has('edge-edge'));
  assert.equal(r.post_routing.crossings,1);
  assert.equal(r.post_routing.edge_node_collisions,0);
  assert.equal(r.post_routing.total_edge_length_css_px,180);
});
test('post-routing semantic metrics distinguish retry from backward main flow',async()=>{
  const r=await fixture(`<g data-cell-id="main"><path d="M 200 50 L 20 50" fill="none" stroke="black"/></g><g data-cell-id="retry"><path d="M 200 120 L 20 120" fill="none" stroke="black"/></g>`,
    {direction:'LR',edgeSemantics:{main:{},retry:{type:'retry'}}});
  assert.equal(r.post_routing.backward_ordinary_edges,1);
  assert.equal(r.post_routing.main_flow_bends,0);
  assert.equal(r.post_routing.crossings,0);
});
test('transformed font projects correctly; sampled curves and missing identity honest',async()=>{
  const r=await fixture(`<g transform="scale(2)"><rect x="0" y="0" width="250" height="70" fill="white"/><text x="10" y="30" font-size="10">Čitelnost</text><path d="M 0 90 Q 80 10 180 90" fill="none" stroke="black"/></g>`,{targetWidthMm:60});
  assert.equal(r.metrics.min_font_css_px,20);
  assert.ok(r.metrics.projected_min_font_pt<9);
  assert.ok(codes(r).has('path-sampled'));
  assert.ok(codes(r).has('identity-unavailable'));
  assert.equal(r.coverage.target_document_verified,false);
});
test('rounded main flow does not claim zero measured bends',async()=>{
  const r=await fixture(`<g data-cell-id="main"><path d="M0,50 L90,50 Q100,50 100,60 L100,190 Q100,200 110,200 L200,200" fill="none" stroke="black"/></g>`,
    {direction:'LR',edgeSemantics:{main:{}}});
  assert.equal(r.post_routing.main_flow_bends,null);
  assert.equal(r.post_routing.score,null);
});
test('collinear intermediate waypoint is neither bend nor missing crossing',async()=>{
  const r=await fixture(`<g data-cell-id="a"><path d="M0 100 L100 100 L200 100" fill="none" stroke="black"/></g><g data-cell-id="b"><path d="M100 0 L100 200" fill="none" stroke="black"/></g>`);
  assert.equal(r.post_routing.crossings,1);
  assert.equal(r.post_routing.edge_metrics.find(e=>e.id==='a').bends,0);
});
