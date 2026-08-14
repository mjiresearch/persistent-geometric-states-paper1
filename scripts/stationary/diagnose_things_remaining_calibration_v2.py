#!/usr/bin/env python3
"""Persist diagnostics from the frozen remaining-calibration THINGS validator.

This wrapper does not alter reconstruction or gate logic. It calls the existing
validator target by target, records any exception text, and always writes a
summary so scientific fail-closed outcomes are not lost to CI control flow.
"""
from __future__ import annotations
import json
from pathlib import Path
import validate_things_remaining_calibration_mom0_v1 as v

OUT=Path('validation/stationary/things_remaining_calibration_mom0_validation_v2_diagnostics.json')

def main():
    meta=json.loads(v.META.read_text())
    results=[]
    for galaxy,filename in v.TARGETS.items():
        try:
            r=v.validate(galaxy,filename,meta)
            results.append({
                'galaxy':galaxy,
                'status':r['status'],
                'n_gates_pass':r.get('n_gates_pass'),
                'all_five_gates_pass':r.get('all_five_gates_pass'),
                'output_json':f'validation/stationary/things_{galaxy.lower()}_mom0_validation_v1.json',
                'output_csv':f'data/stationary/source_reconstruction/things_{galaxy.lower()}_mom0_reconstructed_raw_hi_v1.csv',
            })
        except Exception as exc:
            results.append({
                'galaxy':galaxy,
                'status':'VALIDATION_RUNTIME_FAIL_CLOSED',
                'error_type':type(exc).__name__,
                'error':str(exc),
                'all_five_gates_pass':False,
            })
    payload={
        'status':'THINGS_REMAINING_CALIBRATION_DIAGNOSTICS_PERSISTED',
        'reconstruction_logic':'scripts/stationary/validate_things_remaining_calibration_mom0_v1.py unchanged',
        'results':results,
        'n_full_pass':sum(bool(x.get('all_five_gates_pass')) for x in results),
        'boundary':'Calibration/source-profile diagnostics only; no blind outcomes or persistence quantities evaluated.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))

if __name__=='__main__':
    main()
