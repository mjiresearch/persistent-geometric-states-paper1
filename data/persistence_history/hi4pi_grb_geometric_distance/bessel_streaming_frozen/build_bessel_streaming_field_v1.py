#!/usr/bin/env python3
"""Build the frozen conventional BeSSeL/maser streaming field v1.

This script is intentionally forbidden from reading the GRB H I velocities or
residual products.  Its only GRB input is frozen geometry (l,b,d).
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from urllib.request import urlopen, Request

import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord, Galactocentric, CartesianDifferential

ROOT = Path(__file__).resolve().parent
RAW_URL = "https://cdsarc.cds.unistra.fr/ftp/J/ApJ/885/131/table1.dat"
RAW_PATH = ROOT / "reid2019_table1.dat"
TARGET_PATH = ROOT / "frozen_grb_geometry_only.csv"
OUTDIR = ROOT / "outputs_v1"
OUTDIR.mkdir(parents=True, exist_ok=True)

# Reid et al. 2019 A5 constants
R0 = 8.15
Z_SUN = 0.0055
U_SUN = 10.6
V_SUN = 10.7
W_SUN = 7.6
THETA0 = 236.0
A2 = 0.96
A3 = 1.62
STD_U, STD_V, STD_W = 10.0, 15.0, 7.0
SIGMA_INT = 7.0
BANDWIDTHS = np.array([1.0,1.5,2.0,2.5,3.0,4.0,5.0], dtype=float)
MC_DRAWS = 256
MC_SEED = 20260906
BOOT_DRAWS = 2000
BOOT_SEED = 20260907


def urc_theta(R):
    R = np.asarray(R, dtype=float)
    lam = (A3 / 1.5) ** 5
    Ropt = A2 * R0
    rho = R / Ropt
    log_lam = np.log10(lam)
    term1 = 200.0 * lam ** 0.41
    term2 = np.sqrt(0.80 + 0.49*log_lam + 0.75*np.exp(-0.4*lam)/(0.47 + 2.25*lam**0.4))
    term3 = (0.72 + 0.44*log_lam) * (1.97*rho**1.22 / (rho**2 + 0.61)**1.43)
    term4 = 1.6*np.exp(-0.4*lam) * (rho**2 / (rho**2 + 2.25*lam**0.4))
    return (term1/term2) * np.sqrt(term3 + term4)


def gc_frame():
    # Astropy's x-axis points from the Sun toward the Galactic center, so
    # +v_x corresponds to conventional +U (toward the center).
    return Galactocentric(
        galcen_distance=R0*u.kpc,
        z_sun=Z_SUN*u.kpc,
        galcen_v_sun=CartesianDifferential(
            [U_SUN, THETA0 + V_SUN, W_SUN] * (u.km/u.s)
        ),
    )


def parse_num(s, cast=float):
    s = s.strip()
    if not s:
        return np.nan
    return cast(s)


def parse_reid_table(path: Path):
    rows=[]
    for line in path.read_text(errors='replace').splitlines():
        if not line.strip():
            continue
        try:
            name=line[0:13].strip()
            oname=line[15:30].strip()
            rah=parse_num(line[31:33], int); ram=parse_num(line[34:36], int); ras=parse_num(line[37:44])
            desgn=line[46:47].strip() or '+'
            ded=parse_num(line[47:49], int); dem=parse_num(line[50:52], int); des=parse_num(line[53:59])
            plx=parse_num(line[62:67]); eplx=parse_num(line[68:73])
            pme=parse_num(line[76:82]); epme=parse_num(line[83:87])
            pmn=parse_num(line[90:96]); epmn=parse_num(line[97:101])
            vlsr=parse_num(line[104:108]); evlsr=parse_num(line[109:111])
            arm=line[113:116].strip()
            if not name or not np.isfinite(plx):
                continue
            ra_deg=15.0*(rah + ram/60.0 + ras/3600.0)
            dec_abs=ded + dem/60.0 + des/3600.0
            dec_deg=(-1 if desgn=='-' else 1)*dec_abs
            rows.append(dict(name=name,oname=oname,ra_deg=ra_deg,dec_deg=dec_deg,
                             plx_mas=plx,e_plx_mas=eplx,pmE=pme,e_pmE=epme,
                             pmN=pmn,e_pmN=epmn,VLSR=vlsr,e_VLSR=evlsr,arm=arm))
        except Exception:
            continue
    return pd.DataFrame(rows)


def lsr_to_helio(ra_deg, dec_deg, vlsr):
    c=SkyCoord(ra=ra_deg*u.deg, dec=dec_deg*u.deg, frame='icrs').galactic
    l=c.l.radian; b=c.b.radian
    proj = STD_U*np.cos(l)*np.cos(b) + STD_V*np.sin(l)*np.cos(b) + STD_W*np.sin(b)
    return vlsr - proj


def phase_to_peculiar(ra_deg, dec_deg, plx, pme, pmn, vlsr):
    plx=np.asarray(plx,float); pme=np.asarray(pme,float); pmn=np.asarray(pmn,float); vlsr=np.asarray(vlsr,float)
    dist=(1.0/plx)*u.kpc
    vr=lsr_to_helio(ra_deg,dec_deg,vlsr)*u.km/u.s
    c=SkyCoord(ra=np.broadcast_to(ra_deg,plx.shape)*u.deg,
               dec=np.broadcast_to(dec_deg,plx.shape)*u.deg,
               distance=dist,
               pm_ra_cosdec=pme*u.mas/u.yr,
               pm_dec=pmn*u.mas/u.yr,
               radial_velocity=vr,
               frame='icrs')
    g=c.transform_to(gc_frame())
    x=np.asarray(g.x.to_value(u.kpc)); y=np.asarray(g.y.to_value(u.kpc)); z=np.asarray(g.z.to_value(u.kpc))
    vx=np.asarray(g.v_x.to_value(u.km/u.s)); vy=np.asarray(g.v_y.to_value(u.km/u.s)); vz=np.asarray(g.v_z.to_value(u.km/u.s))
    R=np.sqrt(x*x+y*y)
    # Positive U is radially inward. Positive V is in the direction of Galactic rotation.
    vR_out=(x*vx+y*vy)/R
    vrot=(y*vx-x*vy)/R
    Upec=-vR_out
    Vpec=vrot-urc_theta(R)
    Wpec=vz
    return x,y,z,R,Upec,Vpec,Wpec


def build_maser_sample(df):
    out=[]
    for idx,r in df.iterrows():
        vals=[r.plx_mas,r.e_plx_mas,r.pmE,r.e_pmE,r.pmN,r.e_pmN,r.VLSR,r.e_VLSR]
        if not all(np.isfinite(vals)) or r.plx_mas<=0 or r.e_plx_mas/r.plx_mas>0.20:
            continue
        x,y,z,R,U,V,W=phase_to_peculiar(r.ra_deg,r.dec_deg,
                                        np.array([r.plx_mas]),np.array([r.pmE]),np.array([r.pmN]),np.array([r.VLSR]))
        if R[0] < 4.0:
            continue
        rng=np.random.default_rng(MC_SEED+int(idx))
        p=rng.normal(r.plx_mas,r.e_plx_mas,MC_DRAWS)
        pe=rng.normal(r.pmE,r.e_pmE,MC_DRAWS)
        pn=rng.normal(r.pmN,r.e_pmN,MC_DRAWS)
        vv=rng.normal(r.VLSR,r.e_VLSR,MC_DRAWS)
        good=p>0
        if good.sum()<MC_DRAWS*0.95:
            continue
        xm,ym,zm,Rm,Um,Vm,Wm=phase_to_peculiar(r.ra_deg,r.dec_deg,p[good],pe[good],pn[good],vv[good])
        sU=float(np.std(Um,ddof=1)); sV=float(np.std(Vm,ddof=1)); sW=float(np.std(Wm,ddof=1))
        if max(sU,sV,sW)>20.0:
            continue
        out.append(dict(name=r['name'],arm=r.arm,ra_deg=r.ra_deg,dec_deg=r.dec_deg,
                        plx_mas=r.plx_mas,e_plx_mas=r.e_plx_mas,
                        x_kpc=x[0],y_kpc=y[0],z_kpc=z[0],R_kpc=R[0],
                        U_kms=U[0],V_kms=V[0],W_kms=W[0],
                        e_U_kms=sU,e_V_kms=sV,e_W_kms=sW))
    return pd.DataFrame(out)


def kernel_predict(train, xt, yt, h, comp):
    dx=train.x_kpc.to_numpy()-xt; dy=train.y_kpc.to_numpy()-yt
    d2=dx*dx+dy*dy
    sig=train[f'e_{comp}_kms'].to_numpy()
    base=np.exp(-0.5*d2/(h*h))
    w=base/(sig*sig+SIGMA_INT*SIGMA_INT)
    if not np.any(w>0):
        return np.nan,np.nan,np.nan,np.nan
    val=train[f'{comp}_kms'].to_numpy()
    pred=np.sum(w*val)/np.sum(w)
    neff=(np.sum(w)**2)/np.sum(w*w)
    scatter=np.sqrt(np.sum(w*(val-pred)**2)/np.sum(w))
    nearest=np.sqrt(np.min(d2))
    return pred,neff,scatter,nearest


def choose_bandwidth(train):
    scores=[]
    comps=['U','V','W']
    for h in BANDWIDTHS:
        s=0.0; n=0
        for i in range(len(train)):
            tr=train.drop(train.index[i])
            row=train.iloc[i]
            for comp in comps:
                pred,_,_,_=kernel_predict(tr,row.x_kpc,row.y_kpc,h,comp)
                if np.isfinite(pred):
                    denom=row[f'e_{comp}_kms']**2+SIGMA_INT**2
                    s += (row[f'{comp}_kms']-pred)**2/denom
                    n += 1
        scores.append(dict(h_kpc=float(h),standardized_sse=float(s),n_terms=int(n),mean_standardized_sse=float(s/n)))
    sdf=pd.DataFrame(scores)
    best=float(sdf.loc[sdf.mean_standardized_sse.idxmin(),'h_kpc'])
    return best,sdf


def target_position(l_deg,b_deg,d_kpc):
    c=SkyCoord(l=l_deg*u.deg,b=b_deg*u.deg,distance=d_kpc*u.kpc,frame='galactic').transform_to(gc_frame())
    return float(c.x.to_value(u.kpc)),float(c.y.to_value(u.kpc)),float(c.z.to_value(u.kpc))


def los_basis_coeffs(l_deg,b_deg,d_kpc):
    # Exact finite-difference line-of-sight unit vector in the adopted Galactocentric frame.
    eps=1e-4
    c0=SkyCoord(l=l_deg*u.deg,b=b_deg*u.deg,distance=d_kpc*u.kpc,frame='galactic').transform_to(gc_frame())
    c1=SkyCoord(l=l_deg*u.deg,b=b_deg*u.deg,distance=(d_kpc+eps)*u.kpc,frame='galactic').transform_to(gc_frame())
    p0=np.array([c0.x.to_value(u.kpc),c0.y.to_value(u.kpc),c0.z.to_value(u.kpc)])
    p1=np.array([c1.x.to_value(u.kpc),c1.y.to_value(u.kpc),c1.z.to_value(u.kpc)])
    n=(p1-p0); n=n/np.linalg.norm(n)
    x,y,z=p0; R=np.hypot(x,y)
    eU=np.array([-x/R,-y/R,0.0])
    eV=np.array([y/R,-x/R,0.0])
    eW=np.array([0.0,0.0,1.0])
    return float(n@eU),float(n@eV),float(n@eW)


def bootstrap_los(train,xt,yt,h,cU,cV,cW):
    rng=np.random.default_rng(BOOT_SEED)
    vals=[]
    n=len(train)
    for _ in range(BOOT_DRAWS):
        idx=rng.integers(0,n,n)
        b=train.iloc[idx].reset_index(drop=True)
        U,_,_,_=kernel_predict(b,xt,yt,h,'U')
        V,_,_,_=kernel_predict(b,xt,yt,h,'V')
        W,_,_,_=kernel_predict(b,xt,yt,h,'W')
        vals.append(cU*U+cV*V+cW*W)
    q=np.percentile(vals,[16,50,84])
    return float(q[0]),float(q[1]),float(q[2])


def download_raw():
    if RAW_PATH.exists() and RAW_PATH.stat().st_size>1000:
        return
    req=Request(RAW_URL,headers={'User-Agent':'PGS-BeSSeL-freeze-v1/1.0'})
    with urlopen(req,timeout=120) as r, open(RAW_PATH,'wb') as f:
        f.write(r.read())


def main():
    download_raw()
    raw=parse_reid_table(RAW_PATH)
    sample=build_maser_sample(raw)
    sample.to_csv(OUTDIR/'eligible_masers_peculiar_v1.csv',index=False)

    h,cv=choose_bandwidth(sample)
    cv.to_csv(OUTDIR/'bandwidth_cv_v1.csv',index=False)

    targets=pd.read_csv(TARGET_PATH)
    rows=[]
    for _,t in targets.iterrows():
        xt,yt,zt=target_position(t.l_deg,t.b_deg,t.distance_kpc)
        cU,cV,cW=los_basis_coeffs(t.l_deg,t.b_deg,t.distance_kpc)
        preds={}; neffs={}; scatters={}; nearest=[]
        for comp in ['U','V','W']:
            p,nf,sc,nr=kernel_predict(sample,xt,yt,h,comp)
            preds[comp]=p; neffs[comp]=nf; scatters[comp]=sc; nearest.append(nr)
        dlos=cU*preds['U']+cV*preds['V']+cW*preds['W']
        q16,q50,q84=bootstrap_los(sample,xt,yt,h,cU,cV,cW)
        min_neff=min(neffs.values()); nearest_kpc=min(nearest)
        weak=(min_neff<3.0) or (nearest_kpc>2*h)
        rows.append(dict(target=t.target,arm=t.arm,l_deg=t.l_deg,b_deg=t.b_deg,
                         distance_kpc=t.distance_kpc,x_kpc=xt,y_kpc=yt,z_kpc=zt,
                         h_kpc=h,
                         U_pred_kms=preds['U'],V_pred_kms=preds['V'],W_pred_kms=preds['W'],
                         U_scatter_kms=scatters['U'],V_scatter_kms=scatters['V'],W_scatter_kms=scatters['W'],
                         Neff_U=neffs['U'],Neff_V=neffs['V'],Neff_W=neffs['W'],min_Neff=min_neff,
                         nearest_maser_kpc=nearest_kpc,cU=cU,cV=cV,cW=cW,
                         delta_v_los_stream_pred_kms=dlos,
                         bootstrap_p16_kms=q16,bootstrap_p50_kms=q50,bootstrap_p84_kms=q84,
                         weak_support=weak))
    pred=pd.DataFrame(rows)
    pred.to_csv(OUTDIR/'frozen_bessel_streaming_predictions_v1.csv',index=False)

    summary={
        'protocol':'CONVENTIONAL_BESSEL_STREAMING_FREEZE_V1',
        'raw_catalog_rows':int(len(raw)),
        'eligible_rows':int(len(sample)),
        'selected_bandwidth_kpc':h,
        'bandwidth_candidates_kpc':BANDWIDTHS.tolist(),
        'sigma_intrinsic_kms':SIGMA_INT,
        'mc_draws_per_source':MC_DRAWS,
        'bootstrap_draws':BOOT_DRAWS,
        'guardrail':'No GRB H I velocity or residual was read by this script. Predictions are geometry-only and frozen before outcome comparison.',
        'predictions':pred.to_dict(orient='records')
    }
    (OUTDIR/'freeze_summary_v1.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
