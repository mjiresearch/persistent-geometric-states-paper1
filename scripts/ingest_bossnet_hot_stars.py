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


def main():
    with requests.get(URL,stream=True,timeout=120) as r:
        r.raise_for_status()
        with TMP.open('wb') as f:
            for chunk in r.iter_content(chunk_size=8*1024*1024):
                if chunk: f.write(chunk)
    with fits.open(TMP,memmap=False) as hdul:
        tab=hdul[1].data
        names=list(tab.names)
        t_candidates=[n for n in names if n.lower() in {'teff','t_eff','bossnet_teff'} or ('teff' in n.lower() and 'err' not in n.lower() and not n.lower().startswith('e_'))]
        if not t_candidates: raise RuntimeError(f'No Teff-like column found. Columns: {names}')
        tcol=t_candidates[0]
        teff=np.asarray(tab[tcol],float)
        mask=np.isfinite(teff)&(teff>=10000)&(teff<=60000)
        idx=np.where(mask)[0]
        wanted=[]
        keys=['sdss_id','catalogid','gaia','source','ra','dec','l','b','pmra','pmdec','parallax','v_rad','rv','teff','logg','fe_h','snr','carton','program']
        for n in names:
            nl=n.lower()
            if any(k in nl for k in keys): wanted.append(n)
        wanted=list(dict.fromkeys(wanted))
        out={}
        for n in wanted:
            arr=tab[n][idx]
            if getattr(arr.dtype,'kind',None)=='S': arr=np.char.decode(arr,'utf-8',errors='ignore')
            try: out[n]=arr
            except Exception: pass
        df=pd.DataFrame(out)
    df.to_csv(OUT/'bossnet_hot_stars_selected.csv.gz',index=False,compression='gzip')
    report={
        'source_url':URL,
        'raw_download_bytes':int(TMP.stat().st_size),
        'all_columns':names,
        'teff_column_used':tcol,
        'hot_star_rows_teff_10000_60000':int(len(df)),
        'selected_columns':list(df.columns),
        'has_gaia_id':any('gaia' in c.lower() and ('source' in c.lower() or 'dr3' in c.lower()) for c in df.columns),
        'has_pmra':any('pmra' in c.lower() for c in df.columns),
        'has_pmdec':any('pmdec' in c.lower() for c in df.columns),
        'has_parallax':any('parallax' in c.lower() for c in df.columns),
        'has_rv':any(('v_rad' in c.lower()) or (c.lower()=='rv') or ('radial_velocity' in c.lower()) for c in df.columns),
        'has_ra_dec':any(c.lower()=='ra' for c in df.columns) and any(c.lower()=='dec' for c in df.columns),
    }
    (OUT/'bossnet_hot_star_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
# workflow trigger 2026-08-08
