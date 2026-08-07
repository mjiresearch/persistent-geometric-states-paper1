#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import spearmanr

OUT = Path('data/persistence_history/milky_way_stage3b_mcgaugh')
OUT.mkdir(parents=True, exist_ok=True)
CELLS = Path('data/persistence_history/milky_way_stage2/azimuthal_history_cells.csv')

TABLE2_URL = 'https://cdsarc.cds.unistra.fr/ftp/J/ApJ/885/87/table2.dat'
TABLE3_URL = 'https://cdsarc.cds.unistra.fr/ftp/J/ApJ/885/87/table3.dat'
RNG = np.random.default_rng(20260807)


def download_text(url: str) -> str:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.text


def parse_table2(text: str) -> pd.DataFrame:
    rows=[]
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            rows.append({
                'Rad': float(line[0:8]),
                'Vbulge': float(line[9:17]),
                'Vgas': float(line[18:26]),
                'Vdisk': float(line[27:34]),
                'Vc_model': float(line[35:42]),
                'Sbulge': float(line[43:51]) if line[43:51].strip() else np.nan,
                'Sdisk': float(line[52:58]) if line[52:58].strip() else np.nan,
                'Sgas': float(line[59:65]) if line[59:65].strip() else np.nan,
            })
        except ValueError:
            continue
    d=pd.DataFrame(rows).sort_values('Rad')
    d['Vbar'] = np.sqrt(d['Vbulge']**2 + d['Vgas']**2 + d['Vdisk']**2)
    d['Vnonbar_model_equiv'] = np.sqrt(np.clip(d['Vc_model']**2-d['Vbar']**2,0,None))
    return d


def parse_table3(text: str) -> pd.DataFrame:
    rows=[]
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            rows.append({
                'Rad': float(line[0:5]),
                'dSdR': float(line[6:11]),
                'E_dSdR': float(line[12:15]),
                'e_dSdR': float(line[16:19]),
                'Vcc': float(line[20:26]),
                'E_Vcc': float(line[27:32]),
                'e_Vcc': float(line[33:38]),
            })
        except ValueError:
            continue
    return pd.DataFrame(rows).sort_values('Rad')


def radial_history() -> pd.DataFrame:
    c=pd.read_csv(CELLS)
    hist_cols=['age_median_gyr','old_fraction_gt8','FeH_median','aFe_median',
               'ecc_median','zmax_median_kpc','radial_excursion_median_kpc']
    rows=[]
    for r,g in c.groupby('R_bin_kpc'):
        w=pd.to_numeric(g['n'],errors='coerce').to_numpy(float)
        row={'R_kpc':float(r),'stars_weight':int(np.nansum(w)),'cells':int(len(g))}
        for col in hist_cols:
            x=pd.to_numeric(g[col],errors='coerce').to_numpy(float)
            m=np.isfinite(x)&np.isfinite(w)&(w>0)
            row[col]=float(np.average(x[m],weights=w[m])) if np.any(m) else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values('R_kpc')


def detrend(r,y):
    r=np.asarray(r,float); y=np.asarray(y,float)
    m=np.isfinite(r)&np.isfinite(y)
    out=np.full_like(y,np.nan)
    if m.sum()<5: return out
    coef=np.polyfit(r[m],y[m],2 if m.sum()>=6 else 1)
    out[m]=y[m]-np.polyval(coef,r[m])
    return out


def stats(r,x,y):
    r=np.asarray(r,float); x=np.asarray(x,float); y=np.asarray(y,float)
    m=np.isfinite(r)&np.isfinite(x)&np.isfinite(y)
    r,x,y=r[m],x[m],y[m]
    if len(r)<6: return {'n':int(len(r))}
    rho,p=spearmanr(x,y)
    xd,yd=detrend(r,x),detrend(r,y)
    md=np.isfinite(xd)&np.isfinite(yd)
    rd,pd=spearmanr(xd[md],yd[md])
    order=np.argsort(r)
    rf,pf=spearmanr(np.diff(x[order]),np.diff(y[order])) if len(r)>=6 else (np.nan,np.nan)
    return {'n':int(len(r)),'rho_raw':float(rho),'p_raw':float(p),
            'rho_detrended':float(rd),'p_detrended':float(pd),
            'rho_first_difference':float(rf),'p_first_difference':float(pf)}


def main():
    t2=parse_table2(download_text(TABLE2_URL))
    t3=parse_table3(download_text(TABLE3_URL))
    t2.to_csv(OUT/'mcgaugh2019_table2_mass_model.csv',index=False)
    t3.to_csv(OUT/'mcgaugh2019_table3_rotation_curve.csv',index=False)

    h=radial_history()
    # Primary support domain inherited from Stage 3 robustness screen.
    h=h[(h['R_kpc']>=5.0)&(h['R_kpc']<=10.5)&(h['stars_weight']>=100)&(h['cells']>=5)].copy()
    r=h['R_kpc'].to_numpy(float)

    # Interpolate published pointwise observed curve and baryonic components to exactly
    # the independent DR20 history-bin radii.
    h['Vobs_mcgaugh_kms']=np.interp(r,t3['Rad'],t3['Vcc'])
    h['Vobs_err_hi_kms']=np.interp(r,t3['Rad'],t3['E_Vcc'])
    h['Vobs_err_lo_kms']=np.interp(r,t3['Rad'],t3['e_Vcc'])
    h['Vbar_mcgaugh_kms']=np.interp(r,t2['Rad'],t2['Vbar'])
    h['Vbulge_kms']=np.interp(r,t2['Rad'],t2['Vbulge'])
    h['Vdisk_kms']=np.interp(r,t2['Rad'],t2['Vdisk'])
    h['Vgas_kms']=np.interp(r,t2['Rad'],t2['Vgas'])
    h['Vc_model_mcgaugh_kms']=np.interp(r,t2['Rad'],t2['Vc_model'])
    res2=h['Vobs_mcgaugh_kms']**2-h['Vbar_mcgaugh_kms']**2
    h['Vres2_kms2']=res2
    h['Vres_equiv_kms']=np.sqrt(np.clip(res2,0,None))
    h['mass_discrepancy_fraction_v2']=res2/(h['Vobs_mcgaugh_kms']**2)
    h['gres_kms2_per_kpc']=res2/h['R_kpc']

    hist=['age_median_gyr','old_fraction_gt8','FeH_median','aFe_median',
          'ecc_median','zmax_median_kpc','radial_excursion_median_kpc']
    targets=['Vres_equiv_kms','mass_discrepancy_fraction_v2','gres_kms2_per_kpc']
    cor={hh:{tt:stats(r,h[hh],h[tt]) for tt in targets} for hh in hist}

    # Monte Carlo observational-error propagation for the two simplest history proxies.
    mc={}
    sigma=0.5*(h['Vobs_err_hi_kms'].abs().to_numpy(float)+h['Vobs_err_lo_kms'].abs().to_numpy(float))
    vbar=h['Vbar_mcgaugh_kms'].to_numpy(float)
    vobs=h['Vobs_mcgaugh_kms'].to_numpy(float)
    for hh in ['age_median_gyr','old_fraction_gt8']:
        raw=[]; det=[]
        x=h[hh].to_numpy(float)
        for _ in range(2000):
            vv=RNG.normal(vobs,sigma)
            yy=np.sqrt(np.clip(vv**2-vbar**2,0,None))
            raw.append(spearmanr(x,yy).statistic)
            xd=detrend(r,x); yd=detrend(r,yy); m=np.isfinite(xd)&np.isfinite(yd)
            det.append(spearmanr(xd[m],yd[m]).statistic)
        raw=np.asarray(raw); det=np.asarray(det)
        mc[hh]={
            'rho_raw_median':float(np.nanmedian(raw)),
            'rho_raw_16_84':[float(np.nanpercentile(raw,16)),float(np.nanpercentile(raw,84))],
            'rho_detrended_median':float(np.nanmedian(det)),
            'rho_detrended_16_84':[float(np.nanpercentile(det,16)),float(np.nanpercentile(det,84))],
        }

    h.to_csv(OUT/'mcgaugh_history_residual_join.csv',index=False)
    report={
        'analysis_name':'Milky Way Stage 3B independent McGaugh 2019 baryonic-decomposition cross-check',
        'source_urls':{'mass_model':TABLE2_URL,'rotation_curve':TABLE3_URL},
        'table_rows':{'table2':int(len(t2)),'table3':int(len(t3))},
        'history_bins':int(len(h)),
        'history_R_range_kpc':[float(h.R_kpc.min()),float(h.R_kpc.max())] if len(h) else None,
        'positive_baryonic_deficit_bins':int((h.Vres2_kms2>0).sum()),
        'fraction_positive_baryonic_deficit_bins':float((h.Vres2_kms2>0).mean()) if len(h) else None,
        'correlations':cor,
        'observational_error_monte_carlo':mc,
        'guardrail':('McGaugh 2019 table2 is a published Milky Way mass model with separate bulge, gas and disk circular-speed components; '
                     'table3 is a published circular-speed curve with asymmetric statistical errors. Baryonic-model systematics and shared radial '
                     'gradients remain confounders, so detrended and first-difference correlations are more diagnostic than raw correlations. '
                     'This is an independent cross-check, not a persistence detection.')
    }
    (OUT/'stage3b_summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
