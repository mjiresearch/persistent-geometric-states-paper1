#!/usr/bin/env python3
"""Run DDO154 THINGS MOM0 validation with original Walter+2008 survey metadata.

This wrapper reuses the audited v1 reconstruction implementation, changing only
source-metadata constants/provenance before execution. Calibration/source-domain
validation only; no rotation residuals, persistence parameters, or blind outcomes.
"""
from __future__ import annotations
import json
from pathlib import Path
import validate_things_ddo154_mom0_profile_v1 as v

# Original THINGS survey metadata (Walter et al. 2008 source tables).
v.D_MPC=4.3
v.INC_DEG=66.0
v.PA_DEG=230.0
v.CENTER_RA_DEG=15.0*(12.0+54.0/60.0+5.9/3600.0)
v.CENTER_DEC_DEG=27.0+9.0/60.0+10.0/3600.0
v.BMAJ_ARCSEC=14.09
v.BMIN_ARCSEC=12.62
v.PUBLISHED_FLUX_JY_KMS=82.1
v.OUTCSV=Path('data/stationary/source_reconstruction/things_ddo154_mom0_reconstructed_raw_hi_v2.csv')
v.OUTJSON=Path('validation/stationary/things_ddo154_mom0_validation_v2.json')


def main():
    exit_code=0
    try:
        v.main()
    except SystemExit as e:
        exit_code=int(e.code or 0)
    if not v.OUTJSON.exists():
        raise RuntimeError('v1 reconstruction did not emit validation JSON')
    result=json.loads(v.OUTJSON.read_text())
    result['validation_version']='v2_original_things_metadata'
    result['mask_policy']='validation/stationary/THINGS_MOM0_ZERO_BLANK_POLICY_V1.md'
    result['beam']['source']='Walter et al. 2008 THINGS observational table, natural weighting: 14.09 x 12.62 arcsec'
    result['gates']['global_hi_flux']['published_source']='Walter et al. 2008 THINGS Table 5, column S_HI (THINGS integrated flux)'
    result['geometry']['source']='Walter et al. 2008 THINGS source table'
    result['boundary']='Calibration/source-profile validation only. Original THINGS metadata used; no rotation velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcomes evaluated.'
    v.OUTJSON.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if exit_code:
        raise SystemExit(exit_code)

if __name__=='__main__':main()
