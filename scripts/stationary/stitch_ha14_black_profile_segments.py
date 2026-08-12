#!/usr/bin/env python3
"""Stitch black IDL R-segments in Ha14 fig-density.eps into connected components.

This statically interprets only M/R and style aliases. It does not execute
PostScript. Components are formed from exact shared endpoints; long components
inside the known plot rectangles are candidate source-native H I profiles.
"""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from collections import defaultdict,deque
from pathlib import Path
URL='https://arxiv.org/e-print/1407.1744';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_black_segment_components_v1.json')
RECTS={'UGC09037':(2220.,11568.,14574.,19616.),'UGC12506':(2220.,1408.,14574.,9456.)}

def main():
 req=urllib.request.Request(URL,headers={'User-Agent':UA});
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');b=tf.extractfile(tf.getmember('fig-density.eps')).read();lines=b.decode('latin-1','replace').splitlines()
 start=next((i for i,l in enumerate(lines) if l.startswith('%%EndPageSetup')),0)+1
 toks=[]
 for li,line in enumerate(lines[start:],start+1):
  if '%' in line:line=line.split('%',1)[0]
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|[A-Za-z][A-Za-z0-9_]*',line):toks.append((li,t))
 stack=[];cur=None;color=(0.,0.,0.);dash='L0';width=10.;segments=[]
 def nv(t):
  try:return float(t)
  except:return None
 def popn(n):
  if len(stack)<n:return None
  a=stack[-n:];del stack[-n:]
  return a if all(isinstance(x,(int,float)) for x in a) else None
 for li,t in toks:
  v=nv(t)
  if v is not None:stack.append(v);continue
  if t=='M':
   a=popn(2)
   if a:cur=(a[0],a[1])
  elif t=='R':
   a=popn(2)
   if a and cur is not None:
    old=cur;cur=(cur[0]+a[0],cur[1]+a[1]);segments.append({'line':li,'a':old,'b':cur,'color':color,'dash':dash,'width':width})
  elif t=='P':
   a=popn(2)
   if a:
    old=cur;cur=(a[0],a[1]);segments.append({'line':li,'a':old,'b':cur,'color':color,'dash':dash,'width':width})
  elif t in {'L0','L1','L2','L3','L4','L5'}:dash=t
  elif t=='setrgbcolor':
   a=popn(3)
   if a:color=tuple(a)
  elif t in {'setgray','K'}:
   a=popn(1)
   if a:color=(a[0],)*3
  elif t=='setlinewidth':
   a=popn(1)
   if a:width=a[0]
  else:
   if len(stack)>12:stack=stack[-12:]
 result={}
 for gal,(x0,y0,x1,y1) in RECTS.items():
  # black segments with both endpoints in/on panel.
  ss=[s for s in segments if max(abs(c) for c in s['color'])<1e-8 and x0<=s['a'][0]<=x1 and y0<=s['a'][1]<=y1 and x0<=s['b'][0]<=x1 and y0<=s['b'][1]<=y1]
  adj=defaultdict(list)
  for idx,s in enumerate(ss):
   adj[s['a']].append(idx);adj[s['b']].append(idx)
  unseen=set(range(len(ss)));comps=[]
  while unseen:
   seed=unseen.pop();edges={seed};nodes={ss[seed]['a'],ss[seed]['b']};q=deque(nodes)
   while q:
    p=q.popleft()
    for ei in adj[p]:
     if ei in unseen:
      unseen.remove(ei);edges.add(ei)
      for n in (ss[ei]['a'],ss[ei]['b']):
       if n not in nodes:nodes.add(n);q.append(n)
   xs=[p[0] for p in nodes];ys=[p[1] for p in nodes]
   earr=[ss[i] for i in sorted(edges)]
   comps.append({'n_edges':len(edges),'n_nodes':len(nodes),'bbox':[min(xs),min(ys),max(xs),max(ys)],'x_span':max(xs)-min(xs),'y_span':max(ys)-min(ys),
                 'min_line':min(e['line'] for e in earr),'max_line':max(e['line'] for e in earr),'nodes':[list(p) for p in sorted(nodes)],
                 'edges':[{'line':e['line'],'a':list(e['a']),'b':list(e['b']),'dash':e['dash'],'width':e['width']} for e in earr]})
  comps.sort(key=lambda c:(c['x_span'],c['n_edges'],c['y_span']),reverse=True)
  # scientific candidates: horizontal span > one major x tick (~1765) and not exactly an axis boundary.
  cand=[c for c in comps if c['x_span']>1000 and c['y_span']>20 and not (abs(c['bbox'][1]-y0)<1e-6 and abs(c['bbox'][3]-y0)<1e-6) and not (abs(c['bbox'][1]-y1)<1e-6 and abs(c['bbox'][3]-y1)<1e-6)]
  result[gal]={'n_black_segments_inside':len(ss),'n_components':len(comps),'top_components':comps[:80],'candidates':cand[:30]}
 out={'status':'HA14_BLACK_SEGMENT_COMPONENT_STITCH_COMPLETE','asset_sha256':hashlib.sha256(b).hexdigest(),'panels':result,
      'boundary':'Static source-native M/R/P geometry only; no PostScript execution, OCR, raster digitization, normalization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'panels':{g:{'n_segments':v['n_black_segments_inside'],'n_components':v['n_components'],'candidates':[{k:c[k] for k in ['n_edges','n_nodes','bbox','x_span','y_span','min_line','max_line']} for c in v['candidates'][:15]]} for g,v in result.items()}},indent=2))
if __name__=='__main__':main()
