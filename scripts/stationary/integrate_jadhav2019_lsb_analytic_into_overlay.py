#!/usr/bin/env python3
"""Integrate Jadhav & Banerjee 2019 analytic LSB H I profiles into the public-source overlay.

Scientific rules:
- five frozen dB96-family targets have public analytic atomic-HI profiles;
- existing higher-information raw machine-readable profiles, if any, remain preferred;
- no helium factor, frozen-distance change, inclination renormalization, resampling,
  interpolation, or persistence fitting occurs here.
"""
from __future__ import annotations

import csv
from pathlib import Path

OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
SOURCE=Path('data/stationary/source_reconstruction/jadhav_banerjee2019_lsb_hi_analytic_profiles_v1.csv')

FIELDS=[
    'galaxy','stationary_role','public_source_family','acquisition_status',
    'numeric_rows_or_model','source_quantity','helium_status',
    'preferred_public_source','source_artifact','notes',
]
STRONGER={'raw_source_profile_ingested'}


def read(path):
    with path.open(newline='',encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def main():
    overlay_rows=read(OVERLAY)
    if len({r['galaxy'] for r in overlay_rows}) != len(overlay_rows):
        raise RuntimeError('Duplicate galaxy in overlay before Jadhav integration')
    overlay={r['galaxy']:r for r in overlay_rows}

    src=read(SOURCE)
    if len(src)!=5 or len({r['galaxy'] for r in src})!=5:
        raise RuntimeError(f'Expected exactly five unique Jadhav profiles, got {len(src)} rows')

    added=[]; upgraded=[]; retained=[]
    for r in src:
        g=r['galaxy']; role=r['stationary_role']
        existing=overlay.get(g)
        if existing and existing['stationary_role'] != role:
            raise RuntimeError(f'Frozen role mismatch for {g}: {existing["stationary_role"]} vs {role}')
        note=(
            'Jadhav & Banerjee 2019 public analytic atomic-HI profile recovered as the published '
            'off-centred Gaussian / double-Gaussian model with quoted parameter uncertainties. '
            'Parameters retained exactly as published; no helium, distance/inclination renormalization, '
            'or common-grid resampling applied. Underlying LSB HI profile provenance is de Blok literature.'
        )
        if existing and existing['acquisition_status'] in STRONGER:
            if 'Jadhav & Banerjee 2019' not in existing['notes']:
                existing['notes']=existing['notes'].rstrip()+' '+note+' Retained as secondary analytic QC because the existing raw machine-readable source is stronger.'
            retained.append(g)
            continue

        new={
            'galaxy':g,
            'stationary_role':role,
            'public_source_family':'Jadhav & Banerjee 2019 / de Blok LSB HI',
            'acquisition_status':'analytic_profile_recovered',
            'numeric_rows_or_model':'analytic_model',
            'source_quantity':'raw atomic HI surface density',
            'helium_status':'helium not included',
            'preferred_public_source':'1',
            'source_artifact':str(SOURCE),
            'notes':note,
        }
        if existing:
            new['notes'] += (
                f" Supersedes prior overlay status '{existing['acquisition_status']}' for numerical profile availability; "
                f"prior source provenance retained: {existing['public_source_family']} — {existing['notes']}"
            )
            overlay[g]=new; upgraded.append(g)
        else:
            overlay[g]=new; added.append(g)

    rows=[overlay[g] for g in sorted(overlay)]
    with OVERLAY.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)

    print('source profiles',len(src))
    print('added',len(added),added)
    print('upgraded',len(upgraded),upgraded)
    print('stronger retained',len(retained),retained)
    print('overlay total',len(rows))

if __name__=='__main__': main()
