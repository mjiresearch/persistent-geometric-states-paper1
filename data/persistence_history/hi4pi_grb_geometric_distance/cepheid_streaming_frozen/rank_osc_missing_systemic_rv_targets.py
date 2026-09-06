#!/usr/bin/env python3
"""Outcome-blind ranking of missing systemic-RV Cepheids for the frozen OSC field.

Reads no H I or Persistence outcome. See OSC_RV_TARGET_RANK_FREEZE.md.
"""
from __future__ import annotations
import importlib.util, itertools, json, math
from pathlib import Path
import numpy as np, pandas as pd

HERE=Path(__file__).resolve().parent
OUT=HERE/'osc_rv_target_rank'; OUT.mkdir(parents=True,exist_ok=True)
SIGMAS=[1.0,2.0,5.0]
PRIMARY=2.0
MC=512
SEED=20260924


def loadmod(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
v1=loadmod('v1_rank',HERE/'build_gaia_cepheid_streaming_v1.py')
v2=loadmod('v2_rank',HERE/'build_gaia_cepheid_streaming_v2.py')
v3=loadmod('v3_rank',HERE/'build_gaia_cepheid_streaming_v3.py')

TARGET=[t for t in v1.TARGETS if t['arm']=='OSC'][0]


def select_accepted_rv(r,veloce):
    sid=int(r.source_id); vr=veloce.get(sid)
    if vr is not None and vr['binflag']=='F' and vr['nrv']>=8:
        return ('veloce_dr1_vgamma',float(vr['vgamma']),1.0)
    if np.isfinite(r.average_rv) and np.isfinite(r.average_rv_error) and np.isfinite(r.num_clean_epochs_rv) and r.num_clean_epochs_rv>=8 and r.average_rv_error<=5:
        return ('gaia_vari_cepheid',float(r.average_rv),float(r.average_rv_error))
    if np.isfinite(r.radial_velocity) and np.isfinite(r.radial_velocity_error) and np.isfinite(r.rv_nb_transits) and r.rv_nb_transits>=8 and r.radial_velocity_error<=5:
        return ('gaia_source_rvs',float(r.radial_velocity),float(r.radial_velocity_error))
    if np.isfinite(r.melnik_rv) and np.isfinite(r.melnik_erv) and r.melnik_erv<=5:
        return ('melnik2015_hrv',float(r.melnik_rv),float(r.melnik_erv))
    return None


def nonrv_ok(r):
    vals=[r.pmra,r.pmra_error,r.pmdec,r.pmdec_error,r.ruwe,r.e_mu]
    return all(np.isfinite(vals)) and r.ruwe<1.4 and (math.log(10)/5*r.e_mu)<=0.20


def pos_and_arm(r,pt):
    x,y,z,R,_,_,_=v1.phase([r.ra],[r.dec],[r.Dist],[r.pmra],[r.pmdec],[0.0])
    phi=float(np.arctan2(y[0],x[0])); R=float(R[0])
    s,dp,_=v1.armcoords(np.array([R]),np.array([phi]),v1.OSC,pt)
    return R,phi,float(s[0]),float(dp[0])


def hypothetical_errors(r,sigma_rv):
    # Outcome-blind uncertainty propagation. RV perturbations are centered at 0;
    # the candidate's unknown systemic RV value is never read or assumed.
    rng=np.random.default_rng(SEED + (int(r.source_id) % 1000003) + int(100*sigma_rv))
    dm=rng.normal(0,float(r.e_mu),MC); dd=float(r.Dist)*10**(dm/5)
    pra=rng.normal(float(r.pmra),float(r.pmra_error),MC)
    pde=rng.normal(float(r.pmdec),float(r.pmdec_error),MC)
    rv=rng.normal(0.0,float(sigma_rv),MC)
    _,_,_,_,U,V,_=v1.phase(np.repeat(float(r.ra),MC),np.repeat(float(r.dec),MC),dd,pra,pde,rv)
    return float(np.std(U,ddof=1)),float(np.std(V,ddof=1))


def weights(d,h,comp):
    sig=d['e'+comp].to_numpy(float)
    return np.exp(-.5*(d.s.to_numpy(float)/h)**2)*np.exp(-.5*(d.dperp.to_numpy(float)/v1.OSC[2])**2)/(sig*sig+v1.SIGMA_INT**2)


def neff_from_w(w):
    w=np.asarray(w,float)
    return float(w.sum()**2/np.sum(w*w)) if len(w) and np.sum(w*w)>0 else 0.0


def added_neff(basew,neww):
    w=np.concatenate([np.asarray(basew,float),np.atleast_1d(neww).astype(float)])
    return neff_from_w(w)


def cweight(row,h,comp,sigma):
    e=row[f'e{comp}_{sigma:g}']
    if not np.isfinite(e) or e>20:return np.nan
    return math.exp(-.5*(row.s_phase_kpc/h)**2)*math.exp(-.5*(row.d_perp_kpc/v1.OSC[2])**2)/(e*e+v1.SIGMA_INT**2)


def main():
    v1.download(); ceps=v1.parse_ceps(); gen=v1.gaia_join(ceps.source_id.tolist())
    spec=v2.gaia_cepheid_join(ceps.source_id.tolist())
    keep=['source_id','average_rv','average_rv_error','num_clean_epochs_rv']
    df=ceps.merge(gen,on='source_id',how='inner').merge(spec[keep],on='source_id',how='left')
    mel=v3.melnik_catalog(); df=v3.attach_melnik(df,mel); veloce=v2.parse_veloce()
    existing=v3.build_sample(df,veloce)
    _,_,_,Rt,pt=v1.target_pos(TARGET)
    ex,_=v1.members(existing,'OSC',pt); ex.attrs['arm']='OSC'

    # Candidate pool: passes all non-RV and frozen OSC geometry rules, but no RV
    # passes the frozen hierarchy. Stars failing propagated-UV after an accepted RV
    # are explicitly not classified as missing-RV targets.
    cand=[]; other_fail=[]
    for _,r in df.iterrows():
        if not nonrv_ok(r): continue
        R,phi,s,dp=pos_and_arm(r,pt)
        if R<4 or abs(dp)>2*v1.OSC[2]: continue
        accepted=select_accepted_rv(r,veloce)
        if accepted is not None:
            if int(r.source_id) not in set(existing.source_id.astype(int)):
                other_fail.append(dict(source_id=int(r.source_id),R_kpc=R,phi_rad=phi,s_phase_kpc=s,d_perp_kpc=dp,accepted_rv_source=accepted[0],reason='accepted_RV_but_not_V3_eligible_likely_propagated_UV_error'))
            continue
        q=dict(source_id=int(r.source_id),ra_deg=float(r.ra),dec_deg=float(r.dec),GLON_deg=float(r.GLON),GLAT_deg=float(r.GLAT),Dist_kpc=float(r.Dist),e_mu_mag=float(r.e_mu),ruwe=float(r.ruwe),pmra=float(r.pmra),pmra_error=float(r.pmra_error),pmdec=float(r.pmdec),pmdec_error=float(r.pmdec_error),R_kpc=R,phi_rad=phi,s_phase_kpc=s,d_perp_kpc=dp,
               gaia_source_rv=float(r.radial_velocity) if np.isfinite(r.radial_velocity) else np.nan,
               gaia_source_rv_error=float(r.radial_velocity_error) if np.isfinite(r.radial_velocity_error) else np.nan,
               gaia_source_rv_transits=float(r.rv_nb_transits) if np.isfinite(r.rv_nb_transits) else np.nan,
               gaia_vari_rv=float(r.average_rv) if np.isfinite(r.average_rv) else np.nan,
               gaia_vari_rv_error=float(r.average_rv_error) if np.isfinite(r.average_rv_error) else np.nan,
               gaia_vari_rv_epochs=float(r.num_clean_epochs_rv) if np.isfinite(r.num_clean_epochs_rv) else np.nan,
               melnik_name=str(r.melnik_name) if isinstance(r.melnik_name,str) else '')
        for sig in SIGMAS:
            eU,eV=hypothetical_errors(r,sig); q[f'eU_{sig:g}']=eU; q[f'eV_{sig:g}']=eV
        cand.append(q)
    c=pd.DataFrame(cand)

    # Frozen existing support by bandwidth.
    base={}
    for h in v1.HGRID:
        base[float(h)]={}
        for comp in ['U','V']:
            w=weights(ex,float(h),comp); base[float(h)][comp]=dict(w=w,neff=neff_from_w(w))

    # Single-candidate support effects at all precision sensitivities.
    rows=[]
    for _,r in c.iterrows():
        z=r.to_dict()
        for sig in SIGMAS:
            best=(-np.inf,None,None,None); passes=[]
            for h in v1.HGRID:
                h=float(h); wu=cweight(r,h,'U',sig); wv=cweight(r,h,'V',sig)
                if not np.isfinite(wu) or not np.isfinite(wv): continue
                nU=added_neff(base[h]['U']['w'],wu); nV=added_neff(base[h]['V']['w'],wv); m=min(nU,nV)
                if m>best[0]:best=(m,h,nU,nV)
                if nU>=3 and nV>=3:passes.append(h)
            z[f'best_min_neff_sigmaRV_{sig:g}']=best[0] if np.isfinite(best[0]) else np.nan
            z[f'best_h_sigmaRV_{sig:g}']=best[1]
            z[f'best_neffU_sigmaRV_{sig:g}']=best[2]
            z[f'best_neffV_sigmaRV_{sig:g}']=best[3]
            z[f'passes_single_sigmaRV_{sig:g}']=bool(passes)
            z[f'passing_h_sigmaRV_{sig:g}']=';'.join(str(x) for x in passes)
        rows.append(z)
    rank=pd.DataFrame(rows)
    if len(rank):
        rank=rank.sort_values([f'passes_single_sigmaRV_{PRIMARY:g}',f'best_min_neff_sigmaRV_{PRIMARY:g}','s_phase_kpc'],ascending=[False,False,True])
        rank.to_csv(OUT/'osc_missing_systemic_rv_candidates_ranked.csv',index=False)

    # Pair search at the primary 2 km/s precision.
    pairs=[]
    cr=rank.reset_index(drop=True)
    for i,j in itertools.combinations(range(len(cr)),2):
        a=cr.iloc[i]; b=cr.iloc[j]; best=(-np.inf,None,None,None); passes=[]
        for h in v1.HGRID:
            h=float(h); au=cweight(a,h,'U',PRIMARY); av=cweight(a,h,'V',PRIMARY); bu=cweight(b,h,'U',PRIMARY); bv=cweight(b,h,'V',PRIMARY)
            if not all(np.isfinite([au,av,bu,bv])): continue
            nU=added_neff(base[h]['U']['w'],[au,bu]); nV=added_neff(base[h]['V']['w'],[av,bv]); m=min(nU,nV)
            if m>best[0]: best=(m,h,nU,nV)
            if nU>=3 and nV>=3: passes.append(h)
        pairs.append(dict(source_id_1=int(a.source_id),source_id_2=int(b.source_id),passes_pair=bool(passes),passing_h=';'.join(str(x) for x in passes),best_min_neff=best[0] if np.isfinite(best[0]) else np.nan,best_h_kpc=best[1],best_neffU=best[2],best_neffV=best[3],sum_abs_phase_kpc=abs(a.s_phase_kpc)+abs(b.s_phase_kpc)))
    pairdf=pd.DataFrame(pairs)
    if len(pairdf):
        pairdf=pairdf.sort_values(['passes_pair','best_min_neff','sum_abs_phase_kpc'],ascending=[False,False,True])
        pairdf.head(500).to_csv(OUT/'osc_missing_systemic_rv_pairs_ranked_top500.csv',index=False)

    # Compact summary.
    current={str(h):{'Neff_U':base[float(h)]['U']['neff'],'Neff_V':base[float(h)]['V']['neff']} for h in v1.HGRID}
    top_single=rank.head(20).replace({np.nan:None}).to_dict('records') if len(rank) else []
    top_pairs=pairdf.head(20).replace({np.nan:None}).to_dict('records') if len(pairdf) else []
    summary=dict(protocol='OSC_RV_TARGET_RANK_FREEZE',status='OUTCOME_BLIND_FROZEN_RANKING',target=TARGET,existing_OSC_eligible_6d=int(len(ex)),geometry_nonrv_missing_RV_candidates=int(len(rank)),accepted_RV_but_other_quality_fail=int(len(other_fail)),hypothetical_rv_precision_primary_kms=PRIMARY,sensitivity_kms=SIGMAS,current_neff_by_h=current,single_candidates_passing_primary=int(rank[f'passes_single_sigmaRV_{PRIMARY:g}'].sum()) if len(rank) else 0,pairs_passing_primary=int(pairdf.passes_pair.sum()) if len(pairdf) else 0,top_single=top_single,top_pairs=top_pairs,guardrail='No H I spectrum, H I velocity, H I residual, conventional outcome, or Persistence prediction was read.')
    (OUT/'osc_rv_target_rank_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(other_fail).to_csv(OUT/'osc_geometry_candidates_with_RV_but_other_quality_fail.csv',index=False)
    print(json.dumps(summary,indent=2,allow_nan=False))

if __name__=='__main__': main()
