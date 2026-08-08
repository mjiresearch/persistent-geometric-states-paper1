#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

OUT = Path('data/external/galactic_acceleration/donlon2025_v3')
OUT.mkdir(parents=True, exist_ok=True)
URL = 'https://raw.githubusercontent.com/thomasdonlon/Empirical_Model_MSP_Spindown_Accels/main/v3/data.csv'
RAW = Path('/tmp/donlon2025_v3_data.csv')
YEAR_S = 365.25 * 86400.0
MM_S_PER_YR_TO_1E10_MS2 = (1e-3 / YEAR_S) / 1e-10
R_SUN_KPC = 8.210
Z_SUN_KPC = 0.0

NUMERIC = [
    'GL','GB','PX','PX_ERR','DIST','DIST_ERR','PMTOT','PMTOT_ERR',
    'PS','PS_ERR','PSDOT_OBS','PSDOT_OBS_ERR','PSDOT_SHK','PSDOT_SHK_ERR',
    'PSDOT_B','PSDOT_B_ERR','MODEL_PSDOT_B','MODEL_PSDOT_B_ERR','ALOS_PS','ALOS_PS_ERR',
    'PB','PB_ERR','PBDOT','PBDOT_ERR','PBDOT_SHK','PBDOT_SHK_ERR','PBDOT_GR','PBDOT_GR_ERR',
    'ALOS_PB','ALOS_PB_ERR','BSURF','BSURF_ERR','CHAR_AGE','CHAR_AGE_ERR'
]


def download():
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    RAW.write_bytes(r.content)


def main():
    download()
    # Row 2 of the public file contains units, not a source.
    d = pd.read_csv(RAW, skiprows=[1])
    for c in NUMERIC:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors='coerce')
    d['NAME'] = d['NAME'].astype(str).str.strip()
    d = d[d['NAME'].ne('') & d['NAME'].ne('nan')].copy()

    pb_ok = np.isfinite(d['ALOS_PB']) & np.isfinite(d['ALOS_PB_ERR']) & (d['ALOS_PB_ERR'] > 0)
    ps_ok = np.isfinite(d['ALOS_PS']) & np.isfinite(d['ALOS_PS_ERR']) & (d['ALOS_PS_ERR'] > 0)
    d['has_binary_orbital_accel'] = pb_ok.astype(int)
    d['has_spin_inferred_accel'] = ps_ok.astype(int)
    d['accel_source'] = np.where(pb_ok, 'binary_orbital', np.where(ps_ok, 'spin_inferred', 'none'))
    d['ALOS_USE_mm_s_yr'] = np.where(pb_ok, d['ALOS_PB'], d['ALOS_PS'])
    d['ALOS_USE_ERR_mm_s_yr'] = np.where(pb_ok, d['ALOS_PB_ERR'], d['ALOS_PS_ERR'])
    d['aGal_1e10_m_s2'] = d['ALOS_USE_mm_s_yr'] * MM_S_PER_YR_TO_1E10_MS2
    d['aGal_err_1e10_m_s2'] = d['ALOS_USE_ERR_mm_s_yr'] * MM_S_PER_YR_TO_1E10_MS2

    # Construct the same physical axes used in Stage 6A from Galactic l,b and the curated DIST.
    # Moran-like axes: +x away from GC, +y toward l=90 deg, +z north.
    l = np.deg2rad(d['GL'].to_numpy(float))
    b = np.deg2rad(d['GB'].to_numpy(float))
    dist = d['DIST'].to_numpy(float)
    cb = np.cos(b)
    dx_toward_gc = dist * cb * np.cos(l)
    dy_l90 = dist * cb * np.sin(l)
    dz_north = dist * np.sin(b)
    d['x_moranlike_kpc'] = R_SUN_KPC - dx_toward_gc
    d['y_moranlike_kpc'] = dy_l90
    d['z_moranlike_kpc'] = Z_SUN_KPC + dz_north
    # Fixed MWM/Astropy mapping from the Stage 6 coordinate audit.
    d['X_mwm_kpc'] = -d['x_moranlike_kpc']
    d['Y_mwm_kpc'] = d['y_moranlike_kpc']
    d['Z_mwm_kpc'] = d['z_moranlike_kpc']
    d['R_gal_kpc'] = np.hypot(d['X_mwm_kpc'], d['Y_mwm_kpc'])
    d['phi_mwm_deg'] = (np.degrees(np.arctan2(d['Y_mwm_kpc'], d['X_mwm_kpc'])) + 360.0) % 360.0

    usable = d[np.isfinite(d['aGal_1e10_m_s2']) & np.isfinite(d['aGal_err_1e10_m_s2']) &
               np.isfinite(d['DIST']) & np.isfinite(d['GL']) & np.isfinite(d['GB'])].copy()

    # Identify exact duplicate sky locations (e.g. two pulsars in the same physical binary system).
    usable['sky_key'] = usable['GL'].round(6).astype(str) + '|' + usable['GB'].round(6).astype(str) + '|' + usable['DIST'].round(6).astype(str)
    sky_counts = usable.groupby('sky_key').size()
    duplicate_keys = set(sky_counts[sky_counts > 1].index)
    usable['duplicate_sky_location'] = usable['sky_key'].isin(duplicate_keys).astype(int)

    cols = [
        'NAME','GL','GB','DIST','DIST_ERR','PX','PX_ERR',
        'accel_source','has_binary_orbital_accel','has_spin_inferred_accel',
        'ALOS_PB','ALOS_PB_ERR','ALOS_PS','ALOS_PS_ERR','ALOS_USE_mm_s_yr','ALOS_USE_ERR_mm_s_yr',
        'aGal_1e10_m_s2','aGal_err_1e10_m_s2',
        'x_moranlike_kpc','y_moranlike_kpc','z_moranlike_kpc',
        'X_mwm_kpc','Y_mwm_kpc','Z_mwm_kpc','R_gal_kpc','phi_mwm_deg',
        'duplicate_sky_location','sky_key','BSURF','CHAR_AGE'
    ]
    usable[cols].to_csv(OUT/'donlon2025_v3_accelerations_normalized.csv', index=False)
    d.to_csv(OUT/'donlon2025_v3_full.csv.gz', index=False, compression='gzip')

    report = {
        'source_url': URL,
        'source_repository': 'thomasdonlon/Empirical_Model_MSP_Spindown_Accels',
        'source_version': 'v3 (published-paper final dataset per authors README)',
        'raw_rows_after_units_removed': int(len(d)),
        'usable_acceleration_rows': int(len(usable)),
        'unique_names': int(usable['NAME'].nunique()),
        'binary_orbital_rows': int((usable['accel_source'] == 'binary_orbital').sum()),
        'spin_inferred_only_rows': int((usable['accel_source'] == 'spin_inferred').sum()),
        'rows_with_both_pb_and_ps_available': int(((usable['has_binary_orbital_accel'] == 1) & (usable['has_spin_inferred_accel'] == 1)).sum()),
        'rows_with_duplicate_sky_location': int(usable['duplicate_sky_location'].sum()),
        'duplicate_sky_groups': int(len(duplicate_keys)),
        'duplicate_names': usable.loc[usable['duplicate_sky_location'] == 1, 'NAME'].tolist(),
        'conversion_mm_s_per_yr_to_1e10_m_s2': float(MM_S_PER_YR_TO_1E10_MS2),
        'acceleration_selection_rule': 'Use ALOS_PB whenever finite with finite positive error; otherwise use ALOS_PS, following the authors README recommendation to prefer binary orbital acceleration when available.',
        'coordinate_rule': {
            'R_sun_kpc': R_SUN_KPC,
            'z_sun_kpc': Z_SUN_KPC,
            'moranlike_axes': '+x away from GC, +y toward Galactic l=90 deg, +z north',
            'mwm_mapping': 'X=-x_moranlike, Y=+y_moranlike, Z=+z_moranlike'
        },
        'guardrail': 'ALOS_PB is the direct binary-orbital timing acceleration channel. ALOS_PS is an empirically inferred acceleration using the published magnetic-braking model and is analyzed separately in Stage 6C rather than treated as equally direct.'
    }
    (OUT/'ingest_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
