#!/usr/bin/env python3
"""Recover NGC289's measured radial H I profile from HIX2018 Figure A3(b).

The source TeX identifies panel (b) as the H I column-density profile measured
from elliptical annuli in the non-clipped ATCA moment-0 map. This script reads
only native PDF vector geometry and native text. No OCR/raster digitization.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen
import fitz

URL='https://arxiv.org/e-print/1802.04043'
PDF_MEMBER='Images/app-fig3.pdf'
TEX_MEMBER='hix2_main.tex'
PROFILE=Path('data/stationary/source_reconstruction/hix2018_ngc0289_hi_profile_v1.csv')
AUDIT=Path('validation/stationary/hix2018_ngc0289_native_hi_profile_recovery_v1.json')
CAL=Path('validation/stationary/hix2018_ngc0289_axis_calibration_v1.txt')
REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
UA='PaperI-HIX-NGC289-native-recovery/1.0'

def sha(b):return hashlib.sha256(b).hexdigest()
def nearblack(v):return v is not None and max(v)<=0.06

def load_frozen_distance():
    # Search authoritative stationary CSVs for an NGC0289 row and a distance-like field.
    candidates=[
      Path('data/stationary/stationary_master_v1.csv'),
      Path('data/stationary/stationary_master.csv'),
      Path('data/stationary/stationary_sample_frozen_v1.csv'),
      Path('data/stationary/stationary_sample_v1.csv'),
      Path('data/stationary/stationary_master_frozen.csv')]
    found=[]
    for p in candidates:
        if not p.exists():continue
        with p.open(newline='',encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        for r in rows:
            name=r.get('galaxy') or r.get('Galaxy') or r.get('name') or r.get('Name')
            if name=='NGC0289':
                for k,v in r.items():
                    if k and ('dist' in k.lower() or k.lower() in {'d','distance_mpc'}):
                        try: found.append({'file':str(p),'field':k,'value':float(v)})
                        except: pass
    return found

def extract_text_context(tex):
    keys=[]
    for phrase in ['Panel (b):','non-clipped moment 0 maps','M_{HI + He} = 1.35 M_{HI}','NGC\\,289 &']:
        pos=tex.find(phrase)
        if pos>=0:keys.append({'phrase':phrase,'context':re.sub(r'\s+',' ',tex[max(0,pos-500):pos+1300]).strip()})
    return keys

def main():
    with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=60) as r:
        payload=r.read();final=r.geturl()
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        pdf=tf.extractfile(tf.getmember(PDF_MEMBER)).read()
        tex=tf.extractfile(tf.getmember(TEX_MEMBER)).read().decode('latin-1',errors='replace')
    d=fitz.open(stream=pdf,filetype='pdf');p=d[0]
    drawings=p.get_drawings()
    # Profile markers are the unique repeated 3x3 pt black filled+stroked glyph family in panel (b).
    markers=[]
    for i,x in enumerate(drawings):
        r=x.get('rect')
        if not r:continue
        if x.get('type')=='fs' and nearblack(x.get('color')) and nearblack(x.get('fill')) and abs(r.width-3.0)<0.03 and abs(r.height-3.0)<0.03 and 232<=((r.x0+r.x1)/2)<=364 and 28<=((r.y0+r.y1)/2)<=148 and len(x.get('items',[]))==8:
            markers.append({'i':i,'x':(r.x0+r.x1)/2,'y':(r.y0+r.y1)/2})
    markers.sort(key=lambda z:z['x'])
    if len(markers)!=52: raise RuntimeError(f'Expected 52 native H I markers, found {len(markers)}')

    # Native tick primitives. Top x-axis ticks are 0-width 3.5pt filled/stroked black paths at y~28.85.
    xt=[]; yt=[]
    for i,x in enumerate(drawings):
        r=x.get('rect')
        if not r or x.get('type')!='fs' or not nearblack(x.get('color')) or not nearblack(x.get('fill')):continue
        cx=(r.x0+r.x1)/2;cy=(r.y0+r.y1)/2
        if abs(r.width)<0.03 and abs(r.height-3.5)<0.03 and 228<cx<365 and 27<cy<31: xt.append({'i':i,'x':cx,'y':cy})
        if abs(r.width-3.5)<0.03 and abs(r.height)<0.03 and 228<cx<234 and 25<cy<152: yt.append({'i':i,'x':cx,'y':cy})
    xt.sort(key=lambda z:z['x']);yt.sort(key=lambda z:z['y'])
    # Major native text/tick labels show 0,25,50,75 kpc at four of the top ticks.
    # Require exact positions matching the four major tick primitives.
    xmaj=xt[:]
    if len(xmaj)!=4: raise RuntimeError(f'Expected four major top x ticks, found {xmaj}')
    xvals=[0.0,25.0,50.0,75.0]
    # Left y axis shows 0,2,4,6 Msun/pc2, increasing upward (PDF y decreases upward).
    # Keep major tick rows by matching native label center levels / regular spacing.
    # yt may include extra minor/reference primitives; select four with ~32.77pt regular spacing.
    best=None
    from itertools import combinations
    for comb in combinations(yt,4):
        ys=sorted([q['y'] for q in comb])
        ds=[ys[j+1]-ys[j] for j in range(3)]
        score=max(ds)-min(ds)
        if best is None or score<best[0]:best=(score,comb,ys,ds)
    if best is None or best[0]>0.2: raise RuntimeError(f'Cannot isolate regular y major ticks: {yt}')
    # sorted y top->bottom correspond values 6,4,2,0
    ymaj=sorted(best[1],key=lambda z:z['y']); yvals=[6.0,4.0,2.0,0.0]

    # Linear least-squares closed form.
    def linfit(xs,vs):
        n=len(xs);mx=sum(xs)/n;mv=sum(vs)/n
        b=sum((x-mx)*(v-mv) for x,v in zip(xs,vs))/sum((x-mx)**2 for x in xs)
        a=mv-b*mx
        resid=[v-(a+b*x) for x,v in zip(xs,vs)]
        return a,b,resid
    ax,bx,xres=linfit([q['x'] for q in xmaj],xvals)
    ay,by,yres=linfit([q['y'] for q in ymaj],yvals)
    pts=[]
    for j,m in enumerate(markers):
        r_kpc=ax+bx*m['x'];sig=ay+by*m['y']
        pts.append({'index':j,'pdf_x':m['x'],'pdf_y':m['y'],'radius_kpc_source':r_kpc,'sigma_hi_msun_pc2':sig})
    # Native marker x-grid QC.
    dxx=[markers[i+1]['x']-markers[i]['x'] for i in range(len(markers)-1)]
    med=sorted(dxx)[len(dxx)//2]; grid_dev=max(abs(v-med) for v in dxx)
    # HIX source distance explicitly published in Table 1.
    source_distance=23.06
    # Convert source physical radii to angular radii to preserve distance-independence.
    arcsec_per_kpc=206265.0/(source_distance*1000.0)
    for q in pts:q['radius_arcsec']=q['radius_kpc_source']*arcsec_per_kpc
    frozen=load_frozen_distance()
    for q in pts:
        q['radius_kpc_frozen']=None
        if frozen:
            # use first authoritative hit, preserve full hit list in audit
            q['radius_kpc_frozen']=q['radius_arcsec']*(frozen[0]['value']*1000.0)/206265.0
    PROFILE.parent.mkdir(parents=True,exist_ok=True)
    fields=['galaxy','stationary_role','source_reference','source_product','source_distance_mpc','radius_arcsec','radius_kpc_source','radius_kpc_frozen','sigma_hi_msun_pc2','helium_included','extraction_method','pdf_x','pdf_y']
    with PROFILE.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for q in pts:
            w.writerow({'galaxy':'NGC0289','stationary_role':'calibration','source_reference':'Lutz_et_al_2018_HIX_II_arXiv1802.04043','source_product':'Figure_A3_panel_b_measured_radial_HI_column_density','source_distance_mpc':source_distance,'radius_arcsec':f"{q['radius_arcsec']:.8f}",'radius_kpc_source':f"{q['radius_kpc_source']:.8f}",'radius_kpc_frozen':'' if q['radius_kpc_frozen'] is None else f"{q['radius_kpc_frozen']:.8f}",'sigma_hi_msun_pc2':f"{q['sigma_hi_msun_pc2']:.8f}",'helium_included':'0','extraction_method':'source_native_PDF_vector_marker_centers_linear_native_tick_calibration','pdf_x':f"{q['pdf_x']:.6f}",'pdf_y':f"{q['pdf_y']:.6f}"})
    audit={'status':'HIX2018_NGC0289_NATIVE_VECTOR_HI_PROFILE_RECOVERED','galaxy':'NGC0289','stationary_role':'calibration','n_points':len(pts),
           'source':{'url':final,'package_sha256':sha(payload),'pdf_member':PDF_MEMBER,'pdf_sha256':sha(pdf),'distance_mpc':source_distance},
           'profile_semantics':{'quantity':'deprojected H I column/surface density','helium_included':False,'observational_status':'measured_from_elliptical_annuli_in_non_clipped_ATCA_moment0_map','geometry':'annulus inclination and PA from extrapolated TiRiFiC profiles'},
           'x_axis':{'ticks':xmaj,'values_kpc':xvals,'intercept':ax,'slope_kpc_per_pdf_pt':bx,'residuals_kpc':xres,'max_abs_residual_kpc':max(abs(x) for x in xres)},
           'y_axis':{'ticks':ymaj,'values_msun_pc2':yvals,'intercept':ay,'slope_msun_pc2_per_pdf_pt':by,'residuals':yres,'max_abs_residual':max(abs(x) for x in yres)},
           'marker_grid':{'median_dx_pdf_pt':med,'max_abs_dx_deviation_pdf_pt':grid_dev},
           'ranges':{'radius_kpc_source':[min(q['radius_kpc_source'] for q in pts),max(q['radius_kpc_source'] for q in pts)],'radius_arcsec':[min(q['radius_arcsec'] for q in pts),max(q['radius_arcsec'] for q in pts)],'sigma_hi_msun_pc2':[min(q['sigma_hi_msun_pc2'] for q in pts),max(q['sigma_hi_msun_pc2'] for q in pts)]},
           'frozen_distance_hits':frozen,'text_evidence':extract_text_context(tex),
           'boundary':'Public later direct ATCA profile; native vector extraction only. No raster digitization. L_A and C_A remain locked.',
           'output':str(PROFILE)}
    AUDIT.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    CAL.write_text('\n'.join([f"status={audit['status']}",f"n_points={len(pts)}",f"x_ticks={xmaj}",f"x_values_kpc={xvals}",f"x_fit={ax:.12g}+({bx:.12g})*x max_resid={audit['x_axis']['max_abs_residual_kpc']:.3g}",f"y_ticks={ymaj}",f"y_values_msun_pc2={yvals}",f"y_fit={ay:.12g}+({by:.12g})*y max_resid={audit['y_axis']['max_abs_residual']:.3g}",f"marker_dx_median={med:.8f} max_dev={grid_dev:.8f}",f"source_distance_mpc={source_distance}",f"frozen_distance_hits={json.dumps(frozen)}",f"ranges={json.dumps(audit['ranges'])}",'quantity=raw_HI helium_included=0','method=measured_from_non_clipped_ATCA_moment0_map_in_elliptical_annuli; geometry from TiRiFiC inclination/PA','No OCR or raster digitization.'])+'\n',encoding='utf-8')
    print(json.dumps({'status':audit['status'],'n_points':len(pts),'x_ticks':xmaj,'y_ticks':ymaj,'ranges':audit['ranges'],'frozen_distance_hits':frozen,'outputs':[str(PROFILE),str(AUDIT),str(CAL)]},indent=2))
if __name__=='__main__':main()
