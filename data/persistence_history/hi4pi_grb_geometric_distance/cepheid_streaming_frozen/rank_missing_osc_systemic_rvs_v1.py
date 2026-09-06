#!/usr/bin/env python3
"""Outcome-blind ranking of missing systemic-RV measurements for frozen OSC V3.

Reads no H I residuals and no Persistence predictions. See
OSC_RV_TARGET_RANKING_FREEZE_V1.md.
"""
from __future__ import annotations
import importlib.util, itertools, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord

HERE = Path(__file__).resolve().parent
OUT = HERE / 'osc_rv_target_ranking_v1'
OUT.mkdir(parents=True, exist_ok=True)
HGRID = np.array([1., 2., 3., 4., 5., 7., 10.])
RV_SIGMAS = [1.0, 2.0, 5.0]
PRIMARY_RV_SIGMA = 2.0
MC = 512
SEED = 20260924
THRESH = 3.0


def loadmod(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

v1 = loadmod('v1_rank', HERE / 'build_gaia_cepheid_streaming_v1.py')
v2 = loadmod('v2_rank', HERE / 'build_gaia_cepheid_streaming_v2.py')
v3 = loadmod('v3_rank', HERE / 'build_gaia_cepheid_streaming_v3.py')

TARGET = next(t for t in v1.TARGETS if t['target']=='GRB_221009A' and t['arm']=='OSC')
OSC_SIGMA = v1.OSC[2]
SIGMA_INT = v1.SIGMA_INT


def finite(*xs):
    return all(np.isfinite(x) for x in xs)


def accepted_rv_source(r, veloce):
    sid = int(r.source_id)
    vr = veloce.get(sid)
    if vr is not None and vr['binflag']=='F' and vr['nrv']>=8:
        return 'veloce_dr1_vgamma'
    if finite(r.average_rv, r.average_rv_error, r.num_clean_epochs_rv) and r.num_clean_epochs_rv>=8 and r.average_rv_error<=5:
        return 'gaia_vari_cepheid'
    if finite(r.radial_velocity, r.radial_velocity_error, r.rv_nb_transits) and r.rv_nb_transits>=8 and r.radial_velocity_error<=5:
        return 'gaia_source_rvs'
    if finite(r.melnik_rv, r.melnik_erv) and r.melnik_erv<=5:
        return 'melnik2015_hrv'
    return None


def galpos(ra, dec, dist):
    c = SkyCoord(ra=float(ra)*u.deg, dec=float(dec)*u.deg,
                 distance=float(dist)*u.kpc, frame='icrs').transform_to(v1.frame())
    x = float(c.x.to_value(u.kpc)); y = float(c.y.to_value(u.kpc)); z = float(c.z.to_value(u.kpc))
    R = float(np.hypot(x,y)); phi = float(np.arctan2(y,x))
    return x,y,z,R,phi


def propagated_uv_errors(r, rv_sigma):
    rng = np.random.default_rng(SEED + (int(r.source_id) % 1000003) + int(rv_sigma*100))
    dm = rng.normal(0.0, float(r.e_mu), MC)
    dd = float(r.Dist) * 10**(dm/5.0)
    pra = rng.normal(float(r.pmra), float(r.pmra_error), MC)
    pde = rng.normal(float(r.pmdec), float(r.pmdec_error), MC)
    rv = rng.normal(0.0, float(rv_sigma), MC)
    _,_,_,_,Um,Vm,_ = v1.phase(np.repeat(float(r.ra),MC), np.repeat(float(r.dec),MC), dd, pra, pde, rv)
    return float(np.std(Um,ddof=1)), float(np.std(Vm,ddof=1))


def weight(s, dp, err, h):
    geo = math.exp(-0.5*(s/h)**2) * math.exp(-0.5*(dp/OSC_SIGMA)**2)
    return geo / (err*err + SIGMA_INT*SIGMA_INT)


def neff(ws):
    ws = np.asarray(ws,float)
    if len(ws)==0 or ws.sum()<=0: return 0.0
    return float(ws.sum()**2 / np.sum(ws*ws))


def existing_osc_weights():
    sample = pd.read_csv(HERE/'outputs_v3'/'eligible_6d_cepheids_v3.csv')
    pt = v1.target_pos(TARGET)[4]
    d,_ = v1.members(sample,'OSC',pt)
    d.attrs['arm']='OSC'
    return d, pt


def build_candidates(pt):
    v1.download(); ceps = v1.parse_ceps()
    gen = v1.gaia_join(ceps.source_id.tolist())
    spec = v2.gaia_cepheid_join(ceps.source_id.tolist())
    keep = ['source_id','average_rv','average_rv_error','num_clean_epochs_rv']
    df = ceps.merge(gen,on='source_id',how='inner').merge(spec[keep],on='source_id',how='left')
    mel = v3.melnik_catalog(); df = v3.attach_melnik(df,mel); veloce = v2.parse_veloce()
    eligible_ids = set(pd.read_csv(HERE/'outputs_v3'/'eligible_6d_cepheids_v3.csv').source_id.astype('int64').tolist())
    rows=[]
    for _,r in df.iterrows():
        if int(r.source_id) in eligible_ids: continue
        if not finite(r.pmra,r.pmra_error,r.pmdec,r.pmdec_error,r.ruwe,r.e_mu,r.ra,r.dec,r.Dist): continue
        if float(r.ruwe)>=1.4: continue
        frac = math.log(10)/5*float(r.e_mu)
        if frac>0.20 or float(r.Dist)<=0: continue
        if accepted_rv_source(r,veloce) is not None: continue
        try: x,y,z,R,phi = galpos(r.ra,r.dec,r.Dist)
        except Exception: continue
        if R<4: continue
        s,dp,_ = v1.armcoords(np.array([R]),np.array([phi]),v1.OSC,pt)
        s=float(s[0]); dp=float(dp[0])
        if abs(dp)>2*OSC_SIGMA: continue
        errs={}
        ok_primary=True
        for rs in RV_SIGMAS:
            eU,eV = propagated_uv_errors(r,rs)
            errs[rs]=(eU,eV)
            if rs==PRIMARY_RV_SIGMA and max(eU,eV)>20: ok_primary=False
        if not ok_primary: continue
        cg=SkyCoord(ra=float(r.ra)*u.deg,dec=float(r.dec)*u.deg,frame='icrs').galactic
        rows.append(dict(source_id=int(r.source_id),ra_deg=float(r.ra),dec_deg=float(r.dec),
                         l_deg=float(cg.l.deg),b_deg=float(cg.b.deg),Dist_kpc=float(r.Dist),e_mu=float(r.e_mu),ruwe=float(r.ruwe),
                         R_kpc=R,phi_rad=phi,s_phase_kpc=s,d_perp_kpc=dp,
                         eU_1kms=errs[1.0][0],eV_1kms=errs[1.0][1],
                         eU_2kms=errs[2.0][0],eV_2kms=errs[2.0][1],
                         eU_5kms=errs[5.0][0],eV_5kms=errs[5.0][1]))
    return pd.DataFrame(rows), len(ceps), len(df)


def base_weights(existing,h):
    s=existing.s.to_numpy(float); dp=existing.dperp.to_numpy(float)
    wU=np.array([weight(a,b,e,h) for a,b,e in zip(s,dp,existing.eU.to_numpy(float))])
    wV=np.array([weight(a,b,e,h) for a,b,e in zip(s,dp,existing.eV.to_numpy(float))])
    near=float(np.min(np.abs(s))) if len(s) else np.inf
    return wU,wV,near


def evaluate_additions(existing, additions, rv_sigma):
    best=None; per=[]
    for h in HGRID:
        bU,bV,near=base_weights(existing,float(h))
        addU=[]; addV=[]; addS=[]
        for r in additions:
            eU=float(r[f'eU_{int(rv_sigma)}kms']); eV=float(r[f'eV_{int(rv_sigma)}kms'])
            addU.append(weight(float(r.s_phase_kpc),float(r.d_perp_kpc),eU,float(h)))
            addV.append(weight(float(r.s_phase_kpc),float(r.d_perp_kpc),eV,float(h)))
            addS.append(abs(float(r.s_phase_kpc)))
        NU=neff(np.r_[bU,addU]); NV=neff(np.r_[bV,addV]); nmin=min(NU,NV)
        near2=min([near]+addS) if addS else near
        qualified=(NU>=THRESH and NV>=THRESH and near2<=2*h)
        rec=dict(h_kpc=float(h),Neff_U=NU,Neff_V=NV,min_Neff=nmin,nearest_phase_kpc=near2,qualified=bool(qualified))
        per.append(rec)
        key=(nmin, -float(h))
        if best is None or key>(best[0],-best[1]['h_kpc']): best=(nmin,rec)
    quals=[x for x in per if x['qualified']]
    smallest=min((x['h_kpc'] for x in quals),default=None)
    return best[1],smallest,per


def main():
    existing,pt=existing_osc_weights()
    cand,ncat,njoin=build_candidates(pt)
    singles=[]
    for _,r in cand.iterrows():
        out=dict(r)
        for rs in RV_SIGMAS:
            best,qh,_=evaluate_additions(existing,[r],rs)
            out[f'best_min_Neff_{int(rs)}kms']=best['min_Neff']
            out[f'best_h_{int(rs)}kms']=best['h_kpc']
            out[f'qualifying_h_{int(rs)}kms']=qh
        singles.append(out)
    sdf=pd.DataFrame(singles)
    if len(sdf):
        sdf=sdf.sort_values(['best_min_Neff_2kms','s_phase_kpc','source_id'],ascending=[False,True,True],key=lambda s: np.abs(s) if s.name=='s_phase_kpc' else s)
    sdf.to_csv(OUT/'osc_missing_rv_candidates_ranked.csv',index=False)

    pairs=[]
    records=list(cand.to_dict('records'))
    for a,b in itertools.combinations(records,2):
        best,qh,_=evaluate_additions(existing,[pd.Series(a),pd.Series(b)],PRIMARY_RV_SIGMA)
        pairs.append(dict(source_id_1=int(a['source_id']),source_id_2=int(b['source_id']),
                          phase1_kpc=float(a['s_phase_kpc']),phase2_kpc=float(b['s_phase_kpc']),
                          best_min_Neff_2kms=best['min_Neff'],best_h_2kms=best['h_kpc'],qualifying_h_2kms=qh,
                          Neff_U_at_best=best['Neff_U'],Neff_V_at_best=best['Neff_V']))
    pdf=pd.DataFrame(pairs)
    if len(pdf): pdf=pdf.sort_values(['best_min_Neff_2kms','best_h_2kms'],ascending=[False,True])
    pdf.to_csv(OUT/'osc_missing_rv_pairs_ranked.csv',index=False)

    base=[]
    for h in HGRID:
        wU,wV,near=base_weights(existing,float(h))
        base.append(dict(h_kpc=float(h),Neff_U=neff(wU),Neff_V=neff(wV),nearest_phase_kpc=near,
                         qualified=bool(neff(wU)>=THRESH and neff(wV)>=THRESH and near<=2*h)))

    top_single = sdf.head(20).to_dict('records') if len(sdf) else []
    top_pair = pdf.head(30).to_dict('records') if len(pdf) else []
    summary=dict(protocol='OSC_RV_TARGET_RANKING_FREEZE_V1',status='OUTCOME_BLIND',catalog_rows=ncat,joined_rows=njoin,
                 existing_osc_6d_rows=len(existing),candidate_missing_rv_rows=len(cand),primary_hypothetical_rv_sigma_kms=PRIMARY_RV_SIGMA,
                 sensitivity_rv_sigma_kms=RV_SIGMAS,base_support=base,
                 any_single_qualifies=bool(len(sdf) and sdf['qualifying_h_2kms'].notna().any()),
                 any_pair_qualifies=bool(len(pdf) and pdf['qualifying_h_2kms'].notna().any()),
                 top_singles=top_single,top_pairs=top_pair,
                 guardrail='No H I spectrum, H I velocity, H I residual, GRB conventional outcome, or Persistence prediction was read. Ranking uses only geometry and uncertainty weights; no hypothetical velocity value is used as a prediction.')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2,default=lambda o: float(o) if isinstance(o,np.floating) else int(o) if isinstance(o,np.integer) else bool(o) if isinstance(o,np.bool_) else None)+'\n')
    print(json.dumps(summary,indent=2,default=lambda o: float(o) if isinstance(o,np.floating) else int(o) if isinstance(o,np.integer) else bool(o) if isinstance(o,np.bool_) else None))

if __name__=='__main__': main()
