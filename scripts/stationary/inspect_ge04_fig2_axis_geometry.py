#!/usr/bin/env python3
"""Inspect native axis-frame geometry and 7-point filled circles in Ge04 Fig. 2.

No rendering or PostScript execution. The output is a compact QC artifact used
to derive the linear source-coordinate -> published-axis transforms.
"""
from __future__ import annotations
import hashlib,io,json,math,re,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/astro-ph/0403154';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/ge04_fig2_axis_geometry_v1.json')
TARGETS={'ESO116-G12':'116readradialgraph.mr.eps','ESO079-G014':'79readradialgraph.mr.eps'}

def fetch():
 req=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');return tf.extractfile(tf.getmember('fig2.eps')).read()
def blocks(s):
 ls=s.splitlines();o={};st=None;nm=None
 for i,l in enumerate(ls):
  if l.startswith('%%BeginDocument:'):st=i;nm=l.split(':',1)[1].strip()
  elif l.startswith('%%EndDocument') and st is not None:o[nm]='\n'.join(ls[st:i+1]);st=None;nm=None
 return o
def toks(txt):
 for li,line in enumerate(txt.splitlines(),1):
  if '%' in line:line=line.split('%',1)[0]
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|/?[A-Za-z][A-Za-z0-9_.-]*',line):yield li,t
def parse(txt):
 stack=[];cur=None;path=[];fills=[];segs=[]
 def num(t):
  try:return float(t)
  except:return None
 def pop(n):
  if len(stack)<n:return None
  a=stack[-n:];del stack[-n:];return a if all(isinstance(x,(int,float)) for x in a) else None
 def addseg(a,b,li,op):
  if a is not None and b is not None:segs.append({'line':li,'a':list(a),'b':list(b),'dx':b[0]-a[0],'dy':b[1]-a[1],'length':math.hypot(b[0]-a[0],b[1]-a[1]),'op':op})
 def fill(li):
  nonlocal path
  if len(path)>=3:
   pts=path[:]
   if pts[-1]!=pts[0]:pts.append(pts[0])
   xs=[p[0] for p in pts];ys=[p[1] for p in pts]
   fills.append({'line':li,'n_points':len(pts),'points':[list(p) for p in pts],'bbox':[min(xs),min(ys),max(xs),max(ys)],'center':[(min(xs)+max(xs))/2,(min(ys)+max(ys))/2],'width':max(xs)-min(xs),'height':max(ys)-min(ys)})
  path=[]
 for li,t in toks(txt):
  v=num(t)
  if v is not None:stack.append(v);continue
  if t.startswith('/'):continue
  if t in {'M','B','F'}:
   a=pop(2)
   if a:cur=(a[0],a[1]);path=[cur]
  elif t=='L':
   a=pop(2)
   if a and cur is not None:
    old=cur;cur=(a[0],a[1]);addseg(old,cur,li,'L');path.append(cur)
  elif t=='l':
   a=pop(2)
   if a and cur is not None:
    old=cur;cur=(cur[0]+a[0],cur[1]+a[1]);addseg(old,cur,li,'l');path.append(cur)
  elif t=='m':
   a=pop(2)
   if a and cur is not None:cur=(cur[0]+a[0],cur[1]+a[1]);path=[cur]
  elif t in {'CF','ef','eofill','fill'}:fill(li)
  elif t=='cp':
   if path and path[-1]!=path[0]:addseg(path[-1],path[0],li,'cp');path.append(path[0])
  elif len(stack)>24:stack=stack[-24:]
 return fills,segs

def main():
 b=fetch();bs=blocks(b.decode('latin-1','replace'));res={}
 for g,n in TARGETS.items():
  fills,segs=parse(bs[n]);cir=[f for f in fills if f['n_points'] in {7,8} and 35<=f['width']<=60 and 30<=f['height']<=55]
  tri=[f for f in fills if f['n_points'] in {4,5} and 35<=f['width']<=60 and 30<=f['height']<=55]
  horiz=[s for s in segs if abs(s['dy'])<=1 and abs(s['dx'])>=300];vert=[s for s in segs if abs(s['dx'])<=1 and abs(s['dy'])>=300]
  # retain unique geometries
  def uniq(arr):
   seen=set();o=[]
   for s in sorted(arr,key=lambda q:(q['line'],q['a'],q['b'])):
    k=tuple(round(x,3) for x in (*s['a'],*s['b']))
    if k not in seen:seen.add(k);o.append(s)
   return o
  res[g]={'block':n,'block_sha256':hashlib.sha256(bs[n].encode('latin-1','replace')).hexdigest(),'circle_count':len(cir),'circle_centers':[f['center'] for f in cir],'circle_records':cir,'triangle_count':len(tri),'triangle_centers':[f['center'] for f in tri],'long_horizontal_segments':uniq(horiz)[:100],'long_vertical_segments':uniq(vert)[:100]}
 out={'status':'GE04_FIG2_AXIS_GEOMETRY_INSPECTED','asset_sha256':hashlib.sha256(b).hexdigest(),'targets':res,'visual_axis_labels_from_published_pdf':{'ESO116-G12':{'r_arcsec_labeled':[0,50,100,150,200],'sigma_hi_msun_pc2_labeled':[0,2,4,6,8,10]},'ESO079-G014':{'r_arcsec_labeled':[0,50,100,150],'sigma_hi_msun_pc2_labeled':[0,2,4,6]}},'boundary':'Native vector coordinates plus printed-axis label transcription only; no raster data digitization, PostScript execution, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'targets':{g:{'circle_count':v['circle_count'],'circle_centers':v['circle_centers'],'triangle_count':v['triangle_count'],'horiz':v['long_horizontal_segments'],'vert':v['long_vertical_segments']} for g,v in res.items()}},indent=2))
if __name__=='__main__':main()
