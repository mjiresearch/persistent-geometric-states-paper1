#!/usr/bin/env python3
"""Corrected IDL geometry stitch for Ha14 fig-density.eps.

Interprets M=moveto, N=rmoveto, R=rlineto, P=lineto, D=stroke while
tracking only source-native vector coordinates and style. PostScript is never
executed. Including N is essential because IDL uses relative moves between
short plotted strokes.
"""
from __future__ import annotations
import hashlib,io,json,math,re,tarfile,urllib.request
from collections import defaultdict
from pathlib import Path
URL='https://arxiv.org/e-print/1407.1744'; UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_black_segment_components_idl_v2.json')
RECTS={'UGC09037':(2220.,11568.,14574.,19616.,470),'UGC12506':(2220.,1408.,14574.,9456.,956)}
TOL=18.0

def parse():
 req=urllib.request.Request(URL,headers={'User-Agent':UA});
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');b=tf.extractfile(tf.getmember('fig-density.eps')).read();lines=b.decode('latin-1','replace').splitlines()
 st=next((i for i,l in enumerate(lines) if l.startswith('%%EndPageSetup')),0)+1;toks=[]
 for li,line in enumerate(lines[st:],st+1):
  if '%' in line:line=line.split('%',1)[0]
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  toks += [(li,t) for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|[A-Za-z][A-Za-z0-9_]*',line)]
 stack=[];cur=None;color=(0.,0.,0.);dash='L0';width=10.;segs=[];moves=[]
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
   if a:cur=(a[0],a[1]);moves.append({'line':li,'op':'M','to':cur})
  elif t=='N':
   a=popn(2)
   if a and cur is not None:cur=(cur[0]+a[0],cur[1]+a[1]);moves.append({'line':li,'op':'N','to':cur})
  elif t=='R':
   a=popn(2)
   if a and cur is not None:
    old=cur;cur=(cur[0]+a[0],cur[1]+a[1]);segs.append({'line':li,'a':old,'b':cur,'dx':a[0],'dy':a[1],'color':color,'dash':dash,'width':width})
  elif t=='P':
   a=popn(2)
   if a:
    old=cur;cur=(a[0],a[1]);segs.append({'line':li,'a':old,'b':cur,'dx':None if old is None else cur[0]-old[0],'dy':None if old is None else cur[1]-old[1],'color':color,'dash':dash,'width':width})
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
  elif t in {'D','C','stroke','gsave','grestore','show','showpage','newpath','closepath','clip'}:
   pass
  else:
   # Unknown operators can have operands; cap residual numeric stack only.
   if len(stack)>12:stack=stack[-12:]
 return b,segs,moves

def comps_for(ss,tol):
 n=len(ss);parent=list(range(n));rank=[0]*n
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):
  a=find(a);b=find(b)
  if a==b:return
  if rank[a]<rank[b]:a,b=b,a
  parent[b]=a
  if rank[a]==rank[b]:rank[a]+=1
 grid=defaultdict(list);cell=max(tol,1.)
 for i,s in enumerate(ss):
  for p in (s['a'],s['b']):
   gx,gy=int(math.floor(p[0]/cell)),int(math.floor(p[1]/cell))
   for dx in (-1,0,1):
    for dy in (-1,0,1):
     for j,q in grid[(gx+dx,gy+dy)]:
      if (p[0]-q[0])**2+(p[1]-q[1])**2<=tol*tol:union(i,j)
   grid[(gx,gy)].append((i,p))
 groups=defaultdict(list)
 for i in range(n):groups[find(i)].append(i)
 out=[]
 for ids in groups.values():
  pts=[p for i in ids for p in (ss[i]['a'],ss[i]['b'])];xs=[p[0] for p in pts];ys=[p[1] for p in pts]
  out.append({'n_edges':len(ids),'bbox':[min(xs),min(ys),max(xs),max(ys)],'x_span':max(xs)-min(xs),'y_span':max(ys)-min(ys),
   'min_line':min(ss[i]['line'] for i in ids),'max_line':max(ss[i]['line'] for i in ids),
   'segments':[{'line':ss[i]['line'],'a':list(ss[i]['a']),'b':list(ss[i]['b']),'dx':ss[i]['dx'],'dy':ss[i]['dy'],'dash':ss[i]['dash'],'width':ss[i]['width']} for i in ids]})
 out.sort(key=lambda c:(c['x_span'],c['n_edges'],c['y_span']),reverse=True);return out

def main():
 b,segs,moves=parse();panels={}
 for g,(x0,y0,x1,y1,cut) in RECTS.items():
  ss=[s for s in segs if s['line']<cut and max(abs(c) for c in s['color'])<1e-8 and s['dash']=='L0' and x0<s['a'][0]<x1 and y0<s['a'][1]<y1 and x0<s['b'][0]<x1 and y0<s['b'][1]<y1]
  exact=comps_for(ss,0.1);tol=comps_for(ss,TOL)
  # candidate requires broad radial span and nonzero vertical structure; report even if made of many short strokes.
  ex_c=[c for c in exact if c['x_span']>500 and c['y_span']>20]
  to_c=[c for c in tol if c['x_span']>500 and c['y_span']>20]
  # also report large-x individual segments after N correction
  large=[{'line':s['line'],'a':list(s['a']),'b':list(s['b']),'dx':s['dx'],'dy':s['dy']} for s in ss if s['dx'] is not None and abs(s['dx'])>=120 and abs(s['dy'])>=10]
  panels[g]={'n_segments':len(ss),'exact_candidates':ex_c[:40],'tolerant_candidates':to_c[:40],'large_individual_segments':large[:300]}
 out={'status':'HA14_IDL_V2_BLACK_SEGMENT_STITCH_COMPLETE','asset_sha256':hashlib.sha256(b).hexdigest(),'tolerance_source_units':TOL,'n_relative_moves_N':sum(1 for m in moves if m['op']=='N'),'panels':panels,
      'boundary':'Corrected static M/N/R/P IDL source geometry only; no PostScript execution, OCR, raster digitization, normalization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'n_N':out['n_relative_moves_N'],'panels':{g:{'n_segments':v['n_segments'],'exact':[{k:c[k] for k in ['n_edges','bbox','x_span','y_span','min_line','max_line']} for c in v['exact_candidates'][:15]],'tol':[{k:c[k] for k in ['n_edges','bbox','x_span','y_span','min_line','max_line']} for c in v['tolerant_candidates'][:15]],'large':v['large_individual_segments'][:80]} for g,v in panels.items()}},indent=2))
if __name__=='__main__':main()
