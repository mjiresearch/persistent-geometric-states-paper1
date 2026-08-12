#!/usr/bin/env python3
"""Recover NGC5907 native-vector radial H I profiles from HEROES-II Figure 29.

Source: Allaert et al. (2015), A&A 582 A18, arXiv:1507.03095.
The Figure-29 PDF is source-native vector. This script extracts the approaching
(blue) and receding (red) Sigma_HI polylines from the NGC5907 top panel, calibrates
radius and Sigma_HI from native major ticks, verifies marker/polyline agreement,
and writes both source-side profiles plus a clearly labelled deterministic m=0
mean for the stationary axisymmetric build.

The source-side profiles remain authoritative. The m=0 mean is a Paper-I derived
quantity, not an author-published average. No raster digitization, OCR, profile
fitting, map reconstruction, common distance renormalization, helium scaling,
persistence fitting, or blind-outcome inspection is performed.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pymupdf

ARXIV='1507.03095'
URLS=[f'https://arxiv.org/e-print/{ARXIV}', f'https://export.arxiv.org/e-print/{ARXIV}']
PDF_NAME='Final_params_all.pdf'
OUT_SIDES=Path('data/stationary/source_reconstruction/sa87_ngc5907_heroes2015_hi_side_profiles_v1.csv')
OUT_M0=Path('data/stationary/source_reconstruction/sa87_ngc5907_heroes2015_hi_m0_mean_v1.csv')
OUT_QC=Path('validation/stationary/sa87_ngc5907_heroes2015_native_hi_recovery_v1.json')
OUT_CTX=Path('validation/stationary/sa87_ngc5907_heroes2015_source_convention_v1.txt')

# Native PDF panel/tick geometry already independently audited and committed.
PANEL=(1545.119995,75.599976,1789.920044,246.960022)
X_TICKS=np.array([1545.119995,1588.524292,1631.928467,1675.332764,1718.737061,1762.141235],dtype=float)
R_TICKS=np.array([0.,10.,20.,30.,40.,50.],dtype=float)
Y_TICKS=np.array([246.960022,201.865234,156.770508,111.675781],dtype=float)
S_TICKS=np.array([0.,2.,4.,6.],dtype=float)


def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def dec(b:bytes)->str:return b.decode('latin-1',errors='replace')

def fetch_source():
    errs=[]
    for u in URLS:
        try:
            with urlopen(Request(u,headers={'User-Agent':'PaperI-SA87-recovery/1.0'}),timeout=90) as r:
                return r.read(),r.geturl(),r.headers.get_content_type()
        except Exception as e:errs.append([u,repr(e)])
    raise RuntimeError(errs)

def unpack(payload):
    out={}
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        for m in tf.getmembers():
            if m.isfile():
                f=tf.extractfile(m)
                if f:out[m.name]=f.read()
    return out

def color(c):
    if c is None:return None
    return tuple(round(float(x),6) for x in c)
def is_blue(c):return c is not None and c[2]>0.99 and c[0]<0.01 and c[1]<0.01
def is_red(c):return c is not None and c[0]>0.99 and c[1]<0.01 and c[2]<0.01

def in_panel(r):
    x0,y0,x1,y1=PANEL
    cx=(r.x0+r.x1)/2;cy=(r.y0+r.y1)/2
    return x0-2<=cx<=x1+2 and y0-2<=cy<=y1+2

def line_vertices(items):
    seg=[]
    for it in items:
        if it[0]=='l':
            a,b=it[1],it[2]
            seg.append(((float(a.x),float(a.y)),(float(b.x),float(b.y))))
    if not seg:raise RuntimeError('Polyline has no line items')
    pts=[seg[0][0]]
    for a,b in seg:
        if math.hypot(pts[-1][0]-a[0],pts[-1][1]-a[1])>1e-4:
            raise RuntimeError(f'Non-contiguous source polyline: previous={pts[-1]} next={a}')
        pts.append(b)
    # consecutive de-dup only
    out=[]
    for p in pts:
        if not out or math.hypot(out[-1][0]-p[0],out[-1][1]-p[1])>1e-5:out.append(p)
    return out

def fit_axis(x,y):
    m,b=np.polyfit(x,y,1)
    pred=m*x+b
    return float(m),float(b),float(np.max(np.abs(pred-y)))

def parse_source_conventions(files):
    tex=[]
    for n,b in files.items():
        if n.lower().endswith(('.tex','.ltx')):
            tex.append((n,dec(b)))
    side_hits=[];sigma_hits=[];helium_hits=[];fig_hits=[]
    for n,t in tex:
        lines=t.splitlines()
        for i,line in enumerate(lines):
            lo=max(0,i-4);hi=min(len(lines),i+6)
            ctx='\n'.join(f'{j+1}: {lines[j]}' for j in range(lo,hi))
            low=line.lower()
            if 'approach' in low or 'reced' in low:
                side_hits.append({'file':n,'line':i+1,'context':ctx})
            if re.search(r'sigma.*hi|h.?i.*surface dens|surface dens.*h.?i',line,re.I):
                sigma_hits.append({'file':n,'line':i+1,'context':ctx})
            if re.search(r'helium|\bHe\b|1\.36|1\.4',line,re.I):
                helium_hits.append({'file':n,'line':i+1,'context':ctx})
            if PDF_NAME.lower() in low or ('figure' in low and '29' in low):
                fig_hits.append({'file':n,'line':i+1,'context':ctx})
    joined='\n'.join(x['context'] for x in side_hits+fig_hits)
    low=joined.lower()
    side_caption_pass=('blue' in low and 'approach' in low and 'red' in low and 'reced' in low)
    sigma_label_pass=bool(sigma_hits) or ('sigma' in low and 'hi' in low)
    return {'side_hits':side_hits[:40],'sigma_hits':sigma_hits[:80],'helium_hits':helium_hits[:80],'figure29_hits':fig_hits[:40],
            'side_caption_pass':side_caption_pass,'sigma_hi_source_label_pass':sigma_label_pass}

def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    payload,url,ctype=fetch_source();files=unpack(payload)
    pdf=None
    for n,b in files.items():
        if Path(n).name==PDF_NAME:pdf=b;break
    if pdf is None:raise RuntimeError(f'{PDF_NAME} missing')
    conv=parse_source_conventions(files)
    if not conv['side_caption_pass']:
        raise RuntimeError('Could not verify source caption blue=approaching, red=receding')
    if not conv['sigma_hi_source_label_pass']:
        raise RuntimeError('Could not verify source quantity is Sigma_HI')

    page=pymupdf.open(stream=pdf,filetype='pdf')[0]
    polylines={};markers={'blue':[],'red':[]}
    for i,d in enumerate(page.get_drawings()):
        r=d['rect']
        if not in_panel(r):continue
        c=color(d.get('color'));f=color(d.get('fill'));typ=d.get('type');w=float(d.get('width') or 0)
        ser='blue' if (is_blue(c) or is_blue(f)) else ('red' if (is_red(c) or is_red(f)) else None)
        if ser is None:continue
        if typ=='f' and abs(r.width-3.0)<0.05 and abs(r.height-3.0)<0.05:
            markers[ser].append({'index':i,'x':float((r.x0+r.x1)/2),'y':float((r.y0+r.y1)/2)})
        if typ=='s' and w>=0.9 and r.width>200 and len(d.get('items',[]))>=50:
            if ser in polylines:raise RuntimeError(f'Multiple {ser} source polylines in panel')
            polylines[ser]={'index':i,'vertices':line_vertices(d.get('items',[])),'rect':[float(r.x0),float(r.y0),float(r.x1),float(r.y1)]}
    if set(polylines)!={'blue','red'}:raise RuntimeError(f'Expected one red/one blue polyline; got {polylines.keys()}')
    for ser in ('blue','red'):
        if len(polylines[ser]['vertices'])!=54:raise RuntimeError(f'{ser} polyline count={len(polylines[ser]["vertices"])} !=54')
        if len(markers[ser])!=54:raise RuntimeError(f'{ser} marker count={len(markers[ser])} !=54')
        markers[ser].sort(key=lambda x:x['x'])

    mx,bx,xfit=fit_axis(X_TICKS,R_TICKS)
    my,by,yfit=fit_axis(Y_TICKS,S_TICKS)
    def R(x):return mx*x+bx
    def S(y):return my*y+by

    source_rows=[];phys={}
    marker_resid={};x_monotonic={}
    side_map={'blue':'approaching','red':'receding'}
    for ser in ('blue','red'):
        pts=polylines[ser]['vertices']
        # Native drawing order should already be increasing radius.
        xs=np.array([p[0] for p in pts]);ys=np.array([p[1] for p in pts])
        x_monotonic[ser]=bool(np.all(np.diff(xs)>0))
        if not x_monotonic[ser]:raise RuntimeError(f'{ser} source polyline is not monotonic in radius')
        ms=markers[ser]
        resid=[]
        for (x,y),m in zip(pts,ms):resid.append(math.hypot(x-m['x'],y-m['y']))
        marker_resid[ser]={'max_pdf_points':max(resid),'rms_pdf_points':float(np.sqrt(np.mean(np.square(resid))))}
        if max(resid)>0.01:raise RuntimeError(f'{ser} marker/polyline mismatch max={max(resid)}')
        arr=[]
        for j,(x,y) in enumerate(pts):
            rr=float(R(x));ss=float(S(y))
            # Last samples may mathematically land at zero; reject materially negative recovered values.
            if ss < -0.02:raise RuntimeError(f'{ser} negative Sigma_HI at j={j}: {ss}')
            if abs(ss)<0.02:ss=max(0.0,ss)
            arr.append((rr,ss,x,y))
            source_rows.append({
                'galaxy':'NGC5907','stationary_role':'calibration','side':side_map[ser],'side_color':ser,'sample_index':j,
                'radius_kpc_source':f'{rr:.9f}','sigma_hi_msun_pc2':f'{ss:.9f}','source_x_pdf':f'{x:.6f}','source_y_pdf':f'{y:.6f}',
                'source_figure':'Allaert et al. 2015 Figure 29','source_asset':PDF_NAME,
                'source_quantity':'source-native side-specific Sigma_HI','helium_applied':'no recovery scaling; source quantity is explicitly Sigma_HI'
            })
        phys[ser]=arr
    # Grid equality QC.
    ra=np.array([x[0] for x in phys['blue']]);rr=np.array([x[0] for x in phys['red']])
    grid_delta=np.abs(ra-rr)
    if np.max(grid_delta)>1e-5:raise RuntimeError(f'approaching/receding radius grids differ: max={np.max(grid_delta)} kpc')

    m0=[]
    for j,(a,r) in enumerate(zip(phys['blue'],phys['red'])):
        radius=0.5*(a[0]+r[0]);mean=0.5*(a[1]+r[1]);half=0.5*abs(a[1]-r[1])
        m0.append({
            'galaxy':'NGC5907','stationary_role':'calibration','sample_index':j,'radius_kpc_source':f'{radius:.9f}',
            'sigma_hi_m0_mean_msun_pc2':f'{mean:.9f}','sigma_hi_half_side_difference_msun_pc2':f'{half:.9f}',
            'sigma_hi_approaching_msun_pc2':f'{a[1]:.9f}','sigma_hi_receding_msun_pc2':f'{r[1]:.9f}',
            'derivation':'Paper-I deterministic arithmetic mean of source-published approaching and receding Sigma_HI at identical native radii; not an author-published average',
            'source_figure':'Allaert et al. 2015 Figure 29','source_asset':PDF_NAME,'helium_applied':'no recovery scaling; source quantity is explicitly Sigma_HI'
        })

    source_fields=['galaxy','stationary_role','side','side_color','sample_index','radius_kpc_source','sigma_hi_msun_pc2','source_x_pdf','source_y_pdf','source_figure','source_asset','source_quantity','helium_applied']
    m0_fields=['galaxy','stationary_role','sample_index','radius_kpc_source','sigma_hi_m0_mean_msun_pc2','sigma_hi_half_side_difference_msun_pc2','sigma_hi_approaching_msun_pc2','sigma_hi_receding_msun_pc2','derivation','source_figure','source_asset','helium_applied']
    write_csv(OUT_SIDES,source_rows,source_fields);write_csv(OUT_M0,m0,m0_fields)

    side_diff=np.array([float(x['sigma_hi_half_side_difference_msun_pc2'])*2 for x in m0])
    meanv=np.array([float(x['sigma_hi_m0_mean_msun_pc2']) for x in m0])
    qc={
      'status':'SA87_NGC5907_HEROES_NATIVE_HI_PROFILES_RECOVERED',
      'sparc_ref_id':'SA87','galaxy':'NGC5907','stationary_role':'calibration',
      'lelli_reference':'Sancisi & van Albada 1987 (review); original NGC5907 H I lineage Sancisi 1976',
      'recovery_source':'Allaert et al. 2015 A&A 582 A18 HEROES II; arXiv:1507.03095',
      'source_url':url,'source_content_type':ctype,'source_tar_sha256':sha(payload),'source_pdf':PDF_NAME,'source_pdf_sha256':sha(pdf),
      'source_convention':{
          'quantity':'Sigma_HI (M_sun pc^-2), source axis label','blue':'approaching','red':'receding',
          'helium_handling':'No helium multiplication or division is applied in recovery. Values are preserved as the source-labeled Sigma_HI quantity.',
          'helium_keyword_hits_in_source_tex':conv['helium_hits'],
          'source_caption_contexts':conv['side_hits'][:20]+conv['figure29_hits'][:20],
      },
      'axis_calibration':{
          'x_tick_pdf':X_TICKS.tolist(),'radius_tick_kpc':R_TICKS.tolist(),'radius_slope_kpc_per_pdf_point':mx,'radius_intercept_kpc':bx,'max_tick_residual_kpc':xfit,
          'y_tick_pdf':Y_TICKS.tolist(),'sigma_tick_msun_pc2':S_TICKS.tolist(),'sigma_slope_per_pdf_point':my,'sigma_intercept_msun_pc2':by,'max_tick_residual_msun_pc2':yfit,
      },
      'source_profiles':{
          'approaching':{'color':'blue','n_points':54,'polyline_index':polylines['blue']['index'],'marker_count':54,'marker_polyline_qc':marker_resid['blue']},
          'receding':{'color':'red','n_points':54,'polyline_index':polylines['red']['index'],'marker_count':54,'marker_polyline_qc':marker_resid['red']},
          'identical_radius_grid_max_delta_kpc':float(np.max(grid_delta)),
          'radius_range_kpc':[float(ra.min()),float(ra.max())],
      },
      'derived_m0_mean':{
          'n_points':54,'status':'derived_not_source_published','definition':'0.5*(Sigma_HI_approaching + Sigma_HI_receding) at identical source-native radius',
          'mean_sigma_range_msun_pc2':[float(meanv.min()),float(meanv.max())],
          'max_full_side_difference_msun_pc2':float(side_diff.max()),
          'purpose':'deterministic axisymmetric m=0 source representation; source-side CSV remains authoritative recovery product'
      },
      'outputs':{'source_side_profiles':str(OUT_SIDES),'derived_m0_mean':str(OUT_M0)},
      'boundary':'No raster digitization, OCR, profile fitting, calibrated-map reconstruction, common-distance renormalization, helium correction, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT_QC.parent.mkdir(parents=True,exist_ok=True);OUT_QC.write_text(json.dumps(qc,indent=2)+'\n')
    ctx=[]
    ctx.append('SOURCE CONVENTION: source axis is Sigma_HI; no helium scaling applied in recovery.')
    ctx.append('SIDE CONVENTION VERIFIED FROM SOURCE TEX: blue=approaching, red=receding.')
    for x in conv['side_hits'][:20]:ctx += [f"--- {x['file']} line {x['line']} ---",x['context']]
    ctx.append('\nSIGMA_HI CONTEXTS')
    for x in conv['sigma_hits'][:30]:ctx += [f"--- {x['file']} line {x['line']} ---",x['context']]
    ctx.append('\nHELIUM KEYWORD CONTEXTS (audit only; no scaling inferred)')
    for x in conv['helium_hits'][:30]:ctx += [f"--- {x['file']} line {x['line']} ---",x['context']]
    OUT_CTX.write_text('\n'.join(ctx)+'\n',encoding='utf-8')
    print(json.dumps({'status':qc['status'],'source_rows':len(source_rows),'m0_rows':len(m0),'radius_range_kpc':qc['source_profiles']['radius_range_kpc'],'axis_tick_residuals':{'radius_kpc':xfit,'sigma':yfit},'marker_qc':marker_resid,'grid_delta_kpc':float(np.max(grid_delta)),'outputs':qc['outputs']|{'qc':str(OUT_QC),'context':str(OUT_CTX)}},indent=2))

if __name__=='__main__':main()
