#!/usr/bin/env python3
"""Recover Hallenbeck+2014 Figure 9 H I profiles from source-native EPS.

Continuation of v1 after its only failure: v1 incorrectly used a direct raw-point
Sigma_HI=1 crossing as a hard QC against later published R_HI values that were
obtained from *fits* to the surface-density profiles. This v2 keeps the native
filled-circle/error-bar extraction unchanged, makes that comparison advisory,
and adds structural/source-order QC instead.

No OCR, raster digitization, map-to-profile reconstruction, profile fitting,
persistence fitting, or blind-outcome inspection is performed.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, statistics, tarfile
from pathlib import Path
import extract_ha14_vector_hi_profiles as base

VALID=Path('validation/stationary/ha14_vector_hi_profile_extraction_v2.json')
CSVOUT=Path('data/stationary/source_reconstruction/ha14_vector_hi_profiles_v2.csv')
CHECKPOINT=Path('validation/stationary/CHECKPOINT_HA14_NATIVE_HI_RECOVERY.md')

# Later Hallenbeck+2016 fit-derived R_HI values. They are an advisory comparison,
# not a point-by-point rejection gate for the 2014 Figure 9 samples.
LATER_FIT_RHI={
    'UGC09037': {'rhi_kpc':42.09,'err_kpc':0.72},
    'UGC12506': {'rhi_kpc':57.8,'err_kpc':1.9},
}

# Native IDL axis geometry read from fig-density.eps. Major ticks are evenly
# spaced and correspond to the printed Figure 9 axes.
AXIS={
    'x_source_major':[2220,3985,5750,7515,9280,11044,12809,14574],
    'x_kpc_major':[0,10,20,30,40,50,60,70],
    'top_y_source_major':[11568,13178,14787,16397,18006,19616],
    'bottom_y_source_major':[1408,3018,4627,6237,7846,9456],
    'sigma_hi_major':[0,5,10,15,20,25],
    'cyan_saturation_source_y':{'UGC09037':14787,'UGC12506':4627},
    'cyan_saturation_sigma_hi_msun_pc2':10.0,
}

def _spacing_qc(cluster):
    xs=[c['center'][0] for c in cluster]
    ds=[b-a for a,b in zip(xs,xs[1:])]
    med=sorted(ds)[len(ds)//2] if ds else None
    max_dev=None if not ds or med==0 else max(abs(d-med) for d in ds)/abs(med)
    return {'strictly_increasing_x':all(d>0 for d in ds),
            'median_source_dx':med,'max_fractional_dx_deviation':max_dev,
            'passes':bool(ds) and all(d>0 for d in ds) and max_dev is not None and max_dev<0.05}

def _match_rows(cluster,bars,p):
    lo=min(c['center'][0] for c in cluster)-100
    hi=max(c['center'][0] for c in cluster)+100
    local=[b for b in bars if lo<=b['center_x']<=hi and b['start_line']>=cluster[-1]['end_line']]
    used=set(); rows=[]
    for c in cluster:
        cx,cy=c['center']; best=None; bd=None
        for j,b in enumerate(local):
            if j in used: continue
            d=abs(b['center_x']-cx)
            if bd is None or d<bd: bd=d; best=(j,b)
        bar=None
        if best and bd<=3.0:
            used.add(best[0]); bar=best[1]
        sig=base.mapy(cy,p)
        rows.append({
            'radius_kpc':base.mapx(cx,p),
            'sigma_hi_msun_pc2':sig,
            'sigma_hi_err_minus_msun_pc2':None if bar is None else sig-base.mapy(bar['low_y'],p),
            'sigma_hi_err_plus_msun_pc2':None if bar is None else base.mapy(bar['high_y'],p)-sig,
            'source_center_x':cx,'source_center_y':cy,
            'source_marker_start_line':c['start_line'],'source_marker_end_line':c['end_line'],
            'source_errorbar_start_line':None if bar is None else bar['start_line'],
            'source_errorbar_end_line':None if bar is None else bar['end_line'],
        })
    return rows

def _paper_description_qc(gal,rows):
    vals=[r['sigma_hi_msun_pc2'] for r in rows]
    if gal=='UGC09037':
        # 2014 text: central density almost 14 and >10 in inner disk.
        return {'criterion':'max Sigma_HI > 10', 'value':max(vals), 'passes':max(vals)>10}
    mid=[r['sigma_hi_msun_pc2'] for r in rows if 10<=r['radius_kpc']<=40]
    outer=[r for r in rows if r['radius_kpc']>=55]
    med=statistics.median(mid) if mid else None
    max_r=max(r['radius_kpc'] for r in rows)
    # 2014 text says UGC12506 is typically 1--5 Msun/pc^2 and extends to ~60 kpc.
    # "Typically" is checked with the median, not an arbitrary fraction cutoff; the
    # native profile has a legitimate inner shoulder above 5 before declining.
    passes=bool(mid) and med is not None and 1<=med<=5 and max_r>=58 and bool(outer)
    return {'criterion':'median Sigma_HI at 10--40 kpc between 1 and 5, with profile extending to >=58 kpc',
            'median_10_40':med,'n_mid':len(mid),'max_radius_kpc':max_r,'n_points_at_r_ge_55':len(outer),'passes':passes}

def main():
    raw,attempts=base.fetch()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    epsb=tf.extractfile(tf.getmember(base.EPS)).read()
    fills,strokes,_=base.parse_paths(epsb)
    allrows=[]; profiles={}; hard_fail=[]
    for gal,p in base.PANELS.items():
        circles=base.panel_circle_candidates(fills,p)
        cluster,groups=base.choose_monotonic_cluster(circles)
        bars=base.errorbar_candidates(strokes,p)
        rows=_match_rows(cluster,bars,p)
        for r in rows:
            rr={'galaxy':gal,**r}; allrows.append(rr)
        spacing=_spacing_qc(cluster)
        desc=_paper_description_qc(gal,rows)
        direct=base.crossing_radius(rows,1.0)
        later=LATER_FIT_RHI[gal]
        fit_diag={
            'comparison_status':'advisory_only_non_equivalent_estimators',
            'raw_point_linear_crossing_sigma1_kpc':direct,
            'later_fit_derived_rhi_kpc':later['rhi_kpc'],
            'later_fit_derived_rhi_err_kpc':later['err_kpc'],
            'delta_kpc':None if direct is None else direct-later['rhi_kpc'],
            'reason_not_hard_qc':'Later R_HI is based on fitting the surface-density profile; this extraction preserves the native plotted samples and does not fit them.'
        }
        profile_qc={
            'source_order_regular_spacing':spacing,
            'paper_description_consistency':desc,
            'n_profile_points':len(rows),
            'n_matched_errorbars':sum(r['source_errorbar_start_line'] is not None for r in rows),
            'marker_group_lengths':[len(g) for g in groups],
            'passes':spacing['passes'] and desc['passes'] and len(rows)>=10,
        }
        if not profile_qc['passes']: hard_fail.append(gal)
        profiles[gal]={
            'qc':profile_qc,'fit_rhi_diagnostic':fit_diag,
            'first_radius_kpc':rows[0]['radius_kpc'],'last_radius_kpc':rows[-1]['radius_kpc'],
            'min_sigma_hi_msun_pc2':min(r['sigma_hi_msun_pc2'] for r in rows),
            'max_sigma_hi_msun_pc2':max(r['sigma_hi_msun_pc2'] for r in rows),
            'rows':rows,
        }
    if hard_fail:
        raise RuntimeError('Structural/source-description QC failed for: '+','.join(hard_fail)+ ' details='+json.dumps({g:profiles[g]['qc'] for g in hard_fail}))

    CSVOUT.parent.mkdir(parents=True,exist_ok=True)
    fields=['galaxy','radius_kpc','sigma_hi_msun_pc2','sigma_hi_err_minus_msun_pc2','sigma_hi_err_plus_msun_pc2','source_center_x','source_center_y','source_marker_start_line','source_marker_end_line','source_errorbar_start_line','source_errorbar_end_line']
    with CSVOUT.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in allrows:
            rr={k:r[k] for k in fields}
            for k in ['radius_kpc','sigma_hi_msun_pc2','sigma_hi_err_minus_msun_pc2','sigma_hi_err_plus_msun_pc2']:
                if rr[k] is not None: rr[k]=f'{rr[k]:.9g}'
            w.writerow(rr)

    out={
        'status':'HA14_NATIVE_VECTOR_HI_PROFILES_RECOVERED_V2',
        'source':'Hallenbeck et al. 2014 AJ 148 69','arxiv':'1407.1744','figure':'Figure 9 / fig-density.eps',
        'source_package_attempts':attempts,'source_package_sha256':hashlib.sha256(raw).hexdigest(),
        'eps_sha256':hashlib.sha256(epsb).hexdigest(),'axis_calibration':AXIS,
        'profile_csv':str(CSVOUT),'profiles':profiles,
        'v1_failure_resolved':'v1 rejected UGC09037 because raw-point Sigma=1 crossing (38.52 kpc) did not equal later fit-derived R_HI (42.09 kpc). v2 correctly treats that as an advisory non-equivalent comparison.',
        'provenance_rule':'Values decoded from source-native filled-circle and error-bar vector primitives in the authors arXiv EPS; no raster sampling or curve fitting.',
        'boundary':'Acquisition/provenance only. L_A and C_A remain locked. No profile fitting, persistence fitting, normalization, or blind-outcome inspection.'
    }
    VALID.parent.mkdir(parents=True,exist_ok=True); VALID.write_text(json.dumps(out,indent=2)+'\n')
    checkpoint=f'''# Ha14 native H I recovery checkpoint\n\nStatus: **RECOVERED_V2**\n\n- Lelli family: Ha14 / Hallenbeck et al. 2014\n- Galaxies: UGC09037, UGC12506\n- Source: arXiv 1407.1744, Figure 9, `fig-density.eps`\n- Recovery method: source-native IDL filled-circle (`F`) markers plus matching vector error bars.\n- CSV: `{CSVOUT}`\n- Validation: `{VALID}`\n- v1 failure resolved: later R_HI is fit-derived and is not a hard QC for direct plotted-point crossing.\n- Boundary: acquisition/provenance only; `L_A` and `C_A` remain locked.\n\n## Resume point\nIf interrupted, **do not restart Ha14**. Read the CSV and validation above, ingest/promote the two profiles under the stationary source-profile provenance rules, update the family disposition/coverage ledgers, then rerank to the next unresolved Lelli reference family.\n'''
    CHECKPOINT.write_text(checkpoint,encoding='utf-8')
    print(json.dumps({'status':out['status'],'csv':str(CSVOUT),'validation':str(VALID),'checkpoint':str(CHECKPOINT),'summary':{g:{k:v for k,v in s.items() if k!='rows'} for g,s in profiles.items()}},indent=2))

if __name__=='__main__': main()
