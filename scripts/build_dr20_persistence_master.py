#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import requests
from astropy.table import Table

OUT = Path('data/persistence_history/dr20_master')
OUT.mkdir(parents=True, exist_ok=True)

URLS = {
    'minesweeper': 'https://data.sdss.org/sas/dr20/vac/mwm/minesweeper/minesweeper_v1.2.2.fits',
    'orbits': 'https://data.sdss.org/sas/dr20/vac/mwm/orbits/GravPot16-1.0.0.fits',
    'boss_occam_members': 'https://data.sdss.org/sas/dr20/vac/mwm/boss-occam/BOSS_occam_member-DR20-v1.fits',
    'boss_occam_clusters': 'https://data.sdss.org/sas/dr20/vac/mwm/boss-occam/BOSS_occam_cluster-DR20-v1.fits',
}

ID_CANDIDATES = [
    'source_id','SOURCE_ID','gaia_source_id','GAIA_SOURCE_ID','gaia_dr3_source_id','GAIA_DR3_SOURCE_ID',
    'sdss_id','SDSS_ID','catalogid','CATALOGID','catalog_id','CATALOG_ID','target_id','TARGET_ID'
]

CORE_MS = [
    'source_id','ra','dec','parallax','parallax_error','l','b',
    'Teff','Teff_err','logg','logg_err','Age','Age_lerr','Age_uerr','Age_err',
    'X_gal','X_gal_err','Y_gal','Y_gal_err','Z_gal','Z_gal_err',
    'Vx_gal','Vx_gal_err','Vy_gal','Vy_gal_err','Vz_gal','Vz_gal_err',
    'Lz','Lz_err','ecc_mw22','ecc_mw22_err','R_apo_mw22','R_apo_mw22_err',
    'R_peri_mw22','R_peri_mw22_err','z_max_mw22','z_max_mw22_err',
    'in_sgr_L','in_cluster','cluster'
]

ORBIT_PATTERNS = ('id','source','gaia','sdss','catalog','peri','apo','zmax','lz','ecc','energy','action','jr','jphi','jz','guid','rmean','r_mean')


def download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dest.open('wb') as f:
            for chunk in r.iter_content(1024*1024):
                if chunk:
                    f.write(chunk)


def load_url(url: str, tmpdir: Path, name: str) -> pd.DataFrame:
    p = tmpdir / f'{name}.fits'
    download(url, p)
    return Table.read(p).to_pandas()


def present_ids(df: pd.DataFrame) -> list[str]:
    return [c for c in ID_CANDIDATES if c in df.columns]


def unique_rate(s: pd.Series) -> float:
    x = s.dropna()
    return float(x.nunique()/len(x)) if len(x) else 0.0


def choose_join_key(a: pd.DataFrame, b: pd.DataFrame):
    commons = [c for c in ID_CANDIDATES if c in a.columns and c in b.columns]
    scored = []
    for c in commons:
        sa = a[c].dropna(); sb = b[c].dropna()
        if sa.empty or sb.empty:
            continue
        # normalize integer-like IDs as strings to avoid float coercion
        aa = set(sa.astype(str).tolist())
        bb = set(sb.astype(str).tolist())
        overlap = len(aa & bb)
        scored.append((overlap, min(unique_rate(sa), unique_rate(sb)), c))
    if not scored:
        return None, []
    scored.sort(reverse=True)
    return scored[0][2], scored


def main():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        ms = load_url(URLS['minesweeper'], tmp, 'minesweeper')
        orb = load_url(URLS['orbits'], tmp, 'orbits')
        occ_m = load_url(URLS['boss_occam_members'], tmp, 'boss_occam_members')
        occ_c = load_url(URLS['boss_occam_clusters'], tmp, 'boss_occam_clusters')

    report = {
        'rows': {'minesweeper': len(ms), 'orbits': len(orb), 'boss_occam_members': len(occ_m), 'boss_occam_clusters': len(occ_c)},
        'columns': {
            'minesweeper': list(ms.columns),
            'orbits': list(orb.columns),
            'boss_occam_members': list(occ_m.columns),
            'boss_occam_clusters': list(occ_c.columns),
        },
        'id_columns': {
            'minesweeper': present_ids(ms), 'orbits': present_ids(orb),
            'boss_occam_members': present_ids(occ_m), 'boss_occam_clusters': present_ids(occ_c)
        }
    }

    join_key, scores = choose_join_key(ms, orb)
    report['minesweeper_orbits_join_candidates'] = [
        {'column': c, 'overlap_unique_ids': int(o), 'min_unique_rate': u} for o,u,c in scores
    ]
    report['minesweeper_orbits_join_key'] = join_key

    ms_cols = [c for c in CORE_MS if c in ms.columns]
    if join_key and join_key not in ms_cols:
        ms_cols.insert(0, join_key)
    orb_cols = [c for c in orb.columns if any(p in c.lower() for p in ORBIT_PATTERNS)]
    if join_key and join_key not in orb_cols:
        orb_cols.insert(0, join_key)

    if join_key:
        left = ms[ms_cols].copy()
        right = orb[orb_cols].copy()
        left[join_key] = left[join_key].astype(str)
        right[join_key] = right[join_key].astype(str)
        # enforce one orbital row per identifier only if duplicates exist
        dup_orb = int(right.duplicated(join_key).sum())
        report['orbit_duplicate_join_ids'] = dup_orb
        if dup_orb:
            right = right.drop_duplicates(join_key, keep='first')
        master = left.merge(right, on=join_key, how='left', suffixes=('_ms','_orbit'), indicator=True)
        report['master_rows'] = len(master)
        report['matched_orbit_rows'] = int((master['_merge'] == 'both').sum())
        report['orbit_match_fraction'] = float((master['_merge'] == 'both').mean())
        master.drop(columns=['_merge'], inplace=True)
    else:
        master = ms[ms_cols].copy()
        report['master_rows'] = len(master)
        report['matched_orbit_rows'] = 0
        report['orbit_match_fraction'] = 0.0
        report['warning'] = 'No verified shared identifier between MINESweeper and GravPot16; orbital table not force-joined.'

    # OCCAM is retained as a linked layer unless a verified shared identifier exists.
    occ_key, occ_scores = choose_join_key(master, occ_m)
    report['master_boss_occam_join_candidates'] = [
        {'column': c, 'overlap_unique_ids': int(o), 'min_unique_rate': u} for o,u,c in occ_scores
    ]
    report['master_boss_occam_join_key'] = occ_key
    if occ_key:
        occ = occ_m.copy()
        master[occ_key] = master[occ_key].astype(str)
        occ[occ_key] = occ[occ_key].astype(str)
        occ = occ.drop_duplicates(occ_key, keep='first')
        keep_occ = [occ_key] + [c for c in ['Cluster','RV_Prob','Teff','logg','alpha_M_CLAM','E_alpha_M_CLAM'] if c in occ.columns]
        master = master.merge(occ[keep_occ], on=occ_key, how='left', suffixes=('','_occam'))
        report['boss_occam_matched_rows'] = int(master['Cluster'].notna().sum()) if 'Cluster' in master.columns else 0
    else:
        report['boss_occam_matched_rows'] = 0

    master['sdss_release'] = 'DR20'
    master['history_data_status'] = 'public_observed_plus_orbital_proxies'
    master['email_permission_history_status'] = 'reserved_not_received'

    # Reserved direct-history columns for later permissioned data.
    for c in [
        'birth_radius_kpc','birth_radius_err_kpc','birth_radius_method',
        'migration_delta_r_kpc','migration_probability','migration_class',
        'bar_resonance_flag','spiral_resonance_flag','perturbation_class',
        'accretion_component','accretion_probability','disk_rebuilding_epoch_gyr',
        'source_history_dataset','source_history_permission_id'
    ]:
        if c not in master.columns:
            master[c] = pd.NA

    master.to_parquet(OUT/'dr20_persistence_master.parquet', index=False)
    master.to_csv(OUT/'dr20_persistence_master.csv.gz', index=False, compression='gzip')
    occ_m.to_parquet(OUT/'dr20_boss_occam_members_linked.parquet', index=False)
    occ_c.to_parquet(OUT/'dr20_boss_occam_clusters.parquet', index=False)
    (OUT/'join_report.json').write_text(json.dumps(report, indent=2, default=str))

    # concise README generated from actual join result
    readme = f'''# DR20 persistence master\n\nGenerated reproducibly from public SDSS DR20 VACs.\n\n- MINESweeper rows: {len(ms):,}\n- GravPot16 rows: {len(orb):,}\n- Verified MINESweeper↔orbit join key: `{join_key}`\n- Orbital matches: {report.get('matched_orbit_rows',0):,} / {len(master):,}\n- BOSS OCCAM verified join key: `{occ_key}`\n- BOSS OCCAM matched master rows: {report.get('boss_occam_matched_rows',0):,}\n\nThe master intentionally reserves direct source-history fields (birth radius, migration, bar/spiral interaction, perturbation/accretion and disk rebuilding) for the permissioned email dataset. No positional/fuzzy star matching is used. See `join_report.json` for full schemas and overlap diagnostics.\n'''
    (OUT/'README.md').write_text(readme)
    print(json.dumps({k:v for k,v in report.items() if k not in ('columns',)}, indent=2, default=str))

if __name__ == '__main__':
    main()
