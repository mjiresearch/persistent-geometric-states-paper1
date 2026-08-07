#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path('data/persistence_history/dr20_crosswalk_audit')
OUT.mkdir(parents=True, exist_ok=True)

MS = Path('data/external/sdss/dr20_minesweeper/minesweeper_v1.2.2.parquet')
ORB = Path('data/external/sdss/dr20_orbits/GravPot16-1.0.0_persistence_selected.parquet')
ORB_ALT = Path('data/external/sdss/dr20_orbits/GravPot16-1.0.0.parquet')
BOSS = Path('data/external/sdss/dr20_boss_occam/BOSS_occam_member-DR20-v1.parquet')


def canon(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors='coerce')
    out = pd.Series(pd.NA, index=s.index, dtype='string')
    m = x.notna()
    if m.any():
        # IDs fit in signed int64 for Gaia DR3 / SDSS-V IDs used here.
        out.loc[m] = x.loc[m].astype('int64').astype(str)
    # Fallback for genuinely non-numeric IDs.
    mn = ~m & s.notna()
    if mn.any():
        out.loc[mn] = s.loc[mn].astype(str).str.strip()
    return out


def overlap(a: pd.Series, b: pd.Series) -> dict:
    aa = canon(a).dropna().unique()
    bb = canon(b).dropna().unique()
    inter = np.intersect1d(aa, bb)
    return {
        'a_unique': int(len(aa)),
        'b_unique': int(len(bb)),
        'overlap_unique': int(len(inter)),
        'a_match_fraction': float(len(inter) / len(aa)) if len(aa) else 0.0,
        'b_match_fraction': float(len(inter) / len(bb)) if len(bb) else 0.0,
        'sample_overlap_ids': inter[:10].tolist(),
    }


def describe_ids(s: pd.Series) -> dict:
    x = pd.to_numeric(s, errors='coerce').dropna()
    return {
        'dtype': str(s.dtype),
        'non_null': int(s.notna().sum()),
        'unique': int(s.nunique(dropna=True)),
        'numeric_min': str(int(x.min())) if len(x) else None,
        'numeric_max': str(int(x.max())) if len(x) else None,
        'sample': canon(s).dropna().head(10).tolist(),
    }


def main():
    ms = pd.read_parquet(MS)
    orb_path = ORB if ORB.exists() else ORB_ALT
    orb = pd.read_parquet(orb_path)
    boss = pd.read_parquet(BOSS)

    report = {
        'files': {'minesweeper': str(MS), 'orbits': str(orb_path), 'boss_occam': str(BOSS)},
        'row_counts': {'minesweeper': len(ms), 'orbits': len(orb), 'boss_occam': len(boss)},
        'identifier_descriptions': {},
        'pairwise_overlap': {},
    }

    for c in ['source_id', 'sdssid', 'catalogid']:
        if c in ms.columns:
            report['identifier_descriptions'][f'minesweeper.{c}'] = describe_ids(ms[c])
    if 'Ids' in orb.columns:
        report['identifier_descriptions']['orbits.Ids'] = describe_ids(orb['Ids'])
    for c in ['GaiaDR3_ID', 'SDSS_ID']:
        if c in boss.columns:
            report['identifier_descriptions'][f'boss_occam.{c}'] = describe_ids(boss[c])

    pairs = [
        ('minesweeper.source_id', ms.get('source_id'), 'orbits.Ids', orb.get('Ids')),
        ('minesweeper.sdssid', ms.get('sdssid'), 'orbits.Ids', orb.get('Ids')),
        ('minesweeper.catalogid', ms.get('catalogid'), 'orbits.Ids', orb.get('Ids')),
        ('minesweeper.source_id', ms.get('source_id'), 'boss_occam.GaiaDR3_ID', boss.get('GaiaDR3_ID')),
        ('minesweeper.sdssid', ms.get('sdssid'), 'boss_occam.SDSS_ID', boss.get('SDSS_ID')),
        ('minesweeper.catalogid', ms.get('catalogid'), 'boss_occam.SDSS_ID', boss.get('SDSS_ID')),
        ('orbits.Ids', orb.get('Ids'), 'boss_occam.GaiaDR3_ID', boss.get('GaiaDR3_ID')),
        ('orbits.Ids', orb.get('Ids'), 'boss_occam.SDSS_ID', boss.get('SDSS_ID')),
    ]
    for an, a, bn, b in pairs:
        if a is None or b is None:
            continue
        report['pairwise_overlap'][f'{an}__TO__{bn}'] = overlap(a, b)

    # Pick strongest exact crosswalk for each target.
    orb_candidates = {k:v for k,v in report['pairwise_overlap'].items() if k.endswith('__TO__orbits.Ids')}
    boss_candidates = {k:v for k,v in report['pairwise_overlap'].items() if k.startswith('minesweeper.') and '__TO__boss_occam.' in k}
    if orb_candidates:
        report['best_minesweeper_orbits_crosswalk'] = max(orb_candidates.items(), key=lambda kv: kv[1]['overlap_unique'])
    if boss_candidates:
        report['best_minesweeper_boss_occam_crosswalk'] = max(boss_candidates.items(), key=lambda kv: kv[1]['overlap_unique'])

    (OUT/'crosswalk_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
