#!/usr/bin/env python3
"""Tolerance-stitch black source-native vector segments in Ha14 fig-density.eps.

IDL may restart neighboring plotted segments with integer-rounded coordinates.
We connect segment endpoints separated by <= 18 PostScript source units, far below
one radial bin / plotted resolution. This acts only on native vector coordinates.
"""
from __future__ import annotations
import hashlib,io,json,math,re,tarfile,urllib.request
from collections import defaultdict
from pathlib import Path
URL='https://arxiv.org/e-print/1407.1744'; UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_black_segment_components_tolerant_v1.json')
RECTS={'UGC09037':(2220.,11568.,14574.,19616.),'UGC12506':(2220.,1408.,14574.,9456.)}
TOL=18.0

def source_segments():
 req=urllib.request.Request(URL,headers={'User-Agent':UA});
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');b=tf.extractfile(tf.getmember('fig-density.eps')).read();lines=b.decode('latin-1','replace').splitlines()
 st=next((i for i,l in enumerate(lines) if l.startswith('%%EndPageSetup')),0)+1;toks=[]
 for li,line in enumerate(lines[st:],st+1):
  if '%' in line:line=line.split('%',1)[0]
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  toks += [(li,t) for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|[A-Za-z][A-Za-z0-9_]*',line)]
 stack=[];cur=None;color=(0.,0.,0.);dash='L0';width=10.;segs=[]
 def nv(t):
  try:return float(t)
  except:return None
 def popn(n):
  if len(stack)<n:return None
  a=stack[-n:];del stack[-n:];return a if all(isinstance(x,(int,float)) for x in a) else None
 for li,t in toks:
  v=nv(t)
  if v is not None:stack.append(v);continue
  if t=='M':
   a=popn(2)
   if a:cur=(a[0],a[1])
  elif t=='R':
   a=popn(2)
   if a and cur is not None:
    old=cur;cur=(cur[0]+a[0],cur[1]+a[1]);segs.append({'line':li,'a':old,'b':cur,'color':color,'dash':dash,'width':width})
  elif t=='P':
   a=popn(2)
   if a:
    old=cur;cur=(a[0],a[1]);segs.append({'line':li,'a':old,'b':cur,'color':color,'dash':dash,'width':width})
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
  elif len(stack)>12:stack=stack[-12:]
 return b,segs

def stitch(ss):
 n=len(ss); parent=list(range(n)); rank=[0]*n
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):
  a=find(a);b=find(b)
  if a==b:return
  if rank[a]<rank[b]:a,b=b,a
  parent[b]=a
  if rank[a]==rank[b]:rank[a]+=1
 # endpoint spatial bins, compare neighboring bins
 cell=TOL;grid=defaultdict(list)
 for i,s in enumerate(ss):
  for p in (s['a'],s['b']):
   gx,gy=int(math.floor(p[0]/cell)),int(math.floor(p[1]/cell))
   for dx in (-1,0,1):
    for dy in (-1,0,1):
     for j,q in grid[(gx+dx,gy+dy)]:
      if (p[0]-q[0])**2+(p[1]-q[1])**2<=TOL*TOL:union(i,j)
   grid[(gx,gy)].append((i,p))
 groups=defaultdict(list)
 for i in range(n):groups[find(i)].append(i)
 comps=[]
 for ids in groups.values():
  pts=[]
  for i in ids:pts += [ss[i]['a'],ss[i]['b']]
  xs=[p[0] for p in pts];ys=[p[1] for p in pts]
  comps.append({'n_edges':len(ids),'bbox':[min(xs),min(ys),max(xs),max(ys)],'x_span':max(xs)-min(xs),'y_span':max(ys)-min(ys),
                'min_line':min(ss[i]['line'] for i in ids),'max_line':max(ss[i]['line'] for i in ids),
                'segments':[{'line':ss[i]['line'],'a':list(ss[i]['a']),'b':list(ss[i]['b']),'dash':ss[i]['dash'],'width':ss[i]['width']} for i in ids]})
 comps.sort(key=lambda c:(c['x_span'],c['n_edges'],c['y_span']),reverse=True);return comps

def main():
 b,segs=source_segments();panels={}
 for g,(x0,y0,x1,y1) in RECTS.items():
  # exclude exact plot borders and a 25-unit edge strip so axes/ticks don't percolate into data
  ss=[]
  for s in segs:
   if max(abs(c) for c in s['color'])>=1e-8:continue
   if not (x0<s['a'][0]<x1 and y0<s['a'][1]<y1 and x0<s['b'][0]<x1 and y0<s['b'][1]<y1):continue
   ss.append(s)
  comps=stitch(ss)
  cand=[c for c in comps if c['x_span']>1000 and c['y_span']>40]
  panels[g]={'n_interior_black_segments':len(ss),'n_components':len(comps),'candidates':cand[:40],'top_components':comps[:100]}
 out={'status':'HA14_TOLERANT_BLACK_SEGMENT_STITCH_COMPLETE','tolerance_source_units':TOL,'asset_sha256':hashlib.sha256(b).hexdigest(),'panels':panels,
      'boundary':'Reconnects only source-native vector endpoints within 18 integer PostScript units. No PostScript execution, OCR, raster digitization, map reconstruction, normalization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'panels':{g:{'n_segments':v['n_interior_black_segments'],'n_components':v['n_components'],'candidates':[{k:c[k] for k in ['n_edges','bbox','x_span','y_span','min_line','max_line']} for c in v['candidates'][:20]]} for g,v in panels.items()}},indent=2))
if __name__=='__main__':main()
