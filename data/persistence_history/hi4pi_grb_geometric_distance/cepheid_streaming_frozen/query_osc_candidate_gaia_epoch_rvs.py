#!/usr/bin/env python3
"""Auxiliary outcome-blind lookup of Gaia DR3 epoch RV availability for ranked OSC targets."""
from pathlib import Path
import io, json, time
import pandas as pd, requests
HERE=Path(__file__).resolve().parent
RANK=HERE/'osc_rv_target_rank'/'osc_missing_systemic_rv_candidates_ranked.csv'
OUT=HERE/'osc_rv_target_rank'/'gaia_epoch_rv_lookup'; OUT.mkdir(parents=True,exist_ok=True)
TAP='https://gea.esac.esa.int/tap-server/tap/sync'

def tap(q):
    last=None
    for k in range(5):
        try:
            r=requests.post(TAP,data={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q},timeout=180)
            r.raise_for_status(); return pd.read_csv(io.StringIO(r.text))
        except Exception as e:
            last=e; time.sleep(3*(k+1))
    raise RuntimeError(last)

def main():
    r=pd.read_csv(RANK)
    c=r[r['passes_single_sigmaRV_2']==True].copy()
    ids=[int(x) for x in c.source_id]
    s=','.join(str(x) for x in ids)
    gs=tap(f'SELECT source_id,phot_g_mean_mag,grvs_mag,radial_velocity,radial_velocity_error,rv_nb_transits FROM gaiadr3.gaia_source WHERE source_id IN ({s})')
    vc=tap(f'SELECT source_id,pf,p1_o,average_rv,average_rv_error,num_clean_epochs_rv FROM gaiadr3.vari_cepheid WHERE source_id IN ({s})')
    st=tap(f'SELECT * FROM gaiadr3.vari_rad_vel_statistics WHERE source_id IN ({s})')
    ep=tap(f'SELECT source_id,transit_id,rv_obs_time,radial_velocity,radial_velocity_error,rejected_by_variability FROM gaiadr3.vari_epoch_radial_velocity WHERE source_id IN ({s})')
    gs.to_csv(OUT/'gaia_source_top31.csv',index=False); vc.to_csv(OUT/'vari_cepheid_top31.csv',index=False); st.to_csv(OUT/'vari_rad_vel_statistics_top31.csv',index=False); ep.to_csv(OUT/'vari_epoch_radial_velocity_top31.csv',index=False)
    epgood=ep[ep.rejected_by_variability==False] if len(ep) and 'rejected_by_variability' in ep else ep
    counts=epgood.groupby('source_id').size().to_dict() if len(epgood) else {}
    merged=c[['source_id','ra_deg','dec_deg','GLON_deg','GLAT_deg','Dist_kpc','s_phase_kpc','d_perp_kpc','best_min_neff_sigmaRV_2','best_h_sigmaRV_2']].merge(gs,on='source_id',how='left').merge(vc,on='source_id',how='left')
    merged['gaia_epoch_rv_good_count']=merged.source_id.map(counts).fillna(0).astype(int)
    merged=merged.sort_values(['gaia_epoch_rv_good_count','best_min_neff_sigmaRV_2'],ascending=[False,False])
    merged.to_csv(OUT/'top31_epoch_availability.csv',index=False)
    summary={'status':'OUTCOME_BLIND_AUXILIARY_LOOKUP','single_pass_candidates':len(ids),'candidates_with_vari_rv_statistics':int(st.source_id.nunique()) if len(st) else 0,'candidates_with_epoch_rvs':int(ep.source_id.nunique()) if len(ep) else 0,'good_epoch_rows':int(len(epgood)),'epoch_counts':{str(k):int(v) for k,v in counts.items()},'guardrail':'No H I spectrum, H I velocity, H I residual, conventional-vs-HI outcome, or Persistence prediction was read.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
