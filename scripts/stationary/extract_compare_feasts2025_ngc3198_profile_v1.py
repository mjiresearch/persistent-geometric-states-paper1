#!/usr/bin/env python3
"""Extract NGC3198 from the public FEASTS 2025 ECSV and compare to Leroy 2008.

Source-domain diagnostic only. FEASTS 2025 is treated as raw H I (no helium),
consistent with Wang et al. 2025. Leroy Table 7 is converted back to raw H I by
dividing its published gas surface density by 1.36. No persistence outputs are
read and no profile is promoted by this script.
"""
from __future__ import annotations
import csv,json,math
from pathlib import Path
import numpy as np
from astropy.table import Table

FEASTS=Path('data/stationary/source_reconstruction/feasts2025_HIprof_wang25.ecsv')
LEROY=Path('data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv')
OUT=Path('data/stationary/source_reconstruction/feasts2025_ngc3198_hi_profile_raw_v1.csv')
AUDIT=Path('validation/stationary/feasts2025_ngc3198_leroy_overlap_v1.json')

def main():
 tab=Table.read(FEASTS,format='ascii.ecsv')
 rows=tab[np.asarray(tab['name']).astype(str)=='NGC3198']
 if len(rows)!=1:raise RuntimeError(f'expected one NGC3198 row, found {len(rows)}')
 r=rows[0]
 ra=np.asarray(r['radi_arcsec'],dtype=float); rk=np.asarray(r['radi_kpc'],dtype=float); sig=np.asarray(r['SigmaHI_Msunpc2'],dtype=float)
 finite=np.isfinite(ra)&np.isfinite(rk)&np.isfinite(sig)
 ra=ra[finite];rk=rk[finite];sig=sig[finite]
 if len(rk)<3 or np.any(np.diff(rk)<=0):raise RuntimeError('invalid FEASTS radial sequence')
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['galaxy','source','radius_arcsec','radius_kpc_source_distance','sigma_hi_raw_msun_pc2','source_distance_mpc','helium_included'])
  for a,k,s in zip(ra,rk,sig):w.writerow(['NGC3198','Wang+2025 FEASTS HIprof_wang25.ecsv',f'{a:.15g}',f'{k:.15g}',f'{s:.15g}',f'{float(r["Dist"]):.15g}',0])
 lr=[];ls=[]
 with LEROY.open(newline='',encoding='utf-8-sig') as f:
  for x in csv.DictReader(f):
   if x['galaxy']=='NGC3198' and x['source_sigmaHI_including_helium_msun_pc2'].strip():
    lr.append(float(x['source_radius_kpc']));ls.append(float(x['source_sigmaHI_including_helium_msun_pc2'])/1.36)
 lr=np.asarray(lr);ls=np.asarray(ls);order=np.argsort(lr);lr=lr[order];ls=ls[order]
 if len(lr)<3:raise RuntimeError('too few Leroy NGC3198 points')
 overlap=(rk>=lr.min())&(rk<=lr.max())
 pub=np.interp(rk[overlap],lr,ls);rec=sig[overlap];ratio=rec/pub;frac=np.abs(rec-pub)/pub
 samples=[{'radius_kpc':float(a),'feasts2025_raw_hi':float(b),'leroy2008_raw_hi_interp':float(c),'ratio_feasts_over_leroy':float(d),'abs_fractional_difference':float(e)} for a,b,c,d,e in zip(rk[overlap],rec,pub,ratio,frac)]
 result={
  'status':'FEASTS2025_NGC3198_PROFILE_EXTRACTED_AND_COMPARED',
  'source_file':str(FEASTS),'normalized_profile_csv':str(OUT),'source_distance_mpc':float(r['Dist']),
  'helium_included':False,'n_finite_profile_points':int(len(rk)),'radius_kpc_min':float(rk.min()),'radius_kpc_max':float(rk.max()),
  'sigma_hi_min':float(sig.min()),'sigma_hi_max':float(sig.max()),
  'r1_kpc':float(r['r1_kpc']),'r1_kpc_corrected':float(r['r1_kpc_corrected']),'r001_kpc':float(r['r001_kpc']),'r001_kpc_corrected':float(r['r001_kpc_corrected']),
  'leroy_overlap':{'leroy_n_points':int(len(lr)),'leroy_radius_min_kpc':float(lr.min()),'leroy_radius_max_kpc':float(lr.max()),'n_feasts_points_in_overlap':int(overlap.sum()),'median_abs_fractional_difference':float(np.median(frac)),'median_ratio_feasts_over_leroy':float(np.median(ratio)),'inner_to_outer_ratio_drift':float(abs(np.median(ratio[:max(1,len(ratio)//2)])-np.median(ratio[-max(1,len(ratio)//2):]))),'samples':samples},
  'interpretation_boundary':'Source-profile compatibility diagnostic only. No acceptance threshold is introduced here and no profile is promoted by this script.',
  'science_boundary':'No rotation residuals, persistence parameters, L_A, C_A, tau_A, or blind outcomes read.'
 }
 AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','n_finite_profile_points','radius_kpc_min','radius_kpc_max','r1_kpc','r001_kpc')},indent=2));print(json.dumps(result['leroy_overlap'],indent=2))
if __name__=='__main__':main()
