#!/usr/bin/env python3
# Public birth-radius ingestion for persistence-history testing.
from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import requests

OUT = Path('data/external/dantas_birth_radii')
OUT.mkdir(parents=True, exist_ok=True)

VIZIER_TSV = ('https://vizier.cds.unistra.fr/viz-bin/asu-tsv?'
              '-source=J/A+A/696/A205/catalog&-out.all=1&-out.max=unlimited')
MINESWEEPER = Path('data/external/sdss/dr20_minesweeper/minesweeper_v1.2.2.parquet')


def load_vizier() -> pd.DataFrame:
    r = requests.get(VIZIER_TSV, timeout=120)
    r.raise_for_status()
    lines = [ln for ln in r.text.splitlines() if not ln.startswith('#')]
    txt = '\n'.join(lines)
    df = pd.read_csv(io.StringIO(txt), sep='\t')
    df.columns = [str(c).strip() for c in df.columns]
    return df


def canonical_id(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    x = x.where(~x.isin(['nan','None','']))
    return x


def main() -> None:
    d = load_vizier()
    d.to_csv(OUT/'dantas_2025_birth_radii_catalog.csv.gz', index=False, compression='gzip')
    try:
        d.to_parquet(OUT/'dantas_2025_birth_radii_catalog.parquet', index=False)
    except Exception:
        pass

    report = {
        'source': 'VizieR J/A+A/696/A205, Dantas et al. 2025',
        'source_url': VIZIER_TSV,
        'rows': int(len(d)),
        'columns': [str(c) for c in d.columns],
        'gaia_id_column': 'GaiaEDR3' if 'GaiaEDR3' in d.columns else None,
        'birth_radius_columns': [c for c in d.columns if 'Rbirth' in c],
    }

    if MINESWEEPER.exists() and 'GaiaEDR3' in d.columns:
        ms = pd.read_parquet(MINESWEEPER)
        if 'source_id' in ms.columns:
            left = d.copy(); right = ms.copy()
            left['_gaia_id'] = canonical_id(left['GaiaEDR3'])
            right['_gaia_id'] = canonical_id(right['source_id'])
            joined = left.merge(right, on='_gaia_id', how='inner', suffixes=('_dantas','_mwm'))
            joined.to_csv(OUT/'dantas_mwm_exact_gaia_crossmatch.csv.gz', index=False, compression='gzip')
            report['mwm_crossmatch'] = {
                'minesweeper_rows': int(len(ms)),
                'exact_gaia_matches': int(len(joined)),
                'unique_dantas_gaia_ids': int(left['_gaia_id'].nunique(dropna=True)),
                'unique_mwm_gaia_ids': int(right['_gaia_id'].nunique(dropna=True)),
            }

            cols = {c.lower(): c for c in d.columns}
            rb = cols.get('rbirth')
            rg_candidates = [c for c in d.columns if c.lower() in {'rg','rguide','rguiding','r_g'} or 'rguid' in c.lower()]
            if rb and rg_candidates:
                rg = rg_candidates[0]
                m = d[[c for c in ['CNAME','GaiaEDR3',rb,rg,'b_Rbirth','B_Rbirth','s_Rbirth'] if c in d.columns]].copy()
                m['migration_delta_r_kpc'] = pd.to_numeric(m[rg], errors='coerce') - pd.to_numeric(m[rb], errors='coerce')
                m.to_csv(OUT/'dantas_migration_standardized.csv', index=False)
                report['standardized_migration'] = {'birth_radius_column': rb, 'present_or_guiding_radius_column': rg}

    (OUT/'ingestion_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
