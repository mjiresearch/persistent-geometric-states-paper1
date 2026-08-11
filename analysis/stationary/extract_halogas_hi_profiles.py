#!/usr/bin/env python3
"""Extract HALOGAS DR1 radial HI profiles with the frozen public-map method."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS

NHI_PER_MSUN_PC2=1.249e20
NEW_TARGETS=("NGC0891","NGC1003","NGC5585","UGC04278")

def squeeze_image(data):
    x=np.asarray(data,dtype=float)
    while x.ndim>2:x=x[0]
    if x.ndim!=2:raise ValueError(f"Expected 2-D image, got {x.shape}")
    return x

def beam_arcsec(h):
    a=abs(float(h.get("BMAJ",np.nan)))*3600.;b=abs(float(h.get("BMIN",np.nan)))*3600.
    if not np.isfinite(a) or not np.isfinite(b):raise ValueError("missing BMAJ/BMIN")
    return a,b

def pixel_scale_arcsec(h):
    m=WCS(h).celestial.pixel_scale_matrix
    return float(np.sqrt(np.sum(m[:,0]**2))*3600),float(np.sqrt(np.sum(m[:,1]**2))*3600)

def robust_geometry(image,threshold_fraction=.03):
    z=np.where(np.isfinite(image)&(image>0),image,0.)
    if (z>0).sum()<20:raise ValueError("Too few positive HI pixels")
    z=np.where(z>=threshold_fraction*np.nanmax(z),z,0.);yy,xx=np.indices(z.shape);wt=z.sum()
    xc=float((z*xx).sum()/wt);yc=float((z*yy).sum()/wt);dx,dy=xx-xc,yy-yc
    vals,vecs=np.linalg.eigh([[float((z*dx*dx).sum()/wt),float((z*dx*dy).sum()/wt)],[float((z*dx*dy).sum()/wt),float((z*dy*dy).sum()/wt)]])
    v=vecs[:,np.argmax(vals)];return xc,yc,float(np.degrees(np.arctan2(v[1],v[0])))

def column_density_to_sigma_hi(image,h):
    pos=image[np.isfinite(image)&(image>0)];med=float(np.nanmedian(pos)) if pos.size else np.nan
    # HALOGAS *_coldens.fits values are physical N_HI despite a stale inherited BUNIT.
    if not np.isfinite(med) or med<=1e15:raise ValueError(f"column-density scale not physical; median={med}")
    return image/NHI_PER_MSUN_PC2

def extract(image,h,inc_deg,dist_mpc,central_beams=2.,annulus_beams=.5):
    if abs(np.cos(np.deg2rad(inc_deg)))<.08:raise ValueError(f"edge_on_thin_annulus_invalid:i={inc_deg}")
    sig=column_density_to_sigma_hi(image,h);sx,sy=pixel_scale_arcsec(h);ba,bb=beam_arcsec(h);beam=np.sqrt(ba*bb)
    xc,yc,pa=robust_geometry(image);yy,xx=np.indices(image.shape);dx=(xx-xc)*sx;dy=(yy-yc)*sy;t=np.deg2rad(pa)
    xp=dx*np.cos(t)+dy*np.sin(t);yp=-dx*np.sin(t)+dy*np.cos(t);rell_as=np.sqrt(xp*xp+(yp/np.cos(np.deg2rad(inc_deg)))**2)
    k=dist_mpc*1e3/206265.;rell=rell_as*k;mask=central_beams*beam*k;dr=annulus_beams*beam*k;valid=np.isfinite(sig)&(sig>=0)
    edges=np.arange(0,np.nanmax(rell[valid])+dr,dr);rows=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        m=(rell>=lo)&(rell<hi);s=sig[m&valid]
        if m.sum()<10:continue
        rows.append({"r_kpc":.5*(lo+hi),"Sigma_HI_Msun_pc2":float(np.nanmedian(s)) if s.size else np.nan,"Sigma_HI_p16":float(np.nanpercentile(s,16)) if s.size else np.nan,"Sigma_HI_p84":float(np.nanpercentile(s,84)) if s.size else np.nan,"n_pix_mom0":int(s.size),"beam_smeared_mask":bool(.5*(lo+hi)<mask)})
    return pd.DataFrame(rows),{"center_x_pix":xc,"center_y_pix":yc,"pa_pixel_deg":pa,"inclination_deg":inc_deg,"distance_mpc":dist_mpc,"beam_arcsec":beam,"central_mask_kpc":mask,"annulus_width_kpc":dr,"BUNIT_header":str(h.get("BUNIT","")),"unit_qc":"coldens_values_physical_NHI_header_BUNIT_stale"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--fits-dir",type=Path,required=True);p.add_argument("--manifest",type=Path,required=True);p.add_argument("--master",type=Path,required=True);p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args()
    man=pd.read_csv(a.manifest);master=pd.read_csv(a.master);a.out_dir.mkdir(parents=True,exist_ok=True);allp=[];qc=[]
    for gal in NEW_TARGETS:
        mr=man[man.galaxy==gal];gr=master[master.galaxy==gal]
        if mr.empty or gr.empty:raise ValueError(f"missing manifest/master row for {gal}")
        inc=float(gr.iloc[0].inclination_deg);dist=float(gr.iloc[0].distance_mpc);fn=str(mr.iloc[0].filename)
        with fits.open(a.fits_dir/fn) as hd:image=squeeze_image(hd[0].data);h=hd[0].header.copy()
        base={"name":gal,"source_file":fn,"inclination_deg":inc,"distance_mpc":dist,"BUNIT_header":str(h.get("BUNIT","")),"image_median_positive":float(np.nanmedian(image[np.isfinite(image)&(image>0)]))}
        try:
            prof,meta=extract(image,h,inc,dist);prof.insert(0,"name",gal);prof["source_family"]="HALOGAS_DR1_v2";prof["source_file"]=fn;allp.append(prof);qc.append({**base,**meta,"qc_status":"extracted"})
        except ValueError as e:
            qc.append({**base,"qc_status":"excluded_from_thin_annulus_extraction","qc_reason":str(e)})
            print(gal,"QC EXCLUSION",e)
    profiles=pd.concat(allp,ignore_index=True) if allp else pd.DataFrame();profiles.to_csv(a.out_dir/"halogas_direct_hi_annular_profiles.csv",index=False);pd.DataFrame(qc).to_csv(a.out_dir/"halogas_geometry_and_header_qc.csv",index=False)
    if len(profiles):
        clean=profiles[(~profiles.beam_smeared_mask)&np.isfinite(profiles.Sigma_HI_Msun_pc2)];print("clean profile bins by galaxy:");print(clean.groupby("name").size().to_string())
    print(pd.DataFrame(qc)[["name","qc_status"]].to_string(index=False))
if __name__=="__main__":main()
