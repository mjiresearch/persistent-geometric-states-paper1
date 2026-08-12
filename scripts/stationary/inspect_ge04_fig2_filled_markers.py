#!/usr/bin/env python3
"""Decode filled native marker paths in Ge04 Figure 2 target subpanels.

Static PostScript token interpretation only; no execution/rendering.
"""
from __future__ import annotations
import hashlib,io,json,math,re,tarfile,urllib.request
from collections import Counter
from pathlib import Path
URL='https://arxiv.org/e-print/astro-ph/0403154';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/ge04_fig2_filled_marker_geometry_v1.json')
TARGET_HEADERS={'ESO116-G12':'116readradialgraph.mr.eps','ESO079-G014':'79readradialgraph.mr.eps'}

def fetch_fig():
 req=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');return tf.extractfile(tf.getmember('fig2.eps')).read()

def split_blocks(s):
 lines=s.splitlines();out={};start=None;name=None
 for i,l in enumerate(lines):
  if l.startswith('%%BeginDocument:'):
   start=i;name=l.split(':',1)[1].strip()
  elif l.startswith('%%EndDocument') and start is not None:
   out[name]='\n'.join(lines[start:i+1]);start=None;name=None
 return out

def tokenize(txt):
 for li,line in enumerate(txt.splitlines(),1):
  if '%' in line: line=line.split('%',1)[0]
  # remove literal strings and procedure definitions from the executable body as much as possible
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|/?[A-Za-z][A-Za-z0-9_.-]*|\[|\]|\{|\}',line):
   yield li,t

def parse_paths(txt):
 toks=list(tokenize(txt));stack=[];cur=None;path=[];start_line=None;fills=[];strokes=[]
 def num(t):
  try:return float(t)
  except:return None
 def popn(n):
  if len(stack)<n:return None
  a=stack[-n:];del stack[-n:]
  return a if all(isinstance(x,(int,float)) for x in a) else None
 def finish(kind,li):
  nonlocal path,start_line
  if len(path)>=2:
   pts=list(path);xs=[p[0] for p in pts];ys=[p[1] for p in pts]
   # polygon area on recorded path (closing implicitly for fill)
   area=0.0
   for a,b in zip(pts,pts[1:]+pts[:1]): area += a[0]*b[1]-b[0]*a[1]
   area=abs(area)/2
   per=sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(pts,pts[1:]+pts[:1]))
   rec={'start_line':start_line,'end_line':li,'n_points':len(pts),'points':[list(p) for p in pts], 'bbox':[min(xs),min(ys),max(xs),max(ys)],'center':[(min(xs)+max(xs))/2,(min(ys)+max(ys))/2],'width':max(xs)-min(xs),'height':max(ys)-min(ys),'area':area,'perimeter':per}
   (fills if kind=='fill' else strokes).append(rec)
  path=[];start_line=None
 for li,t in toks:
  v=num(t)
  if v is not None:stack.append(v);continue
  if t.startswith('/'):
   # definition name; ignore operand residue
   continue
  if t in {'B','M','F'}:
   a=popn(2)
   if a:
    if t=='B' and path: finish('stroke',li)
    cur=(a[0],a[1]);path=[cur];start_line=li
  elif t=='L':
   a=popn(2)
   if a and cur is not None:cur=(a[0],a[1]);path.append(cur)
  elif t=='l':
   a=popn(2)
   if a and cur is not None:cur=(cur[0]+a[0],cur[1]+a[1]);path.append(cur)
  elif t=='m':
   a=popn(2)
   if a and cur is not None:cur=(cur[0]+a[0],cur[1]+a[1]);path.append(cur)
  elif t in {'CF','ef','eofill','fill'}: finish('fill',li)
  elif t in {'CS','s','stroke'}: finish('stroke',li)
  elif t=='cp':
   if path and path[-1]!=path[0]:path.append(path[0])
  else:
   if len(stack)>20:stack=stack[-20:]
 return fills,strokes

def shape_class(r):
 w,h=r['width'],r['height'];n=r['n_points'];ar=w/h if h else 999
 if 0.7<=ar<=1.3 and n>=8:return 'round_like'
 if n<=5 and w>0 and h>0:return 'triangle_or_polygon'
 return 'other'

def main():
 b=fetch_fig();blocks=split_blocks(b.decode('latin-1','replace'));res={}
 for gal,hdr in TARGET_HEADERS.items():
  txt=blocks[hdr];fills,strokes=parse_paths(txt)
  for r in fills:r['shape_class']=shape_class(r)
  hist=Counter((r['shape_class'],r['n_points'],round(r['width'],1),round(r['height'],1)) for r in fills)
  likely_round=[r for r in fills if r['shape_class']=='round_like' and r['width']<200 and r['height']<200]
  likely_poly=[r for r in fills if r['shape_class']=='triangle_or_polygon' and r['width']<200 and r['height']<200]
  res[gal]={'block_header':hdr,'block_sha256':hashlib.sha256(txt.encode('latin-1','replace')).hexdigest(),'n_filled_paths':len(fills),'n_stroked_paths':len(strokes),'filled_shape_histogram':[{'shape_class':k[0],'n_points':k[1],'width':k[2],'height':k[3],'count':v} for k,v in hist.most_common(80)],'likely_round_markers':likely_round[:500],'likely_polygon_markers':likely_poly[:500]}
 out={'status':'GE04_FIG2_FILLED_MARKER_GEOMETRY_INSPECTED','asset_sha256':hashlib.sha256(b).hexdigest(),'targets':res,'boundary':'Static native vector path decoding only; no PostScript execution, OCR, raster digitization, normalization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'targets':{g:{'n_fills':v['n_filled_paths'],'n_strokes':v['n_stroked_paths'],'hist':v['filled_shape_histogram'][:30],'round_centers':[r['center'] for r in v['likely_round_markers'][:80]],'poly_centers':[r['center'] for r in v['likely_polygon_markers'][:80]]} for g,v in res.items()}},indent=2))
if __name__=='__main__':main()
