#!/usr/bin/env python3
"""Freeze the UGC4483 whole-galaxy H I profile from committed native-vector audits.

No source re-download is required here. This consumes the already committed
Fig6 procedure inventory and axis-label audit, selects the monotonic CircleF
run (whole-galaxy dots), excludes the legend call, and converts source
coordinates using the printed native axes.
"""
from pathlib import Path
import csv, json, math

INV=Path('validation/stationary/lelli2012b_ugc4483_fig6_vector_procedure_inventory_v1.json')
AX=Path('validation/stationary/ugc4483_fig6_axis_labels_v1.json')
OUT=Path('data/stationary/source_reconstruction/lelli2012b_ugc4483_hi_profile_v1.csv')
VAL=Path('validation/stationary/lelli2012b_ugc4483_hi_profile_recovery_v1.json')
CP=Path('validation/stationary/CHECKPOINT_UGC4483_HI_PROFILE_RECOVERED.md')

def fit(pairs):
    xs=[p[0] for p in pairs]; ys=[p[1] for p in pairs]
    xm=sum(xs)/len(xs); ym=sum(ys)/len(ys)
    b=sum((x-xm)*(y-ym) for x,y in pairs)/sum((x-xm)**2 for x in xs)
    return ym-b*xm,b

def invmap(source,a,b): return (source-a)/b

inv=json.loads(INV.read_text()); ax=json.loads(AX.read_text())
assert inv['status']=='LELLI2012B_UGC4483_FIG6_VECTOR_PROCEDURE_INVENTORY_COMPLETE'
assert ax['status']=='UGC4483_FIG6_AXIS_CONTEXT_EXTRACTED'
assert inv['fig6_sha256']==ax['fig6_sha256']=='335c2befde39ba7b6d61c5129215dd97247a781c86a5d472240a9df4ce35ff7e'

circle=next(x for x in inv['procedure_invocation_summaries'] if x['name']=='CircleF')
calls=circle['first_40_invocations']
run=[]
for p in calls:
    if not run or p['x']>run[-1]['x']: run.append(p)
    else: break
assert len(calls)==11 and len(run)==10
legend=[p for p in calls if p not in run]
assert len(legend)==1 and legend[0]['x']<run[-1]['x']

labels=ax['numeric_labels']
xk=[]; xa=[]; yl=[]
for z in labels:
    a=z.get('anchor');
    if not a or len(z['values'])!=1: continue
    v=float(z['values'][0])
    if a['y']==396 and 0<=v<=1.4: xk.append((v,a['x']))
    if a['y']==4680 and 0<=v<=80: xa.append((v,a['x']))
    if a['x']==774 and v in (5.0,10.0): yl.append((v,a['y']))
assert len(xk)==8 and len(xa)==5 and len(yl)==2
xk_a,xk_b=fit(xk); xa_a,xa_b=fit(xa); y_a,y_b=fit(yl)

rows=[]
for i,p in enumerate(run):
    r=invmap(p['x'],xk_a,xk_b)
    arc=invmap(p['x'],xa_a,xa_b)
    sig=invmap(p['y'],y_a,y_b)
    model=10.5*math.exp(-(r*r)/(2*0.580*0.580))
    rows.append({'galaxy':'UGC04483','source_name':'UGC4483','radius_kpc':r,'radius_arcsec':arc,
                 'sigma_hi_msun_pc2':sig,'source_x':p['x'],'source_y':p['y'],'source_line':p['line'],
                 'published_gaussian_sigma_hi_msun_pc2':model,'gaussian_residual_msun_pc2':sig-model})

# Hard QC is structural/cross-axis only. The published Gaussian is advisory.
sp=[rows[i+1]['source_x']-rows[i]['source_x'] for i in range(len(rows)-1)]
arc_res=[rows[i]['radius_arcsec']-(5+10*i) for i in range(len(rows))]
hard={
 'n_whole_galaxy_points':len(rows),
 'circle_calls_total_including_legend':len(calls),
 'legend_calls_excluded':len(legend),
 'strictly_increasing_radius':all(rows[i+1]['radius_kpc']>rows[i]['radius_kpc'] for i in range(len(rows)-1)),
 'source_x_step_min':min(sp),'source_x_step_max':max(sp),
 'max_abs_arcsec_center_residual':max(abs(x) for x in arc_res),
 'passes':len(rows)==10 and min(sp)>=539 and max(sp)<=540 and max(abs(x) for x in arc_res)<0.11
}
assert hard['passes']
res=[r['gaussian_residual_msun_pc2'] for r in rows]
advisory={'published_model':'Sigma_HI(R)=10.5 exp[-R^2/(2*(0.580 kpc)^2)]',
          'rmse_msun_pc2':math.sqrt(sum(x*x for x in res)/len(res)),
          'mae_msun_pc2':sum(abs(x) for x in res)/len(res),
          'status':'advisory_only_not_used_to_modify_native_points'}

OUT.parent.mkdir(parents=True,exist_ok=True)
fields=list(rows[0])
with OUT.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for r in rows:
        q=r.copy()
        for k in ('radius_kpc','radius_arcsec','sigma_hi_msun_pc2','published_gaussian_sigma_hi_msun_pc2','gaussian_residual_msun_pc2'):
            q[k]=f'{q[k]:.9g}'
        w.writerow(q)

val={'status':'UGC4483_NATIVE_VECTOR_HI_PROFILE_RECOVERED','galaxy_frozen_name':'UGC04483','source_name':'UGC4483',
     'source':'Lelli et al. 2012b, A&A 544 A145','arxiv':'1207.2696','figure':'Figure 6 / Fig6.eps',
     'fig6_sha256':inv['fig6_sha256'],'profile_csv':str(OUT),
     'series_identification':'Figure caption says entire galaxy = dots; gnuplot CircleF has 10 monotonic radial calls plus one non-monotonic legend call.',
     'axis_calibration':{'radius_kpc_source_x_intercept':xk_a,'source_units_per_kpc':xk_b,
                         'radius_arcsec_source_x_intercept':xa_a,'source_units_per_arcsec':xa_b,
                         'sigma_hi_source_y_intercept':y_a,'source_units_per_msun_pc2':y_b,
                         'bottom_axis_ticks':xk,'top_axis_ticks':xa,'left_axis_ticks':yl},
     'hard_qc':hard,'published_gaussian_crosscheck':advisory,
     'profile_summary':{'n_rows':len(rows),'radius_kpc_min':rows[0]['radius_kpc'],'radius_kpc_max':rows[-1]['radius_kpc'],
                        'sigma_hi_min':min(r['sigma_hi_msun_pc2'] for r in rows),'sigma_hi_max':max(r['sigma_hi_msun_pc2'] for r in rows)},
     'helium_status':'not applied; Figure 6 is H I surface density. Paper applies factor 1.32 only downstream in gas mass model.',
     'boundary':'Acquisition/provenance only. No raster digitization, source-map reconstruction, profile fitting, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
VAL.parent.mkdir(parents=True,exist_ok=True);VAL.write_text(json.dumps(val,indent=2)+'\n')
CP.write_text('# UGC4483 H I recovery checkpoint\n\nStatus: **RECOVERED FROM NATIVE FIGURE-6 VECTOR POINTS**\n\n- Frozen galaxy name: `UGC04483`\n- Source: Lelli et al. 2012b, Figure 6 / `Fig6.eps`\n- Whole-galaxy series: 10 monotonic `CircleF` points; 1 additional `CircleF` is the legend symbol and is excluded.\n- CSV: `data/stationary/source_reconstruction/lelli2012b_ugc4483_hi_profile_v1.csv`\n- Validation: `validation/stationary/lelli2012b_ugc4483_hi_profile_recovery_v1.json`\n- Raw H I; no helium factor applied.\n- `L_A` and `C_A` remain locked.\n\n## Resume point\nDo not re-extract UGC4483. Promote `UGC04483` into the public-source overlay, mark `Le14` partially resolved with `NGC4068 -> Sw02` already deferred, reconcile/rerank, and continue to the next actionable Lelli family.\n')
print(json.dumps({'status':val['status'],'summary':val['profile_summary'],'hard_qc':hard,'gaussian':advisory,'csv':str(OUT),'checkpoint':str(CP)},indent=2))
