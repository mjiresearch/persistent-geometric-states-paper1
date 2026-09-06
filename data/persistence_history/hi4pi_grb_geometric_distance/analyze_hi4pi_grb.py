#!/usr/bin/env python3
"""First raw-data test of GRB geometric distances against HI4PI H I kinematics.

The script:
  * reads the aperture-averaged HI4PI spectra,
  * detects significant H I components without hand-picking a velocity,
  * evaluates the Reid et al. (2019) universal rotation curve at each direct
    X-ray dust distance,
  * associates the closest significant H I component to each predicted arm
    velocity (explicitly flagged as model-guided association), and
  * writes peak tables, residuals, plots, and a compact machine-readable verdict.

This is a screening test, not a final persistence detection test.  A few-km/s
residual is comparable to ordinary non-circular Galactic motions and must be
challenged with streaming/warp models before gravitational interpretation.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths

R0_KPC = 8.15
THETA0_KMS = 236.0
A2 = 0.96
A3 = 1.62

TARGETS = {
    "GRB_221009A": (52.96, 4.32),
    "GRB_160623A": (84.17, -2.69),
    "GRB_031203": (255.74, -4.80),
}

STRUCTURES = [
    {"target":"GRB_221009A", "arm":"Outer", "distance_kpc":13.9, "distance_sigma_kpc":0.1},
    {"target":"GRB_221009A", "arm":"OSC",   "distance_kpc":19.0, "distance_sigma_kpc":0.2},
    {"target":"GRB_160623A", "arm":"Outer", "distance_kpc":9.9, "distance_sigma_kpc":0.6},
    {"target":"GRB_031203",  "arm":"Outer", "distance_kpc":9.7, "distance_sigma_kpc":0.4},
]


def urc_shape(R_kpc: float) -> float:
    """Persic-style URC shape used by Reid+2019, normalized later at R0."""
    lam = (A3 / 1.5) ** 5
    beta = 0.72 + 0.44 * np.log10(lam)
    x = np.asarray(R_kpc, float) / (A2 * R0_KPC)
    disk = beta * 1.97 * x**1.22 / (x*x + 0.78**2)**1.43
    halo = 1.6 * np.exp(-0.4*lam) * x*x / (x*x + 1.5**2 * lam**0.4)
    return np.sqrt(disk + halo)

_URC0 = float(urc_shape(R0_KPC))


def theta_reid(R_kpc: float) -> float:
    return float(THETA0_KMS * urc_shape(R_kpc) / _URC0)


def geometry(distance_kpc: float, l_deg: float, b_deg: float):
    l = math.radians(l_deg); b = math.radians(b_deg)
    dp = distance_kpc * math.cos(b)
    R = math.sqrt(R0_KPC**2 + dp**2 - 2*R0_KPC*dp*math.cos(l))
    return R


def vlsr_reid(distance_kpc: float, l_deg: float, b_deg: float) -> float:
    l = math.radians(l_deg); b = math.radians(b_deg)
    R = geometry(distance_kpc, l_deg, b_deg)
    return (theta_reid(R) * R0_KPC / R - THETA0_KMS) * math.sin(l) * math.cos(b)


def gaussian(v, amp, cen, sig, base):
    return base + amp*np.exp(-0.5*((v-cen)/sig)**2)


def robust_noise(v, t):
    edge = np.abs(v) > 250
    if edge.sum() < 30:
        edge = np.abs(v) > np.nanpercentile(np.abs(v), 75)
    x = t[edge]
    med = float(np.nanmedian(x))
    mad = float(np.nanmedian(np.abs(x-med)))
    return med, max(1.4826*mad, 0.02)


def detect_components(v, t):
    order = np.argsort(v); v = v[order]; t = t[order]
    baseline, noise = robust_noise(v, t)
    y = gaussian_filter1d(np.nan_to_num(t-baseline, nan=0.0), 1.0)
    dv = float(np.nanmedian(np.diff(v)))
    min_prom = max(0.30, 5.0*noise)
    min_height = max(0.35, 5.0*noise)
    idx, props = find_peaks(y, prominence=min_prom, height=min_height,
                            distance=max(2, int(round(2.0/max(abs(dv),1e-3)))))
    widths = peak_widths(y, idx, rel_height=0.5)[0] * abs(dv) if len(idx) else np.array([])
    rows=[]
    for j,i in enumerate(idx):
        cen0=float(v[i]); amp0=float(max(y[i],0.05)); fwhm0=float(max(widths[j],1.0))
        win=np.abs(v-cen0)<=max(8.0,1.5*fwhm0)
        cen=cen0; sig=max(fwhm0/2.355,1.0); amp=amp0; base0=baseline
        try:
            popt,_=curve_fit(gaussian,v[win],t[win],p0=[amp0,cen0,sig,baseline],
                bounds=([0,cen0-5,0.3,-np.inf],[np.inf,cen0+5,30,np.inf]),maxfev=10000)
            amp,cen,sig,base0=map(float,popt)
        except Exception:
            pass
        rows.append({"velocity_kms":cen,"amplitude_K":amp,"sigma_kms":sig,
                     "fwhm_kms":2.355*sig,"prominence_K":float(props['prominences'][j]),
                     "baseline_K":base0,"noise_K":noise})
    return pd.DataFrame(rows).sort_values("velocity_kms").reset_index(drop=True), baseline, noise


def distance_mc_velocity(d, dsig, l, b, n=20000, seed=42):
    rng=np.random.default_rng(seed)
    draw=rng.normal(d,dsig,n); draw=draw[draw>0]
    vv=np.array([vlsr_reid(float(x),l,b) for x in draw])
    return float(np.std(vv,ddof=1))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",required=True)
    ap.add_argument("--out-dir",required=True)
    args=ap.parse_args()
    data=Path(args.data_dir); out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)

    all_peaks=[]; spectra={}; noise_meta={}
    for target,(l,b) in TARGETS.items():
        p=data/f"{target}_hi4pi_aperture.csv"
        df=pd.read_csv(p)
        v=df["velocity_lsr_km_s"].to_numpy(float); t=df["brightness_temperature_K"].to_numpy(float)
        spectra[target]=(v,t)
        peaks,base,noise=detect_components(v,t)
        peaks.insert(0,"target",target)
        peaks.to_csv(out/f"{target}_components.csv",index=False)
        all_peaks.append(peaks)
        noise_meta[target]={"baseline_K":base,"noise_K":noise,"n_components":int(len(peaks))}

    peaks_all=pd.concat(all_peaks,ignore_index=True)
    peaks_all.to_csv(out/"all_detected_components.csv",index=False)

    residuals=[]
    for k,s in enumerate(STRUCTURES):
        target=s["target"]; l,b=TARGETS[target]
        R=geometry(s["distance_kpc"],l,b)
        vpred=vlsr_reid(s["distance_kpc"],l,b)
        sigpred=distance_mc_velocity(s["distance_kpc"],s["distance_sigma_kpc"],l,b,seed=100+k)
        cand=peaks_all[peaks_all.target==target].copy()
        # Restrict to the outer-Galaxy sign when possible, then take nearest detected component.
        sign=-1 if 0 < (l%360) < 180 else +1
        signed=cand[cand.velocity_kms*sign>5]
        if len(signed): cand=signed
        cand["abs_delta"]=(cand.velocity_kms-vpred).abs()
        best=cand.sort_values(["abs_delta","prominence_K"],ascending=[True,False]).iloc[0]
        vobs=float(best.velocity_kms)
        dv=vobs-vpred
        residuals.append({
            **s,"l_deg":l,"b_deg":b,"R_gal_kpc":R,"theta_reid_kms":theta_reid(R),
            "v_reid_at_geometric_distance_kms":vpred,"v_reid_sigma_from_distance_kms":sigpred,
            "v_hi_component_kms":vobs,"component_fwhm_kms":float(best.fwhm_kms),
            "component_prominence_K":float(best.prominence_K),"delta_v_obs_minus_reid_kms":dv,
            "abs_delta_v_kms":abs(dv),"association":"nearest significant outer-sign component (model-guided screening)"
        })

    res=pd.DataFrame(residuals)
    res.to_csv(out/"geometric_kinematic_residuals.csv",index=False)

    # Plots are diagnostics, not used for peak selection.
    import matplotlib.pyplot as plt
    for target,(v,t) in spectra.items():
        fig,ax=plt.subplots(figsize=(9,4.8))
        m=np.abs(v)<=180
        ax.plot(v[m],t[m],lw=1)
        pks=peaks_all[peaks_all.target==target]
        for _,r in pks.iterrows():
            if abs(r.velocity_kms)<=180:
                ax.axvline(r.velocity_kms,alpha=.18,lw=.8)
        rr=res[res.target==target]
        for _,r in rr.iterrows():
            ax.axvline(r.v_reid_at_geometric_distance_kms,ls='--',lw=1.3,
                       label=f"Reid @ {r.arm} X-ray d: {r.v_reid_at_geometric_distance_kms:.1f}")
            ax.axvline(r.v_hi_component_kms,ls=':',lw=1.3,
                       label=f"matched H I: {r.v_hi_component_kms:.1f}")
        ax.set_xlabel("LSR velocity (km/s)"); ax.set_ylabel("Brightness temperature (K)")
        ax.set_title(f"{target}: aperture-averaged HI4PI spectrum")
        ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig(out/f"{target}_spectrum_test.png",dpi=160); plt.close(fig)

    # Screening classification relative to ordinary ~10 km/s non-circular scale.
    n_over10=int((res.abs_delta_v_kms>10).sum())
    verdict={
        "test":"HI4PI GRB geometric-distance / kinematic-residual screening",
        "model":"Reid et al. 2019 URC (R0=8.15 kpc, Theta0=236 km/s, a2=0.96, a3=1.62)",
        "association_caveat":"Component association is model-guided and must be replaced by a frozen arm/component rule for a confirmatory test.",
        "residuals_kms":res[["target","arm","delta_v_obs_minus_reid_kms"]].to_dict("records"),
        "max_abs_residual_kms":float(res.abs_delta_v_kms.max()),
        "n_abs_residual_gt_10_kms":n_over10,
        "screening_interpretation":("At least one residual exceeds 10 km/s; inspect streaming/warp controls before any persistence inference."
            if n_over10 else "All matched residuals are within 10 km/s; this raw screening run does not separate Persistence from ordinary non-circular motion."),
        "noise":noise_meta,
    }
    (out/"screening_verdict.json").write_text(json.dumps(verdict,indent=2))
    (out/"screening_verdict.txt").write_text(json.dumps(verdict,indent=2)+"\n")
    print(res.to_string(index=False))
    print(json.dumps(verdict,indent=2))


if __name__=="__main__":
    main()
