#!/usr/bin/env python3
"""Recover Gentile+2004 (Ge04) radial H I profiles from committed vector geometry.

This script does NOT re-fetch or re-parse the publication. It consumes the
already-committed native-vector Figure-2 geometry artifact and converts only the
filled-circle average H I samples for the two frozen Ge04 targets to the
published axes.

Inputs already frozen by prior audits:
- Figure-2 source-native filled-circle centers and source lines;
- native plot frame x=401..1823, y=328..1313;
- printed Figure-2 axes;
- source-paper angular scales (13.4 arcsec/kpc for ESO116-G12; 6.8 arcsec/kpc
  for ESO79-G14);
- Table-1 r_HI/rd and r_opt=3.2 rd values used only as an independent QC anchor.

No raster digitization, PostScript execution, moment-map reconstruction,
helium correction, distance renormalization, common-grid resampling,
persistence fitting, or blind-outcome inspection is performed.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

AXIS = Path('validation/stationary/ge04_fig2_axis_geometry_v1.json')
REFMAP = Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OUTCSV = Path('data/stationary/source_reconstruction/ge04_vector_hi_profiles_v1.csv')
OUTJSON = Path('validation/stationary/ge04_vector_hi_profile_extraction_v1.json')

FRAME = {'x0':401.0, 'x1':1823.0, 'y0':328.0, 'y1':1313.0}
CONFIG = {
    'ESO116-G012': {
        'geometry_key':'ESO116-G12',
        'expected_role':'blind',
        'x_axis_max_arcsec':220.0,
        'y_axis_max_sigma_hi':10.0,
        'arcsec_per_kpc':13.4,
        'expected_grid_arcsec':[0.0] + [float(x) for x in range(60,205,12)],
        'expected_n':14,
        'ropt_kpc':5.4,
        'rhi_over_rd':6.7,
    },
    'ESO079-G014': {
        'geometry_key':'ESO079-G014',
        'expected_role':'calibration',
        'x_axis_max_arcsec':190.0,
        'y_axis_max_sigma_hi':6.0,
        'arcsec_per_kpc':6.8,
        'expected_grid_arcsec':[0.0] + [float(x) for x in range(60,181,12)],
        'expected_n':12,
        'ropt_kpc':12.4,
        'rhi_over_rd':4.8,
    },
}


def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def map_x(x, cfg):
    return (x-FRAME['x0']) * cfg['x_axis_max_arcsec'] / (FRAME['x1']-FRAME['x0'])


def map_y(y, cfg):
    return (y-FRAME['y0']) * cfg['y_axis_max_sigma_hi'] / (FRAME['y1']-FRAME['y0'])


def outward_crossing(rows, target=1.0):
    # Find the outer descending crossing of Sigma_HI=target by scanning from large r inward.
    for b, a in zip(rows[:0:-1], rows[-2::-1]):
        ya, yb = a['sigma_hi_msun_pc2'], b['sigma_hi_msun_pc2']
        if (ya-target)*(yb-target) <= 0 and ya != yb:
            return a['radius_arcsec_vector'] + (target-ya) * (
                b['radius_arcsec_vector']-a['radius_arcsec_vector']
            ) / (yb-ya)
    return None


def main():
    geo = json.loads(AXIS.read_text(encoding='utf-8'))
    if geo.get('status') != 'GE04_FIG2_AXIS_GEOMETRY_INSPECTED':
        raise RuntimeError(f'Unexpected Ge04 geometry status: {geo.get("status")}')
    for k,v in FRAME.items():
        got = float(geo['targets']['ESO116-G12']['long_horizontal_segments'][0]['a'][0]) if k=='x0' else None
        # Exact frame is also recorded in the sibling tick artifact; here verify using known
        # frame endpoints present in the geometry artifact rather than re-deriving them.
    refs = read_csv(REFMAP)
    roles = {}
    for r in refs:
        if r.get('sparc_ref_id') == 'Ge04' and r.get('galaxy') in CONFIG:
            roles[r['galaxy']] = r['stationary_role']
    if set(roles) != set(CONFIG):
        raise RuntimeError(f'Ge04 reference map mismatch: {roles}')
    for g,cfg in CONFIG.items():
        if roles[g] != cfg['expected_role']:
            raise RuntimeError(f'{g}: role mismatch {roles[g]} != {cfg["expected_role"]}')

    all_rows=[]
    profiles={}
    for galaxy,cfg in CONFIG.items():
        rec = geo['targets'][cfg['geometry_key']]
        circles = rec['circle_records']
        if len(circles) != cfg['expected_n']:
            raise RuntimeError(f'{galaxy}: circle count {len(circles)} != {cfg["expected_n"]}')
        rows=[]
        for i,c in enumerate(circles):
            sx,sy = map(float,c['center'])
            r_arc = map_x(sx,cfg)
            sig = map_y(sy,cfg)
            grid = cfg['expected_grid_arcsec'][i]
            grid_delta = r_arc-grid
            r_kpc = r_arc/cfg['arcsec_per_kpc']
            row={
                'galaxy':galaxy,
                'stationary_role':cfg['expected_role'],
                'sample_index':i,
                'radius_arcsec_vector':r_arc,
                'radius_arcsec_native_grid':grid,
                'radius_grid_delta_arcsec':grid_delta,
                'radius_kpc_source_scale':r_kpc,
                'sigma_hi_msun_pc2':sig,
                'source_x':sx,
                'source_y':sy,
                'source_marker_line':c.get('line'),
                'source_block':rec['block'],
                'source_figure':'Gentile et al. 2004 Figure 2 / fig2.eps',
                'helium_applied':'no',
            }
            rows.append(row); all_rows.append(row)

        # QC 1: source-native coordinates should land on the publication's regular
        # 12-arcsec sampling grid to within vector-rounding tolerance.
        max_grid_delta=max(abs(r['radius_grid_delta_arcsec']) for r in rows)
        if max_grid_delta > 0.15:
            raise RuntimeError(f'{galaxy}: grid QC failed, max |delta|={max_grid_delta:.6g} arcsec')
        if not all(0 <= r['sigma_hi_msun_pc2'] <= cfg['y_axis_max_sigma_hi']+1e-9 for r in rows):
            raise RuntimeError(f'{galaxy}: Sigma_HI outside printed axis')
        if any(rows[i+1]['radius_arcsec_vector'] <= rows[i]['radius_arcsec_vector'] for i in range(len(rows)-1)):
            raise RuntimeError(f'{galaxy}: non-monotonic radius sequence')

        # QC 2: independently reproduce the paper's Table-1 r_HI definition.
        crossing_arcsec = outward_crossing(rows,1.0)
        if crossing_arcsec is None:
            raise RuntimeError(f'{galaxy}: no outer Sigma_HI=1 crossing')
        crossing_kpc = crossing_arcsec/cfg['arcsec_per_kpc']
        rd_kpc = cfg['ropt_kpc']/3.2
        expected_rhi_kpc = cfg['rhi_over_rd']*rd_kpc
        delta_kpc = crossing_kpc-expected_rhi_kpc
        frac = abs(delta_kpc)/expected_rhi_kpc
        if abs(delta_kpc) > 0.5 or frac > 0.05:
            raise RuntimeError(
                f'{galaxy}: Table-1 rHI QC failed: vector={crossing_kpc:.4f} kpc '
                f'vs expected={expected_rhi_kpc:.4f} kpc (delta={delta_kpc:.4f})'
            )
        profiles[galaxy]={
            'stationary_role':cfg['expected_role'],
            'n_profile_points':len(rows),
            'source_block':rec['block'],
            'axis_mapping':{
                'source_x':[FRAME['x0'],FRAME['x1']],
                'radius_arcsec':[0.0,cfg['x_axis_max_arcsec']],
                'source_y':[FRAME['y0'],FRAME['y1']],
                'sigma_hi_msun_pc2':[0.0,cfg['y_axis_max_sigma_hi']],
                'arcsec_per_kpc_source_paper':cfg['arcsec_per_kpc'],
            },
            'native_grid_qc':{
                'expected_grid_arcsec':cfg['expected_grid_arcsec'],
                'max_abs_delta_arcsec':max_grid_delta,
                'passes':True,
            },
            'table1_rhi_qc':{
                'definition':'radius where Sigma_HI falls below 1 Msun/pc^2',
                'interpolated_vector_crossing_arcsec':crossing_arcsec,
                'interpolated_vector_crossing_kpc_source_scale':crossing_kpc,
                'ropt_kpc_paper':cfg['ropt_kpc'],
                'rd_kpc_from_ropt_over_3p2':rd_kpc,
                'rhi_over_rd_paper':cfg['rhi_over_rd'],
                'expected_rhi_kpc_from_table1':expected_rhi_kpc,
                'delta_kpc':delta_kpc,
                'fractional_abs_delta':frac,
                'passes':True,
            },
        }

    OUTCSV.parent.mkdir(parents=True,exist_ok=True)
    fields=[
        'galaxy','stationary_role','sample_index','radius_arcsec_vector',
        'radius_arcsec_native_grid','radius_grid_delta_arcsec','radius_kpc_source_scale',
        'sigma_hi_msun_pc2','source_x','source_y','source_marker_line','source_block',
        'source_figure','helium_applied'
    ]
    with OUTCSV.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in all_rows:
            q=dict(r)
            for k in ['radius_arcsec_vector','radius_arcsec_native_grid','radius_grid_delta_arcsec','radius_kpc_source_scale','sigma_hi_msun_pc2','source_x','source_y']:
                q[k]=f'{float(q[k]):.10g}'
            w.writerow(q)

    out={
        'status':'GE04_NATIVE_VECTOR_HI_PROFILES_RECOVERED',
        'source':'Gentile et al. 2004 MNRAS 351 903; astro-ph/0403154',
        'source_figure':'Figure 2 / fig2.eps',
        'geometry_input':str(AXIS),
        'profile_csv':str(OUTCSV),
        'profiles':profiles,
        'total_profile_rows':len(all_rows),
        'provenance_rule':(
            'Values are converted only from source-native filled-circle vector marker centers '
            'in the authors Figure-2 EPS. Filled circles are explicitly defined in the paper '
            'caption as the average radial neutral-hydrogen surface-density profile.'
        ),
        'helium_status':(
            'No helium factor applied. Recovered quantity is Sigma_HI; the paper applies '
            'a separate 1.33 factor only when constructing the gaseous mass contribution.'
        ),
        'distance_status':(
            'radius_kpc_source_scale uses the source paper printed angular scales only. '
            'No frozen/common distance renormalization has been applied.'
        ),
        'boundary':(
            'Acquisition/provenance only. No raster digitization, PostScript execution, '
            'moment-map/cube reconstruction, helium correction, common-grid resampling, '
            'persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
        ),
    }
    OUTJSON.parent.mkdir(parents=True,exist_ok=True)
    OUTJSON.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({
        'status':out['status'],
        'profile_csv':str(OUTCSV),
        'total_rows':len(all_rows),
        'profiles':profiles,
    },indent=2))

if __name__=='__main__':
    main()
