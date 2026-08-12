#!/usr/bin/env python3
"""List large black relative-line segments inside Ha14 density plot panels.

Font glyph strokes are local (~tens of IDL source units); plotted radial links
span hundreds. This reports native R segments only, preserving source line and
geometry for manual/static identification of the H I profile trace.
"""
from __future__ import annotations
import io,json,re,tarfile,urllib.request,hashlib
from pathlib import Path
URL='https://arxiv.org/e-print/1407.1744';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_large_black_r_segments_v1.json')
RECTS={'UGC09037':(2220.,11568.,14574.,19616.,470),'UGC12506':(2220.,1408.,14574.,9456.,956)}

def main():
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
    old=cur;cur=(cur[0]+a[0],cur[1]+a[1]);segs.append({'line':li,'a':old,'b':cur,'dx':a[0],'dy':a[1],'color':color,'dash':dash,'width':width})
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
 panels={}
 for gal,(x0,y0,x1,y1,cut) in RECTS.items():
  arr=[]
  for s in segs:
   if s['line']>=cut:continue
   if max(abs(c) for c in s['color'])>=1e-8 or s['dash']!='L0':continue
   if not (x0<s['a'][0]<x1 and y0<s['a'][1]<y1 and x0<s['b'][0]<x1 and y0<s['b'][1]<y1):continue
   if abs(s['dx'])>=150 and abs(s['dy'])>=20:
    arr.append({k:(list(v) if isinstance(v,tuple) else v) for k,v in s.items() if k!='color'})
  panels[gal]=arr
 out={'status':'HA14_LARGE_BLACK_R_SEGMENT_AUDIT_COMPLETE','asset_sha256':hashlib.sha256(b).hexdigest(),'criterion':'black L0 native R segment; endpoints strictly inside panel; |dx|>=150; |dy|>=20; before colored curves','panels':panels,
      'boundary':'Native vector geometry only; no PostScript execution, OCR, raster digitization, normalization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'counts':{g:len(a) for g,a in panels.items()},'panels':panels},indent=2))
if __name__=='__main__':main()
