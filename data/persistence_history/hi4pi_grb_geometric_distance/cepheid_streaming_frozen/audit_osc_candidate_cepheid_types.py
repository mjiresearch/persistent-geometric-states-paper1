#!/usr/bin/env python3
"""Outcome-blind classification audit of 31 single-RV OSC support candidates."""
from pathlib import Path
import io, json, time
import pandas as pd, requests
HERE=Path(__file__).resolve().parent
RANK=HERE/'osc_rv_target_rank'/'osc_missing_systemic_rv_candidates_ranked.csv'
SIM=HERE/'osc_rv_target_rank'/'simbad_lookup'/'simbad_top31.csv'
RAW=HERE/'gaia_dr3_classical_cepheids_table2.dat'
OUT=HERE/'osc_rv_target_rank'/'classification_audit'; OUT.mkdir(parents=True,exist_ok=True)
TAP='https://gea.esac.esa.int/tap-server/tap/sync'

def tap(q):
    last=None
    for k in range(5):
        try:
            r=requests.post(TAP,data={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q},timeout=180)
            r.raise_for_status(); return pd.read_csv(io.StringIO(r.text))
        except Exception as e:last=e;time.sleep(3*(k+1))
    raise RuntimeError(last)

def provenance():
    rows=[]
    for line in RAW.read_text(errors='replace').splitlines():
        if not line.strip():continue
        try: rows.append((int(line[0:19].strip()),line[75:83].strip()))
        except:pass
    return pd.DataFrame(rows,columns=['source_id','provenance'])

def main():
    r=pd.read_csv(RANK); r=r[r.passes_single_sigmaRV_2==True].copy()
    ids=[int(x) for x in r.source_id]; s=','.join(str(x) for x in ids)
    q=f"SELECT source_id,type_best_classification,type2_best_sub_classification,mode_best_classification,pf,p1_o FROM gaiadr3.vari_cepheid WHERE source_id IN ({s})"
    g=tap(q)
    p=provenance(); sim=pd.read_csv(SIM) if SIM.exists() else pd.DataFrame()
    keep=['source_id','main_id','otype','rvz_radvel','rvz_err','rvz_bibcode']
    if len(sim): sim=sim[[x for x in keep if x in sim.columns]]
    a=r.merge(p,on='source_id',how='left').merge(g,on='source_id',how='left')
    if len(sim): a=a.merge(sim,on='source_id',how='left')
    # Outcome-blind target-quality flags. Gaia_DCEP is supportive, but known literature
    # conflicts remain a manual exclusion; obvious SIMBAD RR/RS types are excluded.
    a['gaia_sos_DCEP']=(a.type_best_classification=='DCEP')
    a['simbad_obvious_nonclassical']=a.otype.fillna('').isin(['RR*','RS*'])
    a['known_literature_conflict']=a.main_id.fillna('').eq('V* QY Cyg')
    a['target_quality_pass']=~a.simbad_obvious_nonclassical & ~a.known_literature_conflict
    a=a.sort_values(['target_quality_pass','best_min_neff_sigmaRV_2'],ascending=[False,False])
    a.to_csv(OUT/'osc_single_pass_candidates_classification_audit.csv',index=False)
    summary={'status':'OUTCOME_BLIND_CLASSIFICATION_AUDIT','n_ranked_single_pass':int(len(a)),'n_gaia_sos_DCEP':int(a.gaia_sos_DCEP.sum()),'n_obvious_simbad_nonclassical':int(a.simbad_obvious_nonclassical.sum()),'n_known_literature_conflicts':int(a.known_literature_conflict.sum()),'n_target_quality_pass':int(a.target_quality_pass.sum()),'top_quality_candidates':a[a.target_quality_pass].head(15)[['source_id','main_id','provenance','type_best_classification','otype','Dist_kpc','s_phase_kpc','d_perp_kpc','best_min_neff_sigmaRV_2','gaia_source_rv','gaia_source_rv_error','gaia_source_rv_transits']].replace({float('nan'):None}).to_dict('records'),'manual_note':'QY Cyg is excluded because independent literature identifies it as a Type II Cepheid despite conflicting current catalog labels. SIMBAD RR*/RS* candidates are excluded from young classical-Cepheid follow-up. Other candidates retain published classical-Cepheid provenance pending spectroscopy.','guardrail':'No H I or Persistence outcome was read.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2,allow_nan=False))
if __name__=='__main__':main()
