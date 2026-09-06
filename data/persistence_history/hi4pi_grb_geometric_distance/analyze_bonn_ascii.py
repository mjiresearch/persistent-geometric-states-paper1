#!/usr/bin/env python3
"""Screen GRB geometric-distance residuals using Bonn-served EBHIS/GASS ASCII profiles.

Parses the public Bonn profile-service ASCII output, detects significant H I
emission peaks in the appropriate observed survey profile, and compares their
centroids with the Reid et al. (2019) URC velocity evaluated at the direct X-ray
dust distance. This is a screening analysis: component association is the
nearest significant outer-Galaxy-sign peak to the model prediction and is
therefore explicitly model-guided, not a confirmatory arm-identification rule.
"""
from __future__ import annotations
import json, math, re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, peak_widths
from scipy.optimize import curve_fit

ROOT=Path(__file__).resolve().parent
INDIR=ROOT/'bonn_ascii'
OUT=ROOT/'bonn_results'
OUT.mkdir(exist_ok=True)

R0=8.15; TH0=236.0; A2=0.96; A3=1.62
TARGETS={
 'GRB_221009A':(52.96,4.32),
 'GRB_160623A':(84.17,-2.69),
 'GRB_031203':(255.74,-4.80),
}
STRUCTURES=[
 ('GRB_221009A','Outer',13.9,0.1),
 ('GRB_221009A','OSC',19.0,0.2),
 ('GRB_160623A','Outer',9.9,0.6),
 ('GRB_031203','Outer',9.7,0.4),
]

def urc_shape(r):
    lam=(A3/1.5)**5
    beta=.72+.44*np.log10(lam)
    x=np.asarray(r,float)/(A2*R0)
    disk=beta*1.97*x**1.22/(x*x+.78**2)**1.43
    halo=1.6*np.exp(-.4*lam)*x*x/(x*x+1.5**2*lam**.4)
    return np.sqrt(disk+halo)
URC0=float(urc_shape(R0))
def theta(r): return float(TH0*urc_shape(r)/URC0)
def radius(d,l,b):
    lr=math.radians(l); br=math.radians(b); dp=d*math.cos(br)
    return math.sqrt(R0**2+dp**2-2*R0*dp*math.cos(lr))
def vpred(d,l,b):
    lr=math.radians(l); br=math.radians(b); r=radius(d,l,b)
    return (theta(r)*R0/r-TH0)*math.sin(lr)*math.cos(br)

def parse_sections(path):
    sections={}; current=None
    pat=re.compile(r'^%%(EBHIS|GASS|gauss)\s+(\d+)\s+datapoints')
    for raw in path.read_text().splitlines():
        m=pat.match(raw.strip())
        if m:
            current=m.group(1); sections[current]=[]; continue
        if current and raw.strip() and not raw.lstrip().startswith('%'):
            p=raw.split()
            if len(p)>=2:
                try: sections[current].append((float(p[0]),float(p[1])))
                except ValueError: pass
    return {k:np.asarray(v,float) for k,v in sections.items()}

def gauss(v,a,c,s,b): return b+a*np.exp(-.5*((v-c)/s)**2)
def peaks_for(arr):
    v=arr[:,0]; t=arr[:,1]; order=np.argsort(v); v=v[order]; t=t[order]
    edge=np.abs(v)>150
    med=float(np.median(t[edge])) if edge.sum()>10 else float(np.median(t))
    mad=float(np.median(np.abs(t[edge]-med))) if edge.sum()>10 else float(np.median(np.abs(t-med)))
    noise=max(1.4826*mad,.02)
    y=gaussian_filter1d(t-med,1)
    dv=float(np.median(np.diff(v)))
    idx,props=find_peaks(y,height=max(.25,5*noise),prominence=max(.20,5*noise),distance=max(2,int(2/max(abs(dv),.01))))
    widths=peak_widths(y,idx,rel_height=.5)[0]*abs(dv) if len(idx) else []
    rows=[]
    for j,i in enumerate(idx):
        c0=float(v[i]); a0=float(y[i]); f0=max(float(widths[j]),1.0); s0=f0/2.355
        win=np.abs(v-c0)<=max(8,1.6*f0)
        c=c0;a=a0;s=s0;b=med
        try:
            popt,_=curve_fit(gauss,v[win],t[win],p0=[a0,c0,s0,med],bounds=([0,c0-5,.3,-np.inf],[np.inf,c0+5,30,np.inf]),maxfev=10000)
            a,c,s,b=map(float,popt)
        except Exception: pass
        rows.append(dict(velocity_kms=c,amplitude_K=a,sigma_kms=s,fwhm_kms=2.355*s,prominence_K=float(props['prominences'][j]),noise_K=noise))
    return pd.DataFrame(rows),noise,med

def mc_sigma(d,sd,l,b,seed):
    rng=np.random.default_rng(seed); x=rng.normal(d,sd,20000); x=x[x>0]
    vv=np.array([vpred(float(z),l,b) for z in x]); return float(np.std(vv,ddof=1))

allpk=[]; meta={}
for name,(l,b) in TARGETS.items():
    sec=parse_sections(INDIR/f'{name}_spectrum.txt')
    # Vaia uses EBHIS for the two northern sightlines, GASS for GRB 031203.
    survey='GASS' if name=='GRB_031203' else 'EBHIS'
    arr=sec.get(survey,np.empty((0,2)))
    if len(arr)==0:
        raise RuntimeError(f'{name}: no {survey} samples in Bonn ASCII output')
    pk,noise,baseline=peaks_for(arr)
    pk.insert(0,'survey',survey); pk.insert(0,'target',name)
    pk.to_csv(OUT/f'{name}_detected_peaks.csv',index=False)
    allpk.append(pk); meta[name]={'survey':survey,'n_samples':len(arr),'noise_K':noise,'baseline_K':baseline,'n_peaks':len(pk)}
pkall=pd.concat(allpk,ignore_index=True); pkall.to_csv(OUT/'all_detected_peaks.csv',index=False)

rows=[]
for seed,(name,arm,d,sd) in enumerate(STRUCTURES,1):
    l,b=TARGETS[name]; vp=vpred(d,l,b); r=radius(d,l,b)
    cand=pkall[pkall.target==name].copy()
    sign=-1 if 0<(l%360)<180 else 1
    outer=cand[cand.velocity_kms*sign>5]
    if len(outer): cand=outer
    cand['abs_delta']=(cand.velocity_kms-vp).abs()
    best=cand.sort_values(['abs_delta','prominence_K'],ascending=[True,False]).iloc[0]
    rows.append(dict(target=name,arm=arm,distance_kpc=d,distance_sigma_kpc=sd,l_deg=l,b_deg=b,R_gal_kpc=r,
      theta_reid_kms=theta(r),v_reid_geometric_kms=vp,v_reid_sigma_distance_kms=mc_sigma(d,sd,l,b,seed),
      v_hi_peak_kms=float(best.velocity_kms),peak_fwhm_kms=float(best.fwhm_kms),peak_prominence_K=float(best.prominence_K),
      delta_v_obs_minus_reid_kms=float(best.velocity_kms-vp),abs_delta_v_kms=float(abs(best.velocity_kms-vp)),
      survey=str(best.survey),association='nearest significant outer-sign peak (model-guided screening)'))
res=pd.DataFrame(rows); res.to_csv(OUT/'geometric_kinematic_residuals.csv',index=False)

verdict={
 'test':'Bonn EBHIS/GASS GRB geometric-distance / Reid-URC screening',
 'status':'screening only; not a persistence detection',
 'association_caveat':'Nearest significant peak is model-guided; confirmatory arm/component association must be frozen independently.',
 'residuals':res[['target','arm','survey','v_reid_geometric_kms','v_hi_peak_kms','delta_v_obs_minus_reid_kms']].to_dict('records'),
 'max_abs_residual_kms':float(res.abs_delta_v_kms.max()),
 'all_abs_within_10_kms':bool((res.abs_delta_v_kms<=10).all()),
 'interpretation':('All model-guided matched residuals are <=10 km/s, so this screening analysis does not distinguish Persistence from ordinary non-circular gas motions.' if (res.abs_delta_v_kms<=10).all() else 'At least one residual exceeds 10 km/s; conventional streaming/warp and component-association controls are required before any persistence inference.'),
 'profile_meta':meta,
}
(OUT/'verdict.json').write_text(json.dumps(verdict,indent=2))
print(res.to_string(index=False)); print(json.dumps(verdict,indent=2))
