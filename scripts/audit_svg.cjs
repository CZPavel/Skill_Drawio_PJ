/** Browser-measured SVG QA. Original implementation; never edits the input. */
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

async function audit(file, options = {}) {
  const {chromium} = require('playwright');
  let browser;
  try { browser = await chromium.launch({headless:true, ...(options.browserChannel ? {channel:options.browserChannel} : {})}); }
  catch (error) {
    if (options.browserChannel) throw error;
    browser = await chromium.launch({headless:true,channel:'msedge'});
  }
  try {
    const page = await browser.newPage({viewport:{width:1920,height:1080},colorScheme:'light',javaScriptEnabled:false});
    await page.route('**/*', route => {
      const url = route.request().url();
      return url.startsWith('file:') || url.startsWith('data:') ? route.continue() : route.abort();
    });
    await page.goto(pathToFileURL(path.resolve(file)).href);
    await page.evaluate(() => document.fonts.ready);
    const result = await page.evaluate(({targetWidthMm,edgeSemantics,direction}) => {
      const svg = document.querySelector('svg');
      if (!svg || document.querySelector('parsererror')) throw new Error('Input is not valid rendered SVG');
      const findings = [];
      const add = (code, cells, message, severity='warning') => findings.push({severity,code,cells,message});
      const bounds = el => {const r=el.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height};};
      const overlap = (a,b) => Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>1 && Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>1;
      const contains = (a,b,t=1) => a.x-t<=b.x && a.y-t<=b.y && a.x+a.w+t>=b.x+b.w && a.y+a.h+t>=b.y+b.h;
      const id = (el,i) => el.closest('[data-cell-id]')?.getAttribute('data-cell-id') || el.id || `element-${i}`;
      const visible = el => { const s=getComputedStyle(el),r=bounds(el); return s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity)!==0 && r.w+r.h>0; };
      const shapes = Array.from(svg.querySelectorAll('rect,ellipse,circle,polygon,path')).filter(el => {
        const s=getComputedStyle(el);
        const cell=el.closest('[data-cell-id]');
        const edgeCell=cell && Array.from(cell.querySelectorAll('path')).some(p=>getComputedStyle(p).fill==='none' && getComputedStyle(p).stroke!=='none');
        return visible(el) && !edgeCell && s.fill!=='none' && s.fill!=='transparent' && !(el.tagName==='path' && !/[zZ]/.test(el.getAttribute('d')||'')) && !(el.parentElement===svg && el.tagName==='rect' && el.getAttribute('width')==='100%');
      }).map((el,i)=>({el,id:id(el,i),r:bounds(el)}));
      if (!svg.querySelector('[data-cell-id]')) add('identity-unavailable',[],'SVG has no data-cell-id: identity falls back to element ID/index','uncertain');
      const texts=[];
      for (const [i,el] of Array.from(svg.querySelectorAll('text,foreignObject *')).entries()) {
        if (!visible(el)) continue;
        const textNodes=Array.from(el.childNodes).filter(n=>n.nodeType===Node.TEXT_NODE && n.textContent.trim());
        if (!textNodes.length) continue;
        for (const n of textNodes) {
          const range=document.createRange(); range.selectNodeContents(n);
          const r=range.getBoundingClientRect();
          if (!r.width || !r.height) continue;
          const matrix=typeof el.getScreenCTM==='function' ? el.getScreenCTM() : el.closest('g')?.getScreenCTM();
          const scale=matrix ? Math.hypot(matrix.a,matrix.b) : 1;
          texts.push({el,id:id(el,i),r:{x:r.x,y:r.y,w:r.width,h:r.height},font:parseFloat(getComputedStyle(el).fontSize)*scale});
        }
        // draw.io uses 1px flex wrapper heights with overflow:visible; these are intentional.
        const s=getComputedStyle(el);
        if (el.clientWidth>0 && el.scrollWidth>el.clientWidth+2 && s.overflowX!=='visible') add('html-scroll-overflow',[id(el,i)],'Rendered HTML scroll width exceeds clipped client width');
        if (el.clientHeight>2 && el.scrollHeight>el.clientHeight+2 && s.overflowY!=='visible') add('html-scroll-overflow',[id(el,i)],'Rendered HTML scroll height exceeds clipped client height');
      }
      for (const text of texts) {
        const own=shapes.filter(s=>s.id===text.id);
        if (own.length && !own.some(s=>contains(s.r,text.r))) add('text-node-overflow',[text.id],'Actual browser text bounds exceed related shape rectangle');
        for (const s of shapes) if(s.id!==text.id && overlap(text.r,s.r) && !contains(s.r,text.r)) add('label-node',[text.id,s.id],'Rendered text intersects unrelated shape rectangle');
      }
      for (let i=0;i<shapes.length;i++) for(let j=i+1;j<shapes.length;j++) {
        const a=shapes[i],b=shapes[j];
        if(a.id!==b.id && overlap(a.r,b.r) && !contains(a.r,b.r) && !contains(b.r,a.r)) add('node-overlap',[a.id,b.id],'Rendered shape rectangles overlap');
      }
      const inside=(p,r,t=0)=>p.x>=r.x-t && p.x<=r.x+r.w+t && p.y>=r.y-t && p.y<=r.y+r.h+t;
      const segmentRect=(a,b,r)=>{
        let lo=0,hi=1;
        for(const [p,q] of [[a.x-b.x,a.x-r.x],[b.x-a.x,r.x+r.w-a.x],[a.y-b.y,a.y-r.y],[b.y-a.y,r.y+r.h-a.y]]) {
          if(p===0){if(q<0)return false;}else if(p<0)lo=Math.max(lo,q/p);else hi=Math.min(hi,q/p);
        }return lo<=hi;
      };
      const intersect=(a,b,c,d)=>{
        const cross=(p,q,r)=>(q.x-p.x)*(r.y-p.y)-(q.y-p.y)*(r.x-p.x);
        if(Math.max(Math.min(a.x,b.x),Math.min(c.x,d.x))>Math.min(Math.max(a.x,b.x),Math.max(c.x,d.x))+.1 || Math.max(Math.min(a.y,b.y),Math.min(c.y,d.y))>Math.min(Math.max(a.y,b.y),Math.max(c.y,d.y))+.1)return false;
        return cross(a,b,c)*cross(a,b,d)<=.01 && cross(c,d,a)*cross(c,d,b)<=.01;
      };
      const edges=[];
      for(const [i,el] of Array.from(svg.querySelectorAll('path,polyline,line')).entries()) {
        const s=getComputedStyle(el);
        if(!visible(el) || s.stroke==='none' || Number(s.strokeWidth)===0 || (el.tagName==='path' && s.fill!=='none'))continue;
        let points=[],curved=false;
        if(el.tagName==='path') {
          const d=el.getAttribute('d')||'';
          if((d.match(/[mM]/g)||[]).length>1){add('path-unresolved',[id(el,i)],'Multiple subpaths require separate rendered visual inspection','uncertain');continue;}
          curved=/[aAcCqQsStT]/.test(d);
          const commands=d.match(/[a-zA-Z][^a-zA-Z]*/g)||[];
          let x=0,y=0;
          if(!curved)for(const command of commands) {
            const op=command[0], nums=(command.slice(1).match(/[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?/g)||[]).map(Number);
            if(!'MmLlHhVv'.includes(op)){curved=true;break;}
            if(op==='H'||op==='h')for(const n of nums){x=op==='h'?x+n:n;points.push({x,y});}
            else if(op==='V'||op==='v')for(const n of nums){y=op==='v'?y+n:n;points.push({x,y});}
            else for(let k=0;k+1<nums.length;k+=2){x=op===op.toLowerCase()?x+nums[k]:nums[k];y=op===op.toLowerCase()?y+nums[k+1]:nums[k+1];points.push({x,y});}
          }
          if(curved) {
            const length=el.getTotalLength(), steps=Math.min(2000,Math.max(2,Math.ceil(length/3)));
            points=Array.from({length:steps+1},(_,k)=>el.getPointAtLength(length*k/steps));
            add('path-sampled',[id(el,i)],'Curve/nonlinear path collisions sampled at about 3 SVG units (capped 2000); approximation','uncertain');
          }
        } else if(el.tagName==='line') points=[{x:el.x1.baseVal.value,y:el.y1.baseVal.value},{x:el.x2.baseVal.value,y:el.y2.baseVal.value}];
        else points=Array.from({length:el.points.numberOfItems},(_,k)=>el.points.getItem(k));
        const matrix=el.getScreenCTM();
        points=points.map(p=>{const q=new DOMPoint(p.x,p.y).matrixTransform(matrix);return {x:q.x,y:q.y};});
        if(!curved) {
          const reduced=[];
          for(const p of points) {
            if(reduced.length && Math.hypot(p.x-reduced.at(-1).x,p.y-reduced.at(-1).y)<0.001)continue;
            while(reduced.length>=2) {
              const a=reduced.at(-2),b=reduced.at(-1);
              const cross=(b.x-a.x)*(p.y-b.y)-(b.y-a.y)*(p.x-b.x);
              const dot=(b.x-a.x)*(p.x-b.x)+(b.y-a.y)*(p.y-b.y);
              if(Math.abs(cross)>0.001||dot<0)break;
              reduced.pop();
            }
            reduced.push(p);
          }
          points=reduced;
        }
        if(points.length<2){add('path-unresolved',[id(el,i)],'No usable rendered path segments','uncertain');continue;}
        const edge={id:id(el,i),points,curved};edges.push(edge);
        if(!curved && points.length>2 && Math.hypot(points.at(-1).x-points.at(-2).x,points.at(-1).y-points.at(-2).y)<20) add('edge-terminal',[edge.id],'Final rendered segment shorter than 20 rendered CSS pixels (review target scale)');
        for(const shape of shapes) {
          if(shape.id===edge.id)continue;
          if(inside(points[0],shape.r,8)||inside(points.at(-1),shape.r,8))continue;
          if(points.slice(1).some((p,k)=>segmentRect(points[k],p,shape.r))) add('edge-node',[edge.id,shape.id],'Rendered path intersects foreign node rectangle/border; nonrectangular silhouettes need visual review');
        }
        for(const text of texts) if(points.slice(1).some((p,k)=>segmentRect(points[k],p,text.r))) add('edge-label',[edge.id,text.id],'Rendered path intersects actual text bounding rectangle (including its own label)');
      }
      for(let i=0;i<edges.length;i++)for(let j=i+1;j<edges.length;j++) {
        const a=edges[i],b=edges[j];if(a.id===b.id)continue;
        if(a.points.slice(1).some((p,k)=>b.points.slice(1).some((q,l)=>intersect(a.points[k],p,b.points[l],q)))) add('edge-edge',[a.id,b.id],'Rendered path segments intersect/overlap; intentional junctions need review');
      }
      // Post-routing evidence stays separate from pre-routing candidate estimates.
      // Strict interior crossings exclude shared endpoint contacts and overlap.
      const proper=(a,b,c,d)=>{
        const cross=(p,q,r)=>(q.x-p.x)*(r.y-p.y)-(q.y-p.y)*(r.x-p.x);
        return cross(a,b,c)*cross(a,b,d)<-0.01 && cross(c,d,a)*cross(c,d,b)<-0.01;
      };
      const crossingPairs=[];
      for(let i=0;i<edges.length;i++)for(let j=i+1;j<edges.length;j++) {
        const a=edges[i],b=edges[j];
        if(a.id!==b.id && a.points.slice(1).some((p,k)=>b.points.slice(1).some((q,l)=>proper(a.points[k],p,b.points[l],q))))crossingPairs.push([a.id,b.id]);
      }
      const edgeMetrics=edges.map(e=>({id:e.id,bends:e.curved?null:Math.max(0,e.points.length-2),
        length_css_px:e.points.slice(1).reduce((s,p,i)=>s+Math.hypot(p.x-e.points[i].x,p.y-e.points[i].y),0),
        start:e.points[0],end:e.points.at(-1)}));
      const secondary=e=>['retry','feedback','backward','exception'].includes(e.type)||['control','note','service'].includes(e.role);
      const ordinary=edgeMetrics.filter(e=>edgeSemantics?.[e.id]&&!secondary(edgeSemantics[e.id]));
      const main=ordinary.filter(e=>edgeSemantics[e.id].type!=='branch');
      const ordinaryBackward=direction ? ordinary.filter(e=>direction==='TB'?e.end.y<e.start.y-1:e.end.x<e.start.x-1).length:null;
      const uniqueFindings=code=>new Set(findings.filter(f=>f.code===code).map(f=>f.cells.join('|'))).size;
      const edgeNode=uniqueFindings('edge-node'),labelNode=uniqueFindings('label-node');
      const edgeLabel=new Set(findings.filter(f=>f.code==='edge-label'&&f.cells[0]!==f.cells[1]).map(f=>f.cells.join('|'))).size;
      const post={crossings:crossingPairs.length,crossing_pairs:crossingPairs,
        edge_node_collisions:edgeNode,label_collisions:labelNode+edgeLabel,
        total_edge_length_css_px:edgeMetrics.reduce((s,e)=>s+e.length_css_px,0),
        main_flow_bends:edgeSemantics&&!main.some(e=>e.bends===null)?main.reduce((s,e)=>s+e.bends,0):null,
        backward_ordinary_edges:ordinaryBackward,edge_metrics:edgeMetrics,
        score:edges.some(e=>e.curved)||findings.some(f=>f.code==='path-unresolved')?null:100-crossingPairs.length*8-edgeNode*80-(labelNode+edgeLabel)*20,
        score_scope:'Rendered rectangle/path screening only; not a quality certificate. Sampled curves and jumps approximate; visual review required.'};
      const content=[...shapes.map(s=>s.r),...texts.map(t=>t.r),...edges.flatMap(e=>e.points.map(p=>({x:p.x,y:p.y,w:0,h:0})))];
      const left=Math.min(...content.map(r=>r.x)),top=Math.min(...content.map(r=>r.y)),right=Math.max(...content.map(r=>r.x+r.w)),bottom=Math.max(...content.map(r=>r.y+r.h));
      const width=content.length?right-left:0,height=content.length?bottom-top:0;
      const minFont=texts.length?Math.min(...texts.map(t=>t.font)):null;
      const exportedWidth=bounds(svg).w;
      const projected=targetWidthMm && exportedWidth && minFont? minFont*targetWidthMm/exportedWidth*72/25.4:null;
      if(projected!==null && projected<9)add('target-font-small',[],`Smallest rendered font projects to ${projected.toFixed(2)} pt at target width; default review minimum 9 pt`);
      const outer=shapes.filter(a=>!shapes.some(b=>a!==b && contains(b.r,a.r) && b.r.w*b.r.h>a.r.w*a.r.h));
      add('bounds-approximation',[],'Shape/text rectangles omit nonrectangular interiors, filters, markers and exact ink; containment is geometric when source grouping is absent','uncertain');
      if(!content.length)add('content-unresolved',[],'No measurable diagram content','uncertain');
      return {findings,post_routing:post,metrics:{nodes:shapes.length,text_runs:texts.length,edges:edges.length,sampled_edges:edges.filter(e=>e.curved).length,bends:edges.filter(e=>!e.curved).reduce((n,e)=>n+Math.max(0,e.points.length-2),0),bounds_css_px:content.length?[left,top,right,bottom]:null,width_css_px:width,height_css_px:height,exported_width_css_px:exportedWidth,aspect_ratio:height?width/height:null,min_font_css_px:minFont,projected_min_font_pt:projected,estimated_whitespace_fraction:width*height?Math.max(0,1-outer.reduce((n,s)=>n+s.r.w*s.r.h,0)/(width*height)):null},coverage:{browser_rendered:true,target_document_verified:false,collision_geometry:'transformed browser rectangles and rendered path segments; sampled curves approximate',visual_review_required:true}};
    },{targetWidthMm:options.targetWidthMm,edgeSemantics:options.edgeSemantics,direction:options.direction});
    return {source:path.resolve(file),...result};
  } finally {await browser.close();}
}

async function main() {
  const args=process.argv.slice(2), file=args.shift(),options={};let output;
  if(!file)throw new Error('Usage: node scripts/audit_svg.cjs FILE --json OUTPUT [--target-width-mm 160] [--browser-channel msedge]');
  while(args.length){const flag=args.shift(),value=args.shift();if(flag==='--json')output=value;else if(flag==='--target-width-mm')options.targetWidthMm=Number(value);else if(flag==='--browser-channel')options.browserChannel=value;else if(flag==='--model'){const m=JSON.parse(fs.readFileSync(value,'utf8').replace(/^\uFEFF/,''));options.edgeSemantics=Object.fromEntries((m.edges||[]).map((e,i)=>[e.id||('edge-'+(i+1)),e]));options.direction=m._layout_direction||(m.direction==='auto'?undefined:m.direction);}else throw new Error(`Unknown argument ${flag}`);}
  if(options.targetWidthMm!==undefined && !(options.targetWidthMm>0))throw new Error('Target width must be positive');
  const result=await audit(file,options), json=JSON.stringify(result,null,2)+'\n';
  if(output){fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});fs.writeFileSync(output,json);}
  console.log(json);
}
module.exports={audit};
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=2;});
