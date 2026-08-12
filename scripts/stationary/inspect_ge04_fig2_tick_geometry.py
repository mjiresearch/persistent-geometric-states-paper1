#!/usr/bin/env python3
"""Extract Ge04 Fig.2 native axis tick geometry for exact affine calibration."""
from __future__ import annotations
import io,json,math,re,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/astro-ph/0403154';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/ge04_fig2_tick_geometry_v1.json')
TARGETS={'ESO116-G12':'116readradialgraph.mr.eps','ESO079-G014':'79readradialgraph.mr.eps'};FRAME=(401.,328.,1823.,1313.)
def getblocks():
 req=urllib.request.Request(URL,headers={'User-Agent':UA});
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');s=tf.extractfile(tf.getmember('fig2.eps')).read().decode('latin-1','replace');ls=s.splitlines();o={};st=None;nm=None
 for i,l in enumerate(ls):
  if l.startswith('%%BeginDocument:'):st=i;nm=l.split(':',1)[1].strip()
  elif l.startswith('%%EndDocument') and st is not None:o[nm]='\n'.join(ls[st:i+1]);st=None;nm=None
 return o
def tokens(txt):
 for li,line in enumerate(txt.splitlines(),1):
  if '%' in line:line=line.split('%',1)[0]
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|/?[A-Za-z][A-Za-z0-9_.-]*',line):yield li,t
def segs(txt):
 stack=[];cur=None;o=[]
 def num(t):
  try:return float(t)
  except:return None
 def pop(n):
  if len(stack)<n:return None
  a=stack[-n:];del stack[-n:];return a if all(isinstance(x,(int,float)) for x in a) else None
 for li,t in tokens(txt):
  v=num(t)
  if v is not None:stack.append(v);continue
  if t.startswith('/'):continue
  if t in {'M','B','F'}:
   a=pop(2)
   if a:cur=(a[0],a[1])
  elif t=='L':
   a=pop(2)
   if a and cur is not None:
    old=cur;cur=(a[0],a[1]);o.append((li,old,cur))
  elif t=='l':
   a=pop(2)
   if a and cur is not None:
    old=cur;cur=(cur[0]+a[0],cur[1]+a[1]);o.append((li,old,cur))
  elif t=='m':
   a=pop(2)
   if a and cur is not None:cur=(cur[0]+a[0],cur[1]+a[1])
  elif len(stack)>24:stack=stack[-24:]
 return o
def main():
 bs=getblocks();x0,y0,x1,y1=FRAME;res={}
 for g,n in TARGETS.items():
  ss=segs(bs[n]);xt=[];yt=[]
  for li,a,b in ss:
   dx=b[0]-a[0];dy=b[1]-a[1]
   # x ticks are vertical, touch top or bottom frame, short <=100 source units
   if abs(dx)<=1 and 4<=abs(dy)<=100 and (abs(a[1]-y0)<=1 or abs(b[1]-y0)<=1 or abs(a[1]-y1)<=1 or abs(b[1]-y1)<=1) and x0-2<=a[0]<=x1+2:
    xt.append({'line':li,'x':round((a[0]+b[0])/2,3),'length':round(abs(dy),3),'a':list(a),'b':list(b)})
   # y ticks are horizontal, touch left/right frame
   if abs(dy)<=1 and 4<=abs(dx)<=100 and (abs(a[0]-x0)<=1 or abs(b[0]-x0)<=1 or abs(a[0]-x1)<=1 or abs(b[0]-x1)<=1) and y0-2<=a[1]<=y1+2:
    yt.append({'line':li,'y':round((a[1]+b[1])/2,3),'length':round(abs(dx),3),'a':list(a),'b':list(b)})
  def groups(arr,key):
   d={}
   for r in arr:
    k=r[key];d.setdefault(k,[]).append(r['length'])
   return [{'position':k,'lengths':sorted(v),'max_length':max(v),'count':len(v)} for k,v in sorted(d.items())]
  res[g]={'x_tick_positions':groups(xt,'x'),'y_tick_positions':groups(yt,'y')}
 out={'status':'GE04_FIG2_TICK_GEOMETRY_INSPECTED','frame_source':{'x0':x0,'x1':x1,'y0':y0,'y1':y1},'targets':res,
      'published_label_transcription':{'ESO116-G12':{'x_major_arcsec':[0,50,100,150,200],'y_major_sigma':[0,2,4,6,8,10]},'ESO079-G014':{'x_major_arcsec':[0,50,100,150],'y_major_sigma':[0,2,4,6]}},
      'boundary':'Static vector tick geometry and printed label transcription only; no raster data digitization, PostScript execution, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
