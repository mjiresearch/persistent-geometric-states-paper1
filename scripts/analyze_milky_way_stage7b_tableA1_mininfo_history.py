#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT=Path('data/persistence_history/milky_way_stage7b_tableA1_mininfo_history')
OUT.mkdir(parents=True,exist_ok=True)
SRC=Path('data/external/ratcliffe2026_sfh/ratcliffe2026_tableA1_global_disc_history.csv')
R=np.linspace(0.001,25.0,5000)
REFF_TO_RD=1.6783469900166605


def trapz(y,x): return np.trapezoid(y,x)
def sigma_exp(total_mass_msun,reff_kpc):
    rd=reff_kpc/REFF_TO_RD
    return total_mass_msun/(2*np.pi*rd**2)*np.exp(-R/rd)
def enclosed_half_radius(sig):
    shell=2*np.pi*R*sig
    c=np.concatenate([[0.0],np.cumsum(0.5*(shell[1:]+shell[:-1])*np.diff(R))])
    if c[-1]<=0:return np.nan
    return float(np.interp(0.5*c[-1],c,R))
def integrated_mass(sig): return float(trapz(2*np.pi*R*sig,R))

def main():
    d=pd.read_csv(SRC).sort_values('lookback_time_gyr',ascending=False).reset_index(drop=True)
    profiles=[]
    for _,row in d.iterrows():
        m=float(row.stellar_mass_1e10_msun)*1e10
        sb=sigma_exp(m,float(row.Reff_birth_radius_kpc))
        sc=sigma_exp(m,float(row.Reff_current_radius_kpc))
        profiles.append({'lookback_time_gyr':float(row.lookback_time_gyr),'mass_msun':m,'birth':sb,'current':sc})
    interval_rows=[]
    grid_rows=[]
    for i in range(len(profiles)-1):
        old=profiles[i];young=profiles[i+1]
        dt=old['lookback_time_gyr']-young['lookback_time_gyr']
        dm=young['mass_msun']-old['mass_msun']
        ds=young['birth']-old['birth']
        pos=np.clip(ds,0,None);neg=np.clip(-ds,0,None)
        mpos=integrated_mass(pos);mneg=integrated_mass(neg);mnet=integrated_mass(ds)
        neg_frac_abs=float(mneg/(mpos+mneg)) if (mpos+mneg)>0 else 0.0
        neg_frac_net=float(mneg/max(abs(mnet),1e-30))
        rzero=[]
        sign=np.sign(ds)
        crossings=np.where(sign[:-1]*sign[1:]<0)[0]
        for k in crossings:
            rzero.append(float(np.interp(0,[ds[k],ds[k+1]],[R[k],R[k+1]])))
        ro=d.iloc[i];ry=d.iloc[i+1]
        sfr_mean=0.5*(float(ro.SFR_msun_per_yr)+float(ry.SFR_msun_per_yr))
        surviving_growth_rate=dm/(dt*1e9)
        interval_rows.append({
            'older_lookback_gyr':old['lookback_time_gyr'],'younger_lookback_gyr':young['lookback_time_gyr'],'interval_gyr':dt,
            'older_mass_1e10_msun':old['mass_msun']/1e10,'younger_mass_1e10_msun':young['mass_msun']/1e10,'net_mass_growth_1e10_msun':dm/1e10,
            'net_mass_growth_rate_msun_per_yr':surviving_growth_rate,'mean_endpoint_published_SFR_msun_per_yr':sfr_mean,
            'growth_rate_over_endpoint_SFR':float(surviving_growth_rate/sfr_mean) if sfr_mean>0 else np.nan,
            'positive_increment_mass_1e10_msun':mpos/1e10,'negative_increment_abs_mass_1e10_msun':mneg/1e10,
            'negative_fraction_of_abs_profile_change':neg_frac_abs,'negative_mass_over_net_growth':neg_frac_net,
            'positive_increment_half_mass_radius_kpc':enclosed_half_radius(pos),'zero_crossing_radii_kpc':';'.join(f'{x:.3f}' for x in rzero),
            'older_birth_Reff_kpc':float(ro.Reff_birth_radius_kpc),'younger_birth_Reff_kpc':float(ry.Reff_birth_radius_kpc)
        })
        for rr,ss in zip(R[::25],ds[::25]):
            grid_rows.append({'older_lookback_gyr':old['lookback_time_gyr'],'younger_lookback_gyr':young['lookback_time_gyr'],'R_kpc':float(rr),'delta_surface_density_msun_per_kpc2':float(ss),'delta_SFR_surface_proxy_msun_per_yr_kpc2':float(ss/(dt*1e9))})
    intervals=pd.DataFrame(interval_rows)
    intervals.to_csv(OUT/'minimum_information_birth_profile_increments.csv',index=False)
    pd.DataFrame(grid_rows).to_csv(OUT/'minimum_information_birth_profile_increment_grid.csv',index=False)

    bad_abs=(intervals.negative_fraction_of_abs_profile_change>0.05)
    bad_net=(intervals.negative_mass_over_net_growth>0.10)
    report={
        'analysis_name':'Milky Way Stage 7B minimum-information source-history sufficiency test from Ratcliffe2026 Table A.1',
        'force_or_pulsar_data_used':False,
        'construction':{
            'assumption':'At each published epoch, approximate the cumulative stellar mass distribution in birth-radius coordinates as a 2D exponential disk with total mass Mstar(t) and half-mass radius equal to published Reff_birth(t).',
            'scale_length_rule':'Rd = Reff_birth / 1.67834699',
            'increment_rule':'Newly assembled birth-radius profile over an interval = younger cumulative exponential profile minus older cumulative exponential profile.',
            'physical_requirement':'A literal newly formed stellar-mass profile must be nonnegative at every radius. Negative differences diagnose insufficiency/inconsistency of reconstructing the full spatial SFH from Mstar+Reff alone, not negative star formation.'
        },
        'n_epochs':int(len(d)),'n_intervals':int(len(intervals)),
        'intervals_with_negative_abs_change_fraction_gt5pct':int(bad_abs.sum()),
        'intervals_with_negative_mass_gt10pct_of_net_growth':int(bad_net.sum()),
        'maximum_negative_fraction_of_abs_profile_change':float(intervals.negative_fraction_of_abs_profile_change.max()),
        'maximum_negative_mass_over_net_growth':float(intervals.negative_mass_over_net_growth.max()),
        'median_negative_fraction_of_abs_profile_change':float(intervals.negative_fraction_of_abs_profile_change.median()),
        'median_growth_rate_over_mean_endpoint_SFR':float(intervals.growth_rate_over_endpoint_SFR.median()),
        'worst_interval_by_negative_fraction':intervals.loc[intervals.negative_fraction_of_abs_profile_change.idxmax()].to_dict(),
        'verdict':('TABLE_A1_SUMMARIES_ARE_INSUFFICIENT_FOR_A_UNIQUE_PHYSICAL_SPATIAL_SFH' if bad_abs.any() else 'MINIMUM_INFORMATION_EXPONENTIAL_HISTORY_IS_NONNEGATIVE_UNDER_THIS_TEST'),
        'interpretation':('The test is deliberately source-side only. Even if every exponential difference were nonnegative, Table A.1 would still encode only an axisymmetric radial mass history and would not provide the azimuthal/current history required by the persistence framework. If appreciable negative increments occur, the actual mass-weighted Rbirth-by-time arrays are required before constructing a physical hereditary source field.'),
        'guardrails':['Mstar is the paper\'s tabulated stellar mass at each epoch; interval mass growth is not identical to initial mass formed because stellar mass loss and endpoint-vs-interval SFR definitions differ.','An exponential profile is the maximum-information compression chosen only to test sufficiency of Mstar+Reff; it is not claimed to be the authors\' actual reconstructed radial profile.','No force, pulsar residual, kernel lifetime, or persistence parameter is used or fit.']
    }
    (OUT/'stage7b_summary.json').write_text(json.dumps(report,indent=2,default=str))
    print(json.dumps(report,indent=2,default=str))
if __name__=='__main__':main()
# workflow trigger 2026-08-08
