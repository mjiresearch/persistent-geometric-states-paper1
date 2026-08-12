#!/usr/bin/env python3
"""Calibrate Elson (2017) WHISP Appendix vector axes from published source constraints.

This is a publication-digitization calibration audit, not a model fit.
For each of the 19 frozen WHISP overlaps:
  * the exact red Sigma_HI vector path is read from the public arXiv Appendix PDF;
  * x=0 is the left plot border and Sigma=0 is the horizontal plot baseline;
  * Swaters et al. (2002) supplies source distance D, optical R-band scale
    length h, HI radius R_HI (Sigma_HI=1 Msun/pc^2), and mean HI surface
    density within 3.2h;
  * the two linear axis scales are solved from the R_HI=1 anchor and the
    published mean-density normalization;
  * inferred physical tick increments are reported as an independent geometry
    sanity check, not forced to preselected values.

No frozen SPARC distance/inclination is substituted, no helium is added, and
no persistence quantity is evaluated.
"""
from __future__ import annotations

import csv, io, json, math, tarfile
from pathlib import Path
from urllib.request import Request, urlopen
import fitz

ARXIV='https://export.arxiv.org/e-print/1709.03288'
PDFS=['profiles1_V2.pdf','profiles2_V2.pdf','profiles3_V2.pdf','profiles4_V2.pdf']
UGCS=[2023,2034,2455,3371,3711,3966,4173,4305,4325,4499,4543,5272,5414,5721,5829,5918,6446,6628,7047,7232,7261,7323,7399,7524,7559,7608,7690,7866,7971,8490,9211,9992,10310,11861,12060,12632,12732]
# Swaters 2002 Table 1 D,h and Table 2 R_HI,<Sigma_HI>_3.2h.
META={
 4325:(10.1,36,142,6.6),4499:(13.0,22,143,7.2),5414:(10.0,30,146,6.0),
 5721:(6.7,14,225,11.7),5829:(9.0,39,188,6.7),5918:(7.7,46,159,2.6),
 6446:(12.0,28,182,5.5),7261:(9.1,35,159,5.2),7323:(8.1,54,184,4.1),
 7399:(8.4,18,192,7.9),7524:(3.5,135,527,3.9),7559:(3.2,45,156,3.6),
 7690:(7.9,12,140,8.8),7866:(4.8,25,149,4.7),8490:(4.9,29,346,9.1),
 9992:(10.4,16,105,5.3),10310:(15.6,25,130,6.2),12632:(6.9,85,266,3.4),
 12732:(13.2,35,272,4.7),
}
TARGETS=set(META)
KPC_PER_ARCSEC_PER_MPC=1000/206265


def dl():
 r=Request(ARXIV,headers={'User-Agent':'PersistenceFrameworkPaperI/1.0'})
 with urlopen(r,timeout=90) as h:return h.read()
def col(c): return None if c is None else tuple(round(float(x),3) for x in c)
def lines(d):
 out=[]
 for it in d.get('items',[]):
  if it[0]=='l':
   p,q=it[1],it[2];out.append((float(p.x),float(p.y),float(q.x),float(q.y)))
 return out

def panel_paths(tf):
 ans=[]; offset=0
 for pi,name in enumerate(PDFS):
  doc=fitz.open(stream=tf.extractfile(name).read(),filetype='pdf');page=doc[0]
  reds=[]
  for d in page.get_drawings():
   if col(d.get('color'))==(1.0,0.0,0.0):
    seg=lines(d)
    if len(seg)>=20: reds.append((d,seg))
  items=[]
  for d,seg in reds:
   r=d['rect']; items.append({'d':d,'seg':seg,'cx':(r.x0+r.x1)/2,'cy':(r.y0+r.y1)/2})
  items.sort(key=lambda x:x['cy'])
  rows=[]
  for item in items:
   if not rows or abs(item['cy']-sum(x['cy'] for x in rows[-1])/len(rows[-1]))>80:
    rows.append([item])
   else: rows[-1].append(item)
  ordered=[]
  for row in rows: ordered.extend(sorted(row,key=lambda x:x['cx']))
  expected=12 if pi<3 else 1
  if len(ordered)!=expected: raise RuntimeError(f'{name}: expected {expected} red paths, got {len(ordered)}')
  for j,item in enumerate(ordered):
   ugc=UGCS[offset+j]
   ans.append((ugc,name,j,page,item['d'],item['seg']))
  offset+=expected
 if offset!=37: raise RuntimeError(offset)
 return ans

def baseline_and_ticks(page, red):
 r=red['rect']; x0,x1=r.x0,r.x1
 h=[]; v=[]
 for d in page.get_drawings():
  if col(d.get('color'))!=(0.0,0.0,0.0): continue
  for xa,ya,xb,yb in lines(d):
   if abs(ya-yb)<0.08 and min(xa,xb)<=x0+0.2 and max(xa,xb)>=x1-0.2:
    h.append((abs(xb-xa), (ya+yb)/2))
  for xa,ya,xb,yb in lines(d):
   if abs(xa-xb)<0.08 and 2.0<=abs(yb-ya)<=5.0 and x0-0.3<=xa<=x1+0.3:
    v.append((xa,min(ya,yb),max(ya,yb),abs(yb-ya)))
 if not h: raise RuntimeError('baseline not found')
 y0=max(h,key=lambda z:z[0])[1]
 xt=sorted({round(x,3) for x,ya,yb,l in v if abs(yb-y0)<0.25 or abs(ya-y0)<0.25})
 yt=[]
 for d in page.get_drawings():
  if col(d.get('color'))!=(0.0,0.0,0.0): continue
  for xa,ya,xb,yb in lines(d):
   if abs(ya-yb)<0.08 and 2.0<=abs(xb-xa)<=5.0:
    lo,hi=sorted((xa,xb))
    if abs(lo-x0)<0.25 or abs(hi-x0)<0.25:
     yy=(ya+yb)/2
     if r.y0-80<=yy<=y0+2: yt.append(round(yy,3))
 xt=dedupe(xt,0.5); yt=dedupe(sorted(yt),0.5)
 return y0,xt,yt

def dedupe(vals,tol):
 out=[]
 for v in vals:
  if not out or abs(v-out[-1])>tol:out.append(v)
 return out

def vertices(seg): return [(seg[0][0],seg[0][1])]+[(s[2],s[3]) for s in seg]
def interp_y(verts,x):
 if x<verts[0][0] or x>verts[-1][0]: return None
 for (x0,y0),(x1,y1) in zip(verts,verts[1:]):
  if x0<=x<=x1 or x1<=x<=x0:
   if abs(x1-x0)<1e-12:return (y0+y1)/2
   t=(x-x0)/(x1-x0);return y0+t*(y1-y0)
 return verts[-1][1]
def integral_fu(verts,ybase,u_max):
 xleft=verts[0][0]; xmax=xleft+u_max
 pts=[]
 for x,y in verts:
  if xleft<=x<=xmax:pts.append((x-xleft,ybase-y))
 if not pts or pts[0][0]>1e-8:
  y=interp_y(verts,xleft);pts.insert(0,(0,ybase-y))
 if pts[-1][0]<u_max-1e-8:
  y=interp_y(verts,xmax)
  if y is None:return None
  pts.append((u_max,ybase-y))
 total=0.0
 for (u0,f0),(u1,f1) in zip(pts,pts[1:]):
  if u1==u0:continue
  m=(f1-f0)/(u1-u0);c=f0-m*u0
  total += m*(u1**3-u0**3)/3 + c*(u1**2-u0**2)/2
 return total

def solve_scale(verts,ybase,rhi,r3,mean):
 width=verts[-1][0]-verts[0][0]
 amin=max(rhi,r3)/width*1.00001
 amax=amin*20
 def evala(a):
  xr=verts[0][0]+rhi/a; yr=interp_y(verts,xr)
  if yr is None:return None
  fr=ybase-yr
  if fr<=0:return None
  b=1/fr
  I=integral_fu(verts,ybase,r3/a)
  if I is None:return None
  pred=2*b*a*a*I/(r3*r3)
  return pred-mean,b,pred,fr,xr
 samples=[]
 for i in range(500):
  a=amin*(amax/amin)**(i/499)
  e=evala(a)
  if e is not None:samples.append((a,e))
 roots=[]
 for (a0,e0),(a1,e1) in zip(samples,samples[1:]):
  if e0[0]==0 or e0[0]*e1[0]<0:
   lo,hi=a0,a1
   elo=e0
   for _ in range(70):
    mid=(lo+hi)/2;em=evala(mid)
    if em is None:break
    if elo[0]*em[0]<=0:hi=mid
    else:lo=mid;elo=em
   a=(lo+hi)/2;e=evala(a)
   if e is not None: roots.append((a,e))
 if not roots and samples:
  a,e=min(samples,key=lambda z:abs(z[1][0]));roots=[(a,e)]
 return roots, len(samples), amin, amax

def nice_distance(v):
 nice=[0.1,0.2,0.25,0.5,1,2,2.5,5,10,20,25,50,100,200,250,500]
 n=min(nice,key=lambda z:abs(math.log(max(v,1e-9)/z)))
 return n,abs(v-n)/n

def main():
 raw=dl();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
 with open('validation/stationary/stationary_split_v1.csv',newline='',encoding='utf-8-sig') as fh:
  roles={r['galaxy']:r['stationary_role'] for r in csv.DictReader(fh)}
 out=[]
 for ugc,pdf,panel,page,red,seg in panel_paths(tf):
  if ugc not in TARGETS:continue
  D,h_arc,rhi_arc,mean=META[ugc]; conv=D*KPC_PER_ARCSEC_PER_MPC
  rhi=rhi_arc*conv; r3=3.2*h_arc*conv
  ybase,xt,yt=baseline_and_ticks(page,red); vv=vertices(seg)
  roots,n_samples,amin,amax=solve_scale(vv,ybase,rhi,r3,mean)
  dx=[b-a for a,b in zip(xt,xt[1:]) if b-a>1]
  dy=[b-a for a,b in zip(yt,yt[1:]) if b-a>1]
  dxt=sorted(dx)[len(dx)//2] if dx else None; dyt=sorted(dy)[len(dy)//2] if dy else None
  cand=[]
  for a,e in roots:
   err,b,pred,fr,xr=e
   xinc=a*dxt if dxt else None;yinc=b*dyt if dyt else None
   xn,xe=nice_distance(xinc) if xinc else (None,None);yn,ye=nice_distance(yinc) if yinc else (None,None)
   cand.append({'kpc_per_pdf_x':a,'sigma_per_pdf_y':b,'mean_pred':pred,'mean_target':mean,'mean_abs_error':abs(pred-mean),'rhi_x_pdf':xr,
                'x_tick_pdf':dxt,'x_tick_kpc':xinc,'x_tick_nice':xn,'x_tick_frac_error':xe,
                'y_tick_pdf':dyt,'y_tick_sigma':yinc,'y_tick_nice':yn,'y_tick_frac_error':ye,
                'nice_score':(xe if xe is not None else 9)+(ye if ye is not None else 9)})
  cand.sort(key=lambda z:(z['mean_abs_error']>1e-6,z['nice_score'],z['mean_abs_error']))
  best=cand[0] if cand else None
  out.append({'galaxy':f'UGC{ugc:05d}','stationary_role':roles.get(f'UGC{ugc:05d}'), 'source_pdf':pdf,'panel_index':panel,
              'source_distance_mpc':D,'source_h_arcsec':h_arc,'source_rhi_arcsec':rhi_arc,'source_rhi_kpc':rhi,
              'source_mean_sigma_hi_3p2h':mean,'source_r3p2h_kpc':r3,'plot_x0_pdf':vv[0][0],'plot_x1_pdf':vv[-1][0],'plot_y0_pdf':ybase,
              'n_vector_vertices':len(vv),'x_ticks_pdf':xt,'y_ticks_pdf':yt,
              'search_valid_samples':n_samples,'search_a_min':amin,'search_a_max':amax,
              'calibration_status':'solved_or_approximate' if best else 'no_valid_scale_candidate',
              'candidates':cand[:5],'best':best})
 solved=[r for r in out if r['best'] is not None]
 unsolved=[r['galaxy'] for r in out if r['best'] is None]
 summary={'status':'ELSON2017_WHISP_VECTOR_AXIS_CALIBRATION_AUDIT','n_targets':len(out),'n_with_candidate':len(solved),'n_without_candidate':len(unsolved),'unsolved_galaxies':unsolved,'targets':out,
          'boundary':'Axes recovered only from public vector geometry and Swaters published source constraints. No SPARC-distance substitution, helium scaling, interpolation to Paper-I grid, persistence fitting, or blind-outcome inspection.'}
 p=Path('validation/stationary/elson2017_whisp_vector_axis_calibration_v1.json');p.write_text(json.dumps(summary,indent=2)+'\n')
 print('TARGETS',len(out),'WITH_CANDIDATE',len(solved),'UNSOLVED',unsolved)
 for r in out:
  b=r['best']
  if b is None:
   print(r['galaxy'],r['stationary_role'],'NO_CANDIDATE','valid_samples',r['search_valid_samples'],'a_range',r['search_a_min'],r['search_a_max'])
  else:
   print(r['galaxy'],r['stationary_role'],'a',round(b['kpc_per_pdf_x'],6),'b',round(b['sigma_per_pdf_y'],6),'xtick',round(b['x_tick_kpc'],4) if b['x_tick_kpc'] else None,'~',b['x_tick_nice'],'ytick',round(b['y_tick_sigma'],4) if b['y_tick_sigma'] else None,'~',b['y_tick_nice'],'nice',round(b['nice_score'],4),'meanerr',round(b['mean_abs_error'],5),'candidates',len(r['candidates']))
if __name__=='__main__':main()
