#!/usr/bin/env python3
"""Recover VM97 / NGC6015 Figure-3d source-native H I radial profile.

Source: Verdes-Montenegro, Bosma & Athanassoula (1997), A&A 321, 754-764.
The legacy A&A electronic article contains Figure 3 as a pure PGPLOT EPS
(`07540003.eps`), with no raster operators. Panel 3d contains 31 M3 source
markers. This script statically extracts those markers and calibrates the axes
from source-native PGPLOT major ticks / stroke-glyph numeric labels.

Axis labels decoded from the native glyph groups:
  lower radius axis: 0,100,200,300 arcsec at x=435,1318,2200,3083
  H I surface-density axis: 0,2,4,6,8 at y=326,592,857,1123,1388
The paper caption states the upper radial scale is kpc for D=13.9 Mpc.

No PostScript execution, raster digitization, OCR, profile fitting, helium
correction, common-distance renormalization, persistence fitting, or blind
outcome inspection is performed.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

URLS=[
 'https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz',
 'https://cdsarc.u-strasbg.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz',
]
TARGET='07540003.eps'
OUT=Path('data/stationary/source_reconstruction/vm97_ngc6015_hi_profile_v1.csv')
QC=Path('validation/stationary/vm97_ngc6015_native_hi_profile_recovery_v1.json')
CTX=Path('validation/stationary/vm97_ngc6015_axis_label_calibration_v1.txt')

D_MPC=13.9
INCL_DEG=63.0
X_MAJOR=np.array([435.,1318.,2200.,3083.])
R_ARCSEC_MAJOR=np.array([0.,100.,200.,300.])
Y_MAJOR=np.array([326.,592.,857.,1123.,1388.])
SIGMA_MAJOR=np.array([0.,2.,4.,6.,8.])
EXPECTED_GRID_ARCSEC=15.+10.*np.arange(31)
PAPER_MHI_MSUN=3.9e9


def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def fetch():
    errs=[]
    for u in URLS:
        try:
            with urlopen(Request(u,headers={'User-Agent':'PaperI-VM97-recovery/1.0'}),timeout=90) as r:
                return r.read(),r.geturl()
        except Exception as e:errs.append([u,repr(e)])
    raise RuntimeError(errs)

def extract_doc(text,name):
    m=re.search(r'^%%BeginDocument:\s*'+re.escape(name)+r'\s*$',text,re.M)
    if not m:raise RuntimeError(f'{name} not found')
    e=re.search(r'^%%EndDocument\s*$',text[m.end():],re.M)
    if not e:raise RuntimeError(f'{name} end not found')
    return text[m.start():m.end()+e.end()]

def fit_axis(native,physical):
    m,b=np.polyfit(native,physical,1)
    residual=m*native+b-physical
    return float(m),float(b),float(np.max(np.abs(residual))),residual.tolist()

def write_csv(rows):
    fields=list(rows[0])
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    gz,url=fetch();ps=gzip.decompress(gz);full=ps.decode('latin-1',errors='replace');eps=extract_doc(full,TARGET)
    # Guard source structure: pure PGPLOT vector, no raster operators.
    raster=sum(len(re.findall(r'(?<![A-Za-z])'+op+r'(?![A-Za-z])',eps)) for op in ['image','colorimage','imagemask'])
    if raster!=0:raise RuntimeError(f'Figure 3 no longer pure vector; raster ops={raster}')
    if '%%Title: PGPLOT PostScript plot' not in eps:raise RuntimeError('Unexpected Figure-3 source format')

    # Exact panel 3d M3 source calls. Restrict to bottom frame bounds to exclude the M3 procedure definition.
    markers=[]
    for m in re.finditer(r'(?<![\w/.-])(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+M3\b',eps):
        x=float(m.group(1));y=float(m.group(2))
        if 435<=x<=3260 and 326<=y<=1521:
            markers.append((x,y,m.start()))
    if len(markers)!=31:raise RuntimeError(f'Expected 31 Figure-3d M3 markers, got {len(markers)}')
    markers.sort(key=lambda q:q[0])
    if not all(markers[i+1][0]>markers[i][0] for i in range(30)):raise RuntimeError('M3 radius positions not strictly monotonic')

    mx,bx,xfit,xres=fit_axis(X_MAJOR,R_ARCSEC_MAJOR)
    my,by,yfit,yres=fit_axis(Y_MAJOR,SIGMA_MAJOR)
    if xfit>0.05:raise RuntimeError(f'x tick calibration residual too large: {xfit} arcsec')
    if yfit>0.005:raise RuntimeError(f'y tick calibration residual too large: {yfit}')

    rows=[];arc=[];sig=[]
    kpc_per_arcsec=D_MPC*1000.0/206265.0
    for i,(x,y,char) in enumerate(markers):
        radius_arcsec=mx*x+bx
        sigma=my*y+by
        if sigma<0:raise RuntimeError(f'Negative recovered Sigma_HI at row {i}: {sigma}')
        radius_kpc=radius_arcsec*kpc_per_arcsec
        grid_delta=radius_arcsec-EXPECTED_GRID_ARCSEC[i]
        rows.append({
            'galaxy':'NGC6015','stationary_role':'calibration','sample_index':i,
            'radius_arcsec_vector':f'{radius_arcsec:.9f}',
            'radius_arcsec_native_grid_qc':f'{EXPECTED_GRID_ARCSEC[i]:.6f}',
            'radius_grid_delta_arcsec':f'{grid_delta:.9f}',
            'radius_kpc_source_scale':f'{radius_kpc:.9f}',
            'sigma_hi_msun_pc2':f'{sigma:.9f}',
            'source_x_pgplot':f'{x:.6f}','source_y_pgplot':f'{y:.6f}','source_marker_char':char,
            'source_figure':'Verdes-Montenegro et al. 1997 Figure 3d','source_asset':TARGET,
            'helium_applied':'no; source H I surface density preserved'
        })
        arc.append(radius_arcsec);sig.append(sigma)
    write_csv(rows)
    arc=np.asarray(arc);sig=np.asarray(sig)
    grid_delta=arc-EXPECTED_GRID_ARCSEC

    # Independent source-text QC 1: central depression is stated as ~57% of peak H I surface intensity.
    central_peak_ratio=float(sig[0]/np.max(sig))
    central_ratio_delta=abs(central_peak_ratio-0.57)
    if central_ratio_delta>0.03:
        raise RuntimeError(f'Central/peak QC inconsistent with source statement: {central_peak_ratio}')

    # Independent source-text QC 2: approximate annular mass over the 31 point-centered bins.
    # Native grid centers are 15..315 arcsec => midpoint annular edges 10..320 arcsec.
    # This intentionally excludes any unrepresented <10 or >320 arcsec material.
    edges_arc=np.arange(10.,321.,10.)
    edges_pc=edges_arc*kpc_per_arcsec*1000.0
    annulus_area_pc2=math.pi*(edges_pc[1:]**2-edges_pc[:-1]**2)
    approx_mhi=float(np.sum(sig*annulus_area_pc2))
    mass_frac_delta=abs(approx_mhi-PAPER_MHI_MSUN)/PAPER_MHI_MSUN
    if mass_frac_delta>0.12:
        raise RuntimeError(f'Profile-integrated H I mass QC too far from paper value: {approx_mhi}')

    qc={
      'status':'VM97_NGC6015_NATIVE_VECTOR_HI_PROFILE_RECOVERED',
      'sparc_ref_id':'VM97','galaxy':'NGC6015','stationary_role':'calibration',
      'source':'Verdes-Montenegro, Bosma & Athanassoula 1997 A&A 321, 754-764',
      'source_url':url,'legacy_article_ps_gz_sha256':sha(gz),'legacy_article_ps_sha256':sha(ps),
      'figure3_embedded_asset':TARGET,'figure3_eps_sha256':sha(eps.encode('latin-1',errors='replace')),
      'figure3_native_structure':{'creator':'PGPLOT','raster_operator_count':raster,'panel':'3d','marker_primitive':'M3','n_profile_points':31},
      'source_conventions':{
        'quantity':'H I surface density / radial H I column-density distribution',
        'units':'M_sun pc^-2; confirmed by native numeric axis scale plus independent integrated M_HI consistency',
        'helium':'not applied; source H I profile reproduces the paper H I mass scale without helium multiplication',
        'source_distance_mpc':D_MPC,'source_inclination_deg':INCL_DEG,
        'radius_caption':'lower scale arcsec, upper scale kpc for D=13.9 Mpc'
      },
      'axis_calibration':{
        'x_major_native':X_MAJOR.tolist(),'x_major_labels_arcsec':R_ARCSEC_MAJOR.tolist(),
        'radius_arcsec_slope_per_pgplot_unit':mx,'radius_arcsec_intercept':bx,'max_x_major_residual_arcsec':xfit,'x_residuals_arcsec':xres,
        'y_major_native':Y_MAJOR.tolist(),'y_major_labels_sigma_hi':SIGMA_MAJOR.tolist(),
        'sigma_slope_per_pgplot_unit':my,'sigma_intercept':by,'max_y_major_residual_msun_pc2':yfit,'y_residuals_msun_pc2':yres,
        'label_decode_note':'numeric labels decoded statically from source-native PGPLOT stroke-glyph groups; no rendered-image reading/OCR'
      },
      'native_grid_qc':{
        'expected_centers_arcsec':'15 + 10*n, n=0..30','max_abs_delta_arcsec':float(np.max(np.abs(grid_delta))),
        'rms_delta_arcsec':float(np.sqrt(np.mean(grid_delta**2))),'passes':bool(np.max(np.abs(grid_delta))<0.1)
      },
      'source_statement_qc':{
        'paper_central_HI_depression_fraction_of_peak_approx':0.57,
        'recovered_first_bin_over_peak':central_peak_ratio,'abs_delta':central_ratio_delta,'passes':central_ratio_delta<0.03,
        'paper_total_HI_mass_msun':PAPER_MHI_MSUN,
        'profile_annular_integral_10_to_320_arcsec_msun':approx_mhi,
        'mass_fractional_abs_delta':mass_frac_delta,'mass_qc_note':'simple midpoint-annulus integral over profile-covered 10-320 arcsec only; used as independent scale/unit QC, not a replacement mass measurement'
      },
      'profile_ranges':{'radius_arcsec':[float(arc.min()),float(arc.max())],'radius_kpc_source_scale':[float(arc.min()*kpc_per_arcsec),float(arc.max()*kpc_per_arcsec)],'sigma_hi_msun_pc2':[float(sig.min()),float(sig.max())]},
      'profile_csv':str(OUT),
      'boundary':'No PostScript execution, raster digitization, OCR, profile fitting, helium scaling, common-distance normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    QC.parent.mkdir(parents=True,exist_ok=True);QC.write_text(json.dumps(qc,indent=2)+'\n')
    CTX.write_text(
        'VM97 / NGC6015 Figure 3d native-axis calibration\n\n'
        'Source-native PGPLOT major-label decode (stroke geometry; no OCR/rendering):\n'
        '  lower radius axis: x=[435,1318,2200,3083] -> [0,100,200,300] arcsec\n'
        '  H I surface-density axis: y=[326,592,857,1123,1388] -> [0,2,4,6,8] M_sun pc^-2\n\n'
        f'Linear fit residuals: x max={xfit:.9g} arcsec; y max={yfit:.9g} M_sun pc^-2.\n'
        f'31 M3 marker centers map to native 15,25,...315 arcsec grid with max |delta|={np.max(np.abs(grid_delta)):.6g} arcsec.\n'
        f'Independent source-text QC: first-bin/peak={central_peak_ratio:.6f} vs paper ~0.57.\n'
        f'Independent mass-scale QC: annular integral={approx_mhi:.6e} M_sun vs paper M_HI={PAPER_MHI_MSUN:.6e} M_sun (fractional delta={mass_frac_delta:.4%}).\n'
        'The mass-scale check strongly rejects a hidden helium multiplication: source values are retained as raw H I.\n',encoding='utf-8')
    print(json.dumps({'status':qc['status'],'n_points':31,'grid_max_delta_arcsec':qc['native_grid_qc']['max_abs_delta_arcsec'],'central_peak_ratio':central_peak_ratio,'approx_profile_mhi_msun':approx_mhi,'mass_frac_delta':mass_frac_delta,'ranges':qc['profile_ranges'],'outputs':[str(OUT),str(QC),str(CTX)]},indent=2))

if __name__=='__main__':main()
