#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import requests
import numpy as np
import pandas as pd
from astropy.io import fits

OUT=Path('data/external/sdss/bossnet_hot_stars')
OUT.mkdir(parents=True,exist_ok=True)
URL='https://data.sdss.org/sas/dr19/spectro/astra/0.6.0/summary/astraAllStarBossNet-0.6.0.fits.gz'
TMP=Path('/tmp/astraAllStarBossNet-0.6.0.fits.gz')

PHASESPACE_COLUMNS=[
    'sdss_id','gaia_dr3_source_id','catalogid','ra','dec','l','b',
    'plx','e_plx','pmra','e_pmra','pmde','e_pmde',
    'r_med_geo','r_lo_geo','r_hi_geo','r_med_photogeo','r_lo_photogeo','r_hi_photogeo',
    'bailer_jones_flags','gaia_v_rad','gaia_e_v_rad','v_rad','e_v_rad','std_v_rad','n_good_rvs',
    'teff','e_teff','logg','e_logg','fe_h','e_fe_h','snr','flag_warn','flag_bad','result_flags'
]


def main():
    with requests.get(URL,stream=True,timeout=120) as r:
        r.raise_for_status()
        with TMP.open('wb') as f:
            for chunk in r.iter_content(chunk_size=8*1024*1024):
                if chunk: f.write(chunk)
    with fits.open(TMP,memmap=False) as hdul:
        tab=hdul[1].data
        names=list(tab.names)
        if 'teff' not in names:
            raise RuntimeError('BOSSNet teff column not present')
        teff=np.asarray(tab['teff'],float)
        mask=np.isfinite(teff)&(teff>=10000)&(teff<=60000)
        idx=np.where(mask)[0]
        out={}
        missing=[]
        for n in PHASESPACE_COLUMNS:
            if n not in names:
                missing.append(n); continue
            arr=np.asarray(tab[n][idx])
            if arr.ndim != 1: continue
            if getattr(arr.dtype,'kind',None)=='S': arr=np.char.decode(arr,'utf-8',errors='ignore')
            out[n]=arr
        df=pd.DataFrame(out)
    df.to_csv(OUT/'bossnet_hot_stars_selected.csv.gz',index=False,compression='gzip')
    report={
        'source_url':URL,
        'raw_download_bytes':int(TMP.stat().st_size),
        'teff_column_used':'teff',
        'hot_star_rows_teff_10000_60000':int(len(df)),
        'selected_columns':list(df.columns),
        'missing_requested_columns':missing,
        'phase_space_ready_columns':{
            'gaia_id':'gaia_dr3_source_id' in df.columns,
            'ra_dec':all(c in df.columns for c in ['ra','dec']),
            'pm':all(c in df.columns for c in ['pmra','pmde']),
            'parallax':'plx' in df.columns,
            'photogeometric_distance':'r_med_photogeo' in df.columns,
            'geometric_distance':'r_med_geo' in df.columns,
            'boss_rv':'v_rad' in df.columns,
            'gaia_rv':'gaia_v_rad' in df.columns,
        },
        'finite_counts':{c:int(np.isfinite(pd.to_numeric(df[c],errors='coerce')).sum()) for c in ['teff','ra','dec','pmra','pmde','plx','r_med_photogeo','v_rad'] if c in df.columns}
    }
    (OUT/'bossnet_hot_star_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
