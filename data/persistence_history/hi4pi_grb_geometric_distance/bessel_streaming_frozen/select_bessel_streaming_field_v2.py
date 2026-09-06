#!/usr/bin/env python3
"""Select support-qualified BeSSeL streaming field V2 using geometry only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

from build_bessel_streaming_field_v1 import (
    ROOT, TARGET_PATH, OUTDIR, BANDWIDTHS,
    kernel_predict, target_position, los_basis_coeffs, bootstrap_los,
)

V2DIR = ROOT / 'outputs_v2'
V2DIR.mkdir(parents=True, exist_ok=True)


def support_at_target(sample, t, h):
    xt,yt,zt=target_position(t.l_deg,t.b_deg,t.distance_kpc)
    neffs=[]; nearest=[]
    for comp in ['U','V','W']:
        _,nf,_,nr=kernel_predict(sample,xt,yt,h,comp)
        neffs.append(float(nf)); nearest.append(float(nr))
    return {
        'target':t.target,'arm':t.arm,'h_kpc':float(h),
        'min_Neff':float(min(neffs)),'nearest_maser_kpc':float(min(nearest)),
        'support_qualified':bool(min(neffs)>=3.0 and min(nearest)<=2.0*h)
    }


def main():
    sample=pd.read_csv(OUTDIR/'eligible_masers_peculiar_v1.csv')
    cv=pd.read_csv(OUTDIR/'bandwidth_cv_v1.csv')
    targets=pd.read_csv(TARGET_PATH)

    support=[]
    for h in BANDWIDTHS:
        for _,t in targets.iterrows():
            support.append(support_at_target(sample,t,float(h)))
    sdf=pd.DataFrame(support)
    sdf.to_csv(V2DIR/'target_support_by_bandwidth_v2.csv',index=False)

    ok=[]
    for h in BANDWIDTHS:
        sub=sdf[sdf.h_kpc==h]
        if len(sub)==len(targets) and bool(sub.support_qualified.all()):
            score=float(cv.loc[np.isclose(cv.h_kpc,h),'mean_standardized_sse'].iloc[0])
            ok.append((score,float(h)))

    if not ok:
        summary={
            'protocol':'CONVENTIONAL_BESSEL_STREAMING_FREEZE_V2',
            'status':'NO_PREDICTION',
            'reason':'No frozen candidate bandwidth satisfies the support rule at all four target geometries.',
            'eligible_masers':int(len(sample)),
        }
        (V2DIR/'freeze_summary_v2.json').write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary,indent=2))
        return

    ok.sort()
    h=ok[0][1]
    rows=[]
    for _,t in targets.iterrows():
        xt,yt,zt=target_position(t.l_deg,t.b_deg,t.distance_kpc)
        cU,cV,cW=los_basis_coeffs(t.l_deg,t.b_deg,t.distance_kpc)
        preds={}; neffs={}; scat={}; nearest=[]
        for comp in ['U','V','W']:
            p,nf,sc,nr=kernel_predict(sample,xt,yt,h,comp)
            preds[comp]=p; neffs[comp]=nf; scat[comp]=sc; nearest.append(nr)
        dlos=cU*preds['U']+cV*preds['V']+cW*preds['W']
        q16,q50,q84=bootstrap_los(sample,xt,yt,h,cU,cV,cW)
        rows.append(dict(
            target=t.target,arm=t.arm,l_deg=t.l_deg,b_deg=t.b_deg,distance_kpc=t.distance_kpc,
            x_kpc=xt,y_kpc=yt,z_kpc=zt,h_kpc=h,
            U_pred_kms=preds['U'],V_pred_kms=preds['V'],W_pred_kms=preds['W'],
            U_scatter_kms=scat['U'],V_scatter_kms=scat['V'],W_scatter_kms=scat['W'],
            Neff_U=neffs['U'],Neff_V=neffs['V'],Neff_W=neffs['W'],min_Neff=min(neffs.values()),
            nearest_maser_kpc=min(nearest),cU=cU,cV=cV,cW=cW,
            delta_v_los_stream_pred_kms=dlos,
            bootstrap_p16_kms=q16,bootstrap_p50_kms=q50,bootstrap_p84_kms=q84,
            support_qualified=True
        ))
    pred=pd.DataFrame(rows)
    pred.to_csv(V2DIR/'frozen_bessel_streaming_predictions_v2.csv',index=False)
    summary={
        'protocol':'CONVENTIONAL_BESSEL_STREAMING_FREEZE_V2',
        'status':'FROZEN_SUPPORT_QUALIFIED',
        'eligible_masers':int(len(sample)),
        'selected_bandwidth_kpc':h,
        'selection_rule':'minimum V1 LOOCV error among bandwidths satisfying all-target min Neff>=3 and nearest<=2h',
        'guardrail':'No GRB H I velocity, residual, or persistence prediction was read.',
        'predictions':pred.to_dict(orient='records')
    }
    (V2DIR/'freeze_summary_v2.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
