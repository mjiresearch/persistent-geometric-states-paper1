#!/usr/bin/env python3
"""Build pre-fit HI profile provenance manifest for Appendix I.

This does not ingest or synthesize HI profiles. It records acquisition status
for the already-frozen stationary sample before any fit of L_A or C_A.
"""
from __future__ import annotations
import argparse, csv, json, hashlib
from pathlib import Path

KNOWN_UNAVAILABLE_169 = {"D564-8", "D631-7", "NGC4138", "NGC5907"}
FEASTS_VALIDATION = {"NGC2841", "NGC2903", "NGC3198", "NGC3521", "NGC4214", "NGC4559", "NGC5033", "NGC5055"}


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024), b''):
            h.update(c)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--split', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--summary', required=True)
    args=ap.parse_args()
    split=Path(args.split)
    with split.open(newline='', encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    out=[]
    for r in rows:
        g=r['galaxy']
        missing=g in KNOWN_UNAVAILABLE_169
        out.append({
            'galaxy': g,
            'stationary_role': r['stationary_role'],
            'master_sha256': r['master_sha256'],
            'expected_in_169_profile_compilation': '0' if missing else '1',
            'primary_direct_profile_eligible': '0' if missing else '1',
            'primary_profile_acquisition_status': 'known_unavailable_in_169_compilation' if missing else 'available_nonpublic_request_required',
            'public_download_verified': '0',
            'profile_data_ingested': '0',
            'profile_source_class': 'SPARC_azimuthally_averaged_HI_profile_private_compilation' if not missing else 'none_known_from_compilation',
            'independent_FEASTS_validation_overlap': '1' if g in FEASTS_VALIDATION else '0',
            'do_not_substitute_validation_for_primary': '1',
            'notes': ('Known missing from the 169-profile compilation; primary direct-profile analysis excludes unless independently verified direct profile is found pre-fit.' if missing else 'Profile reported available in the 169-galaxy SPARC HI compilation, but no public download verified; acquisition from authors/original literature required before ingestion.')
        })
    fields=list(out[0].keys())
    op=Path(args.out); op.parent.mkdir(parents=True, exist_ok=True)
    with op.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)
    summary={
        'status':'ACQUISITION_PENDING',
        'n_frozen_stationary':len(out),
        'n_primary_direct_profile_eligible':sum(x['primary_direct_profile_eligible']=='1' for x in out),
        'n_known_unavailable':sum(x['primary_direct_profile_eligible']=='0' for x in out),
        'n_calibration_eligible':sum(x['primary_direct_profile_eligible']=='1' and x['stationary_role']=='calibration' for x in out),
        'n_blind_eligible':sum(x['primary_direct_profile_eligible']=='1' and x['stationary_role']=='blind' for x in out),
        'n_public_download_verified':0,
        'n_profiles_ingested':0,
        'n_independent_FEASTS_validation_overlap':sum(x['independent_FEASTS_validation_overlap']=='1' for x in out),
        'split_sha256':sha256(split),
        'provenance_sha256':sha256(op),
        'freeze_boundary':'No L_A, C_A, tau_A, or persistence prediction evaluated.'
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))

if __name__=='__main__':
    main()
