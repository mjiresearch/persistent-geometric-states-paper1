#!/usr/bin/env python3
"""Extract radial HI profiles from public HALOGAS DR1 column-density maps.

Geometry and binning are intentionally identical to the previously frozen
THINGS/LITTLE THINGS annular extractor:
- weighted map centroid/major-axis PA fallback;
- frozen SPARC inclination and distance;
- elliptical deprojection;
- central mask = 2.0 geometric-mean beam FWHM;
- annulus width = 0.5 beam FWHM;
- median and p16/p84 HI surface density per annulus;
- no interpolation/extrapolation in this extraction layer.

HALOGAS *_coldens.fits products already encode HI column density, so this file
only converts N_HI [atoms cm^-2] to hydrogen-only Sigma_HI [Msun pc^-2].
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS

NHI_PER_MSUN_PC2 = 1.249e20
NEW_TARGETS = ("NGC0891", "NGC1003", "NGC5585", "UGC04278")


def squeeze_image(data):
    x=np.asarray(data,dtype=float)
    while x.ndim>2: x=x[0]
    if x.ndim!=2: raise ValueError(f"Expected 2-D image, got {x.shape}")
    return x


def beam_arcsec(h):
    bmaj=abs(float(h.get("BMAJ",np.nan)))*3600.; bmin=abs(float(h.get("BMIN",np.nan)))*3600.
    if not np.isfinite(bmaj) or not np.isfinite(bmin): raise ValueError("missing BMAJ/BMIN")
    return bmaj,bmin


def pixel_scale_arcsec(h):
    w=WCS(h).celestial; mat=w.pixel_scale_matrix
    sx=np.sqrt(np.sum(mat[:,0]**2))*3600.; sy=np.sqrt(np.sum(mat[:,1]**2))*3600.
    return float(sx),float(sy)


def robust_geometry(image,threshold_fraction=0.03):
    z=np.where(np.isfinite(image)&(image>0),image,0.)
    if (z>0).sum()<20: raise ValueError("Too few positive HI pixels")
    z=np.where(z>=threshold_fraction*np.nanmax(z),z,0.)
    yy,xx=np.indices(z.shape); wt=z.sum()
    xc=float((z*xx).sum()/wt); yc=float((z*yy).sum()/wt)
    dx,dy=xx-xc,yy-yc
    cxx=float((z*dx*dx).sum()/wt); cyy=float((z*dy*dy).sum()/wt); cxy=float((z*dx*dy).sum()/wt)
    vals,vecs=np.linalg.eigh([[cxx,cxy],[cxy,cyy]])
    major=vecs[:,np.argmax(vals)]
    return xc,yc,float(np.degrees(np.arctan2(major[1],major[0])))


def column_density_to_sigma_hi(image,h):
    """Convert HALOGAS column-density image to Msun pc^-2, HI only.

    The workflow records BUNIT and data range before this routine runs. We
    accept explicit atoms/cm^2-style units or dimensionless maps whose finite
    positive median is plainly in physical column-density scale (>1e15).
    """
    unit=str(h.get("BUNIT","")).strip().lower().replace(" ","")
    finite=image[np.isfinite(image)&(image>0)]
    med=float(np.nanmedian(finite)) if finite.size else np.nan
    physical = ("cm" in unit and ("atom" in unit or "hi" in unit or "n" in unit)) or (np.isfinite(med) and med>1e15)
    if not physical:
        raise ValueError(f"Unrecognized HALOGAS column-density scale: BUNIT={h.get('BUNIT')!r}, median={med:g}")
    return image/NHI_PER_MSUN_PC2


def extract(image,h,inclination_deg,distance_mpc,central_beams=2.0,annulus_beams=0.5):
    sig=column_density_to_sigma_hi(image,h)
    sx,sy=pixel_scale_arcsec(h); bmaj,bmin=beam_arcsec(h); beam=np.sqrt(bmaj*bmin)
    xc,yc,pa=robust_geometry(image)
    yy,xx=np.indices(image.shape); dx=(xx-xc)*sx; dy=(yy-yc)*sy
    th=np.deg2rad(pa); xp=dx*np.cos(th)+dy*np.sin(th); yp=-dx*np.sin(th)+dy*np.cos(th)
    inc=np.deg2rad(inclination_deg)
    if abs(np.cos(inc))<0.08:
        raise ValueError(f"inclination {inclination_deg} deg too close to edge-on for thin-annulus deprojection")
    rell_arcsec=np.sqrt(xp*xp+(yp/np.cos(inc))**2)
    kpc_per_arcsec=distance_mpc*1e3/206265.; rell=rell_arcsec*kpc_per_arcsec
    mask_radius=central_beams*beam*kpc_per_arcsec; dr=annulus_beams*beam*kpc_per_arcsec
    valid=np.isfinite(sig)&(sig>=0)
    rmax=np.nanmax(rell[valid]); edges=np.arange(0,rmax+dr,dr); rows=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        m=(rell>=lo)&(rell<hi); s=sig[m&valid]
        if m.sum()<10: continue
        rows.append({"r_kpc":0.5*(lo+hi),"Sigma_HI_Msun_pc2":float(np.nanmedian(s)) if s.size else np.nan,
                     "Sigma_HI_p16":float(np.nanpercentile(s,16)) if s.size else np.nan,
                     "Sigma_HI_p84":float(np.nanpercentile(s,84)) if s.size else np.nan,
                     "n_pix_mom0":int(s.size),"beam_smeared_mask":bool(0.5*(lo+hi)<mask_radius)})
    return pd.DataFrame(rows), {"center_x_pix":xc,"center_y_pix":yc,"pa_pixel_deg":pa,"inclination_deg":inclination_deg,
                                "distance_mpc":distance_mpc,"beam_arcsec":beam,"central_mask_kpc":mask_radius,
                                "annulus_width_kpc":dr,"BUNIT":str(h.get("BUNIT",""))}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--fits-dir",type=Path,required=True); ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--master",type=Path,required=True); ap.add_argument("--out-dir",type=Path,required=True); a=ap.parse_args()
    man=pd.read_csv(a.manifest); master=pd.read_csv(a.master); a.out_dir.mkdir(parents=True,exist_ok=True)
    allp=[]; metas=[]
    for gal in NEW_TARGETS:
        mr=man[man.galaxy==gal]
        if mr.empty: raise ValueError(f"{gal} absent from HALOGAS manifest")
        gr=master[master.galaxy==gal]
        if gr.empty: raise ValueError(f"{gal} absent from frozen master")
        row=gr.iloc[0]; inc=float(row["inclination_deg"]); dist=float(row["distance_mpc"])
        fn=str(mr.iloc[0].filename); p=a.fits_dir/fn
        with fits.open(p) as hd: image=squeeze_image(hd[0].data); h=hd[0].header.copy()
        prof,meta=extract(image,h,inc,dist); prof.insert(0,"name",gal); prof["source_family"]="HALOGAS_DR1_v2"; prof["source_file"]=fn
        meta.update({"name":gal,"source_file":fn,"image_min":float(np.nanmin(image)),"image_median_positive":float(np.nanmedian(image[np.isfinite(image)&(image>0)])),"image_max":float(np.nanmax(image))})
        allp.append(prof); metas.append(meta)
    pd.concat(allp,ignore_index=True).to_csv(a.out_dir/"halogas_direct_hi_annular_profiles.csv",index=False)
    pd.DataFrame(metas).to_csv(a.out_dir/"halogas_geometry_and_header_qc.csv",index=False)
    clean=pd.concat(allp,ignore_index=True); clean=clean[(~clean.beam_smeared_mask)&np.isfinite(clean.Sigma_HI_Msun_pc2)]
    print("clean profile bins by galaxy:")
    print(clean.groupby("name").size().to_string())

if __name__=="__main__": main()
