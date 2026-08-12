#!/usr/bin/env python3
"""Extract Hallenbeck+2014 Figure 9 H I profiles from source-native IDL EPS.

The arXiv source contains fig-density.eps as vector PostScript. IDL encodes each
H I radial sample as a filled circular path (F), followed by a matching vertical
error-bar path. This script statically parses only M/R/F/D plus color/dash state;
PostScript is never executed. It maps source coordinates to the published Figure
9 axes (x: 0--70 kpc; y: 0--25 Msun/pc^2) and validates against the paper's
published R_HI at Sigma_HI=1 Msun/pc^2.

No OCR, raster digitization, map-to-profile reconstruction, profile fitting,
persistence fitting, or blind-outcome inspection is performed.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, re, tarfile, urllib.request
from pathlib import Path

URLS=['https://arxiv.org/e-print/1407.1744','https://export.arxiv.org/e-print/1407.1744']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
EPS='fig-density.eps'
VALID=Path('validation/stationary/ha14_vector_hi_profile_extraction_v1.json')
CSVOUT=Path('data/stationary/source_reconstruction/ha14_vector_hi_profiles_v1.csv')
PANELS={
 'UGC09037': {'x0':2220.0,'x1':14574.0,'y0':11568.0,'y1':19616.0,'color_line':470,'published_rhi_kpc':42.09,'published_rhi_err_kpc':0.72},
 'UGC12506': {'x0':2220.0,'x1':14574.0,'y0':1408.0,'y1':9456.0,'color_line':956,'published_rhi_kpc':57.8,'published_rhi_err_kpc':1.9},
}

def fetch():
 attempts=[]
 for u in URLS:
  rec={'url':u}
  try:
   req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
   with urllib.request.urlopen(req,timeout=180) as h: raw=h.read();rec.update({'status':'fetched','final_url':h.geturl(),'content_type':h.headers.get('Content-Type',''),'bytes':len(raw)});attempts.append(rec);return raw,attempts
  except Exception as e:rec.update({'status':'error','error':f'{type(e).__name__}: {e}'});attempts.append(rec)
 raise RuntimeError('Ha14 source fetch failed')

def parse_paths(b):
 lines=b.decode('latin-1','replace').splitlines(); start=next((i for i,l in enumerate(lines) if l.startswith('%%EndPageSetup')),0)+1
 toks=[]
 for li,line in enumerate(lines[start:],start+1):
  if '%' in line:line=line.split('%',1)[0]
  line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
  toks += [(li,t) for t in re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|[A-Za-z][A-Za-z0-9_]*',line)]
 stack=[];cur=None;path=[];path_start=None;color=(0.,0.,0.);dash='L0';fills=[];strokes=[]
 def num(t):
  try:return float(t)
  except:return None
 def popn(n):
  if len(stack)<n:return None
  a=stack[-n:];del stack[-n:]
  return a if all(isinstance(x,(int,float)) for x in a) else None
 def finalize(kind,line):
  nonlocal path,path_start
  if len(path)>=2:
   xs=[p[0] for p in path];ys=[p[1] for p in path]
   rec={'kind':kind,'start_line':path_start,'end_line':line,'color':list(color),'dash':dash,'points':[list(p) for p in path],
        'bbox':[min(xs),min(ys),max(xs),max(ys)],'n_points':len(path)}
   (fills if kind=='F' else strokes).append(rec)
  path=[];path_start=None
 for li,t in toks:
  v=num(t)
  if v is not None:stack.append(v);continue
  if t=='M':
   a=popn(2)
   if a:cur=(a[0],a[1]);path=[cur];path_start=li
  elif t=='R':
   a=popn(2)
   if a and cur is not None:cur=(cur[0]+a[0],cur[1]+a[1]);path.append(cur)
  elif t=='P':
   a=popn(2)
   if a:cur=(a[0],a[1]);path.append(cur)
  elif t=='F':finalize('F',li)
  elif t=='D':finalize('D',li)
  elif t in {'L0','L1','L2','L3','L4','L5'}:dash=t
  elif t=='setrgbcolor':
   a=popn(3)
   if a:color=tuple(a)
  elif t in {'setgray','K'}:
   a=popn(1)
   if a:color=(a[0],)*3
  elif len(stack)>12:stack=stack[-12:]
 return fills,strokes,lines

def is_black(rec):return max(abs(c) for c in rec['color'])<1e-10

def panel_circle_candidates(fills,p):
 out=[]
 for f in fills:
  if not is_black(f) or f['dash']!='L0' or f['end_line']>=p['color_line']:continue
  x0,y0,x1,y1=f['bbox'];w=x1-x0;h=y1-y0;cx=(x0+x1)/2;cy=(y0+y1)/2
  if p['x0']<cx<p['x1'] and p['y0']<cy<p['y1'] and 90<=w<=140 and 90<=h<=140 and 0.75<=w/h<=1.25:
   q=dict(f);q.update({'center':[cx,cy],'width':w,'height':h});out.append(q)
 out.sort(key=lambda r:r['start_line']);return out

def choose_monotonic_cluster(cands):
 # Consecutive source-order circle groups with monotonically increasing center x and quasi-regular step.
 groups=[];cur=[]
 for c in cands:
  if not cur:cur=[c];continue
  dx=c['center'][0]-cur[-1]['center'][0]
  if 100<=dx<=400 and c['start_line']-cur[-1]['end_line']<=4:cur.append(c)
  else:
   if len(cur)>=3:groups.append(cur)
   cur=[c]
 if len(cur)>=3:groups.append(cur)
 if not groups:raise RuntimeError('No radial-marker cluster found')
 return max(groups,key=len),groups

def errorbar_candidates(strokes,p):
 out=[]
 for s in strokes:
  if not is_black(s) or s['dash']!='L0' or s['end_line']>=p['color_line']:continue
  x0,y0,x1,y1=s['bbox'];w=x1-x0;h=y1-y0;cx=(x0+x1)/2
  # Ha14 vertical error bars: ~123 source-unit caps and substantive vertical span.
  if p['x0']<cx<p['x1'] and p['y0']<=y0<y1<=p['y1'] and 100<=w<=145 and h>=40 and s['n_points']>=5:
   q=dict(s);q.update({'center_x':cx,'low_y':y0,'high_y':y1,'width':w,'height':h});out.append(q)
 out.sort(key=lambda r:r['start_line']);return out

def mapx(x,p):return (x-p['x0'])*70.0/(p['x1']-p['x0'])
def mapy(y,p):return (y-p['y0'])*25.0/(p['y1']-p['y0'])

def crossing_radius(rows,target=1.0):
 # Linear interpolation in the outer descending branch around Sigma=target.
 for a,b in zip(rows[-1:0:-1],rows[-2::-1]):
  ya,yb=a['sigma_hi_msun_pc2'],b['sigma_hi_msun_pc2']
  if (ya-target)*(yb-target)<=0 and ya!=yb:
   return a['radius_kpc']+(target-ya)*(b['radius_kpc']-a['radius_kpc'])/(yb-ya)
 return None

def main():
 raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');epsb=tf.extractfile(tf.getmember(EPS)).read();fills,strokes,lines=parse_paths(epsb)
 allrows=[];summary={}
 for gal,p in PANELS.items():
  circles=panel_circle_candidates(fills,p);cluster,groups=choose_monotonic_cluster(circles);bars=errorbar_candidates(strokes,p)
  # Keep bars source-local to marker cluster: after the final marker and before legend; match by x center.
  lo=min(c['center'][0] for c in cluster)-100;hi=max(c['center'][0] for c in cluster)+100
  local=[b for b in bars if lo<=b['center_x']<=hi and b['start_line']>=cluster[-1]['end_line']]
  used=set();rows=[]
  for i,c in enumerate(cluster):
   cx,cy=c['center'];best=None;bd=None
   for j,b in enumerate(local):
    if j in used:continue
    d=abs(b['center_x']-cx)
    if bd is None or d<bd:bd=d;best=(j,b)
   bar=None
   if best and bd<=3.0:used.add(best[0]);bar=best[1]
   r=mapx(cx,p);sig=mapy(cy,p)
   row={'galaxy':gal,'radius_kpc':r,'sigma_hi_msun_pc2':sig,
        'sigma_hi_err_minus_msun_pc2':None if bar is None else sig-mapy(bar['low_y'],p),
        'sigma_hi_err_plus_msun_pc2':None if bar is None else mapy(bar['high_y'],p)-sig,
        'source_center_x':cx,'source_center_y':cy,'source_marker_start_line':c['start_line'],'source_marker_end_line':c['end_line'],
        'source_errorbar_start_line':None if bar is None else bar['start_line'],'source_errorbar_end_line':None if bar is None else bar['end_line']}
   rows.append(row);allrows.append(row)
  rhi=crossing_radius(rows,1.0)
  summary[gal]={'n_circle_candidates':len(circles),'marker_group_lengths':[len(g) for g in groups],'n_profile_points':len(rows),'n_matched_errorbars':sum(r['source_errorbar_start_line'] is not None for r in rows),
                'first_radius_kpc':rows[0]['radius_kpc'],'last_radius_kpc':rows[-1]['radius_kpc'],'min_sigma':min(r['sigma_hi_msun_pc2'] for r in rows),'max_sigma':max(r['sigma_hi_msun_pc2'] for r in rows),
                'interpolated_r_at_sigma1_kpc':rhi,'published_rhi_kpc':p['published_rhi_kpc'],'published_rhi_err_kpc':p['published_rhi_err_kpc'],
                'rhi_delta_kpc':None if rhi is None else rhi-p['published_rhi_kpc'],'rows':rows}
  # stringent QC: source series should reproduce published RHI within 2 sigma + half-bin allowance.
  if rhi is None or abs(rhi-p['published_rhi_kpc']) > 2*p['published_rhi_err_kpc']+max(1.0,(rows[1]['radius_kpc']-rows[0]['radius_kpc'])/2):
   raise RuntimeError(f'{gal}: vector profile fails published RHI QC: {rhi} vs {p["published_rhi_kpc"]}')
 CSVOUT.parent.mkdir(parents=True,exist_ok=True)
 fields=['galaxy','radius_kpc','sigma_hi_msun_pc2','sigma_hi_err_minus_msun_pc2','sigma_hi_err_plus_msun_pc2','source_center_x','source_center_y','source_marker_start_line','source_marker_end_line','source_errorbar_start_line','source_errorbar_end_line']
 with CSVOUT.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in allrows:
   rr={k:r[k] for k in fields}
   for k in ['radius_kpc','sigma_hi_msun_pc2','sigma_hi_err_minus_msun_pc2','sigma_hi_err_plus_msun_pc2']:
    if rr[k] is not None:rr[k]=f'{rr[k]:.9g}'
   w.writerow(rr)
 out={'status':'HA14_NATIVE_VECTOR_HI_PROFILES_RECOVERED','source':'Hallenbeck et al. 2014 AJ 148 69','arxiv':'1407.1744','figure':'Figure 9 / fig-density.eps','source_package_attempts':attempts,'source_package_sha256':hashlib.sha256(raw).hexdigest(),'eps_sha256':hashlib.sha256(epsb).hexdigest(),
      'axis_mapping':{'x_source':[2220,14574],'x_kpc':[0,70],'y_top_source':[11568,19616],'y_bottom_source':[1408,9456],'y_sigma_hi_msun_pc2':[0,25]},
      'profile_csv':str(CSVOUT),'profiles':summary,
      'provenance_rule':'Values are decoded from source-native filled-circle and error-bar vector primitives in the authors arXiv EPS; no raster sampling or curve fitting.',
      'boundary':'Acquisition/provenance only. No OCR, raster digitization, map-to-profile reconstruction, normalization, persistence fitting, or blind-outcome inspection.'}
 VALID.parent.mkdir(parents=True,exist_ok=True);VALID.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'csv':str(CSVOUT),'summary':{g:{k:v for k,v in s.items() if k!='rows'} for g,s in summary.items()}},indent=2))
if __name__=='__main__':main()
