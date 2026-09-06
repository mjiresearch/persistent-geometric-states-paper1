#!/usr/bin/env python3
"""Gaia-Cepheid streaming V4: outcome-independent DCEP purity correction.

V3 is immutable. V4 changes only the training-sample type gate defined in
GAIA_CEPHEID_STREAMING_PURITY_V4.md. No H I or Persistence outcome is read.
"""
from __future__ import annotations
import importlib.util, io, json, time
from pathlib import Path
import numpy as np, pandas as pd, requests

HERE=Path(__file__).resolve().parent
OUT=HERE/'outputs_v4'; OUT.mkdir(parents=True,exist_ok=True)
TYPE_CACHE=HERE/'gaia_dr3_current_cepheid_types_v4.csv'
TAP='https://gea.esac.esa.int/tap-server/tap/sync'
QY_CYG=2072235820984829312


def loadmod(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
v1=loadmod('v1_v4',HERE/'build_gaia_cepheid_streaming_v1.py')
v2=loadmod('v2_v4',HERE/'build_gaia_cepheid_streaming_v2.py')
v3=loadmod('v3_v4',HERE/'build_gaia_cepheid_streaming_v3.py')


def current_sos_types(ids):
    if TYPE_CACHE.exists() and TYPE_CACHE.stat().st_size>1000:
        return pd.read_csv(TYPE_CACHE)
    parts=[]
    for j in range(0,len(ids),100):
        chunk=ids[j:j+100]
        q=("SELECT source_id,type_best_classification,type2_best_sub_classification,mode_best_classification "
           "FROM gaiadr3.vari_cepheid WHERE source_id IN ("+','.join(str(int(x)) for x in chunk)+")")
        last=None
        for a in range(4):
            try:
                r=requests.post(TAP,data={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q},timeout=180)
                r.raise_for_status(); parts.append(pd.read_csv(io.StringIO(r.text))); last=None; break
            except Exception as e:
                last=e; time.sleep(3*(a+1))
        if last is not None: raise RuntimeError(f'Gaia type query failed chunk {j}: {last}')
    out=pd.concat(parts,ignore_index=True).drop_duplicates('source_id') if parts else pd.DataFrame(columns=['source_id','type_best_classification','type2_best_sub_classification','mode_best_classification'])
    out.to_csv(TYPE_CACHE,index=False); return out


def boot(d,h,arm,cU,cV): return v3.boot(d,h,arm,cU,cV)

def native(o):
    if isinstance(o,np.bool_): return bool(o)
    if isinstance(o,np.integer): return int(o)
    if isinstance(o,np.floating): return float(o)
    raise TypeError(type(o).__name__)


def main():
    v1.download(); ceps=v1.parse_ceps(); ids=ceps.source_id.tolist()
    gen=v1.gaia_join(ids)
    spec=v2.gaia_cepheid_join(ids)
    keep=['source_id','average_rv','average_rv_error','num_clean_epochs_rv']
    df=ceps.merge(gen,on='source_id',how='inner').merge(spec[keep],on='source_id',how='left')
    mel=v3.melnik_catalog(); df=v3.attach_melnik(df,mel); veloce=v2.parse_veloce()
    types=current_sos_types(ids)
    df=df.merge(types,on='source_id',how='left')

    # Build the exact V3-eligible sample first so V4 can report what the purity
    # gate removes. Retained rows preserve original dataframe indices/seeds.
    sample_v3=v3.build_sample(df,veloce)
    type_present=df.type_best_classification.notna()
    keep_type=(~type_present) | (df.type_best_classification=='DCEP')
    keep_qy=df.source_id.astype('int64')!=QY_CYG
    df4=df.loc[keep_type & keep_qy].copy()
    sample=v3.build_sample(df4,veloce)
    sample.to_csv(OUT/'eligible_6d_cepheids_v4.csv',index=False)

    removed_ids=sorted(set(sample_v3.source_id.astype(int))-set(sample.source_id.astype(int)))
    removed=df[df.source_id.astype('int64').isin(removed_ids)][['source_id','type_best_classification','type2_best_sub_classification','mode_best_classification']].drop_duplicates('source_id').copy()
    removed['explicit_qy_cyg_exclusion']=removed.source_id.astype('int64').eq(QY_CYG)
    removed.to_csv(OUT/'v3_eligible_sources_removed_by_v4_purity.csv',index=False)

    results=[]; choices={}
    for arm in ['Outer','OSC']:
        ts=[t for t in v1.TARGETS if t['arm']==arm]
        h,grid=v1.choose(sample,arm,ts); choices[arm]=dict(selected_h_kpc=h,grid=grid)
        for t in ts:
            _,_,_,R,pt=v1.target_pos(t); d,_=v1.members(sample,arm,pt); d.attrs['arm']=arm
            cU,cV=v1.los_coeff(t); pars=v1.armpars(arm); _,_,rft=v1.armcoords(np.array([R]),np.array([pt]),pars,pt); dp=(R-rft)/np.sqrt(1+pars[1]**2)
            row=dict(target=t['target'],arm=arm,eligible_same_arm_6d=len(d),rv_source_counts=d.rv_source.value_counts().to_dict() if len(d) else {},selected_h_kpc=h,R_kpc=R,phi_rad=pt,d_perp_kpc=dp,cU=cU,cV=cV)
            if h is None:
                row.update(status='NO_PREDICTION',U_pred_kms=None,V_pred_kms=None,Neff_U=None,Neff_V=None,nearest_phase_kpc=None,delta_v_los_inplane_kms=None,bootstrap_p16=None,bootstrap_p50=None,bootstrap_p84=None)
            else:
                U,nU,sU,near=v1.pred(d,h,'U'); V,nV,sV,_=v1.pred(d,h,'V'); q=boot(d,h,arm,cU,cV)
                row.update(status='FROZEN_PREDICTION',U_pred_kms=U,V_pred_kms=V,U_scatter_kms=sU,V_scatter_kms=sV,Neff_U=nU,Neff_V=nV,nearest_phase_kpc=near,delta_v_los_inplane_kms=cU*U+cV*V,bootstrap_p16=q[0],bootstrap_p50=q[1],bootstrap_p84=q[2])
            results.append(row)
    flat=[]
    for r in results:
        q=dict(r); q['rv_source_counts']=json.dumps(q['rv_source_counts'],sort_keys=True); flat.append(q)
    pd.DataFrame(flat).to_csv(OUT/'frozen_gaia_cepheid_streaming_predictions_v4.csv',index=False)

    summary=dict(protocol='GAIA_CEPHEID_STREAMING_PURITY_V4',status='OUTCOME_INDEPENDENT_PURITY_CORRECTION',catalog_rows=len(ceps),v3_reconstructed_eligible_6d_rows=len(sample_v3),v4_eligible_6d_rows=len(sample),removed_from_v3_eligible_count=len(removed_ids),removed_type_counts=removed.type_best_classification.fillna('NONE').value_counts().to_dict(),explicit_qy_cyg_removed=bool(QY_CYG in removed_ids),rv_source_counts=sample.rv_source.value_counts().to_dict(),choices=choices,guardrail='Builder read no H I spectrum, H I velocity, H I residual, conventional-vs-HI comparison, or Persistence prediction. V4 changes only the precommitted DCEP purity gate.',predictions=results)
    txt=json.dumps(summary,indent=2,default=native)+'\n'; (OUT/'freeze_summary_v4.json').write_text(txt); print(txt)

if __name__=='__main__': main()
