#!/usr/bin/env python3
"""Extract IDL /Z marker current-points from Ha14 fig-density.eps.

Static interpretation only. IDL defines Z as a round, linewidth-20 stroke at
currentpoint, so every Z invocation is recorded with the current geometry/style
state established by M/R/P commands. PostScript is never executed.
"""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/1407.1744'; UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_density_z_markers_v1.json')

def main():
 req=urllib.request.Request(URL,headers={'User-Agent':UA});
 with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');b=tf.extractfile(tf.getmember('fig-density.eps')).read();lines=b.decode('latin-1','replace').splitlines()
 start=next((i for i,l in enumerate(lines) if l.startswith('%%EndPageSetup')),0)+1
 # Preserve line numbers; strip comments and literal strings.
 toks=[]
 for li,line in enumerate(lines[start:],start+1):
  if '%' in line: line=line.split('%',1)[0]
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|[A-Za-z][A-Za-z0-9_]*',line): toks.append((li,t))
 stack=[];cur=None;color=(0.,0.,0.);dash='L0';width=10.;marks=[];psegments=[];rsegments=[]
 def nval(t):
  try:return float(t)
  except:return None
 def popn(n):
  if len(stack)<n:return None
  v=stack[-n:];del stack[-n:]
  return v if all(isinstance(x,(int,float)) for x in v) else None
 for li,t in toks:
  v=nval(t)
  if v is not None:stack.append(v);continue
  if t=='M':
   a=popn(2)
   if a:cur=(a[0],a[1])
  elif t=='R':
   a=popn(2)
   if a and cur is not None:
    prev=cur;cur=(cur[0]+a[0],cur[1]+a[1]);rsegments.append({'line':li,'a':prev,'b':cur,'color':list(color),'dash':dash,'width':width})
  elif t=='P':
   a=popn(2)
   if a:
    prev=cur;cur=(a[0],a[1]);psegments.append({'line':li,'a':prev,'b':cur,'color':list(color),'dash':dash,'width':width})
  elif t=='Z':
   if cur is not None:marks.append({'line':li,'point':list(cur),'color':list(color),'dash':dash,'base_width':width,'z_width':20})
  elif t in {'L0','L1','L2','L3','L4','L5'}:dash=t
  elif t=='setrgbcolor':
   a=popn(3)
   if a:color=tuple(a)
  elif t in {'setgray','K'}:
   a=popn(1)
   if a:color=(a[0],a[0],a[0])
  elif t=='setlinewidth':
   a=popn(1)
   if a:width=a[0]
  else:
   if len(stack)>12:stack=stack[-12:]
 # plot rectangles from source audit
 rects={'UGC09037':[2220,11568,14574,19616],'UGC12506':[2220,1408,14574,9456]}
 inside={}
 for gal,(x0,y0,x1,y1) in rects.items():
  inside[gal]=[m for m in marks if x0<=m['point'][0]<=x1 and y0<=m['point'][1]<=y1 and max(abs(c) for c in m['color'])<1e-8]
 # monotonic-x unique marker centers by galaxy
 uniq={}
 for gal,ms in inside.items():
  seen=set();arr=[]
  for m in ms:
   p=tuple(m['point'])
   if p not in seen:seen.add(p);arr.append(m)
  uniq[gal]=arr
 out={'status':'HA14_DENSITY_Z_MARKER_EXTRACTION_COMPLETE','asset_sha256':hashlib.sha256(b).hexdigest(),
      'z_definition':'/Z {gsave currentpoint lineto 20 setlinewidth 1 setlinecap stroke grestore}',
      'n_z_markers':len(marks),'all_markers':marks,'black_markers_inside_plot':inside,'unique_black_markers_inside_plot':uniq,
      'n_p_segments':len(psegments),'black_p_segments_inside_plot':{g:[s for s in psegments if s['a'] and x0<=s['a'][0]<=x1 and y0<=s['a'][1]<=y1 and x0<=s['b'][0]<=x1 and y0<=s['b'][1]<=y1 and max(abs(c) for c in s['color'])<1e-8] for g,(x0,y0,x1,y1) in rects.items()},
      'boundary':'Static IDL alias interpretation only; no PostScript execution, OCR, raster digitization, map reconstruction, normalization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'n_z':len(marks),'inside_counts':{g:len(v) for g,v in inside.items()},'unique_counts':{g:len(v) for g,v in uniq.items()},'unique':uniq,'p_counts':{g:len(v) for g,v in out['black_p_segments_inside_plot'].items()}},indent=2))
if __name__=='__main__':main()
