#!/usr/bin/env python3
"""Run the frozen GALAH manganese v0.2 conventional-dynamics challenge."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits
import analyze_manganese_chemical_history_v0_2 as b

N_PERM=5000; ALPHA=.01; SEED=20260904
BASE=['fe_h','mg_fe','age_bstep','teff','logg','phot_g_mean_mag','bp_rp','ruwe']
RICH=['al_fe','si_fe','ca_fe','ti_fe','ni_fe']
ORBIT=['J_R','J_Z','ecc','zmax','R_peri','R_ap']
VELS=b.VELS


def design(d,extra=()):
    cols=BASE+list(extra); z={c:b.zscore(d[c]) for c in cols}; names=cols+['fe_h_z2','age_bstep_z2']
    return np.column_stack([z[c] for c in cols]+[z['fe_h']**2,z['age_bstep']**2]),names


def packs(d,vg,selection=False):
    dat={'voxel':vg,'age':np.floor(d.age_bstep.to_numpy(float)).astype(np.int32),'feh':np.floor(d.fe_h.to_numpy(float)/.20).astype(np.int32),'mg':np.floor(d.mg_fe.to_numpy(float)/.10).astype(np.int32)}
    if selection:
        dat['survey']=d.survey_name.to_numpy(); dat['field']=d.field_id.to_numpy()
    s=pd.DataFrame(dat); sc=b.codes(s); order=np.argsort(sc,kind='stable'); ss=sc[order]; br=np.flatnonzero(np.r_[True,ss[1:]!=ss[:-1],True])
    groups=[order[br[i]:br[i+1]] for i in range(len(br)-1) if br[i+1]-br[i]>1]; sz=np.array([len(g) for g in groups],int)
    pk={int(q):np.stack([g for g in groups if len(g)==q]) for q in np.unique(sz)} if len(sz) else {}
    return pk,{'strata_total':int(sc.max()+1 if len(sc) else 0),'permutable_strata':len(groups),'stars_in_permutable_strata':int(sz.sum()) if len(sz) else 0,'modeled_stars':len(d),'permutable_fraction':float(sz.sum()/len(d)) if len(d) else 0.0,'median_size':float(np.median(sz)) if len(sz) else 0.0,'max_size':int(sz.max()) if len(sz) else 0}


def model_test(df,extra=(),selection=False,seed=SEED,label='test'):
    d=df.copy(); need=list(extra)
    for c in need: d=d[np.isfinite(d[c].to_numpy(float))]
    d,vc=b.support(d)
    out={'label':label,'rows':len(d),'supported_voxels':len(vc),'power_gate_pass':bool(len(vc)>=12),'extra_nuisance':list(extra),'selection_stratified_permutation':selection}
    if len(vc)<12: out['classification']='underpowered'; return out
    vg=b.codes(d[['vxbin','vybin','vzbin']]); X,names=design(d,extra); mh,_=b.residualize(d.mn_fe.to_numpy(float),X,vg); Y=[]; comp={}; kfull=int(vg.max()+1)+X.shape[1]+1
    for v in VELS:
        r,_=b.residualize(d[v].to_numpy(float),X,vg); Y.append(r); be,se,t=b.robust_partial(mh,r,kfull); comp[v]={'beta_kms_per_dex':be,'hc1_se':se,'t':t}
    Y=np.column_stack(Y); T=sum(comp[v]['t']**2 for v in VELS); pk,pinfo=packs(d,vg,selection); rng=np.random.default_rng(seed); work=mh.copy(); cntT=0; cnt=np.zeros(3,int); null=np.empty(N_PERM)
    for i in range(N_PERM):
        work[:]=mh
        for idx in pk.values():
            rank=np.argsort(rng.random(idx.shape),axis=1); src=np.take_along_axis(idx,rank,axis=1); work[idx]=mh[src]
        ts=np.array([b.robust_partial(work,Y[:,j],kfull)[2] for j in range(3)])
        tt=float(ts@ts); null[i]=tt; cntT+=tt>=T; cnt+=np.abs(ts)>=np.array([abs(comp[v]['t']) for v in VELS])
    pT=float((1+cntT)/(N_PERM+1)); pc=(1+cnt)/(N_PERM+1)
    for j,v in enumerate(VELS): comp[v]['component_permutation_p_two_sided']=float(pc[j])
    out.update({'nuisance_columns':names,'full_model_parameter_count_for_hc1':kfull,'mn_history_sd_dex':float(np.std(mh,ddof=1)),'components':comp,'T_Mn_3D':float(T),'omnibus_permutation_p':pT,'permutations':N_PERM,'permutation_seed':seed,'permutation_grouping':pinfo,'null_T_quantiles':{q:float(np.quantile(null,f)) for q,f in [('q50',.5),('q95',.95),('q99',.99)]},'classification':'positive' if pT<=ALPHA else 'null'})
    if selection and pinfo['permutable_fraction']<.5: out['classification']='underpowered_selection_permutation'
    return out


def base_quality(aa,dd,gg):
    m=aa.merge(dd,on='sobject_id',how='inner',validate='one_to_one').merge(gg,on='sobject_id',how='inner',validate='one_to_one')
    finite=['teff','logg','fe_h','mg_fe','mn_fe','e_mn_fe','age_bstep','e_age_bstep','R_Rzphi','z_Rzphi','phi_Rzphi','vR_Rzphi','vT_Rzphi','vz_Rzphi','phot_g_mean_mag','bp_rp','ruwe']; mask=(m.flag_sp.to_numpy()==0)&(m.flag_mn_fe.to_numpy()==0)&(m.snr_px_ccd3.to_numpy(float)>30)
    for c in finite: mask&=np.isfinite(m[c].to_numpy(float))
    return b.add_vox(m.loc[mask].copy())


def primary_mn_history(q):
    d,vc=b.support(q); vg=b.codes(d[['vxbin','vybin','vzbin']]); X,_=design(d); mh,_=b.residualize(d.mn_fe.to_numpy(float),X,vg); return pd.Series(mh,index=d.sobject_id.to_numpy()).to_dict()


def ad_summary(q,mhmap):
    d=q[q.sobject_id.isin(mhmap)].copy(); d['mn_history']=d.sobject_id.map(mhmap).astype(float); d=d[(d.R_Rzphi>=7)&(d.R_Rzphi<9)&(np.abs(d.z_Rzphi)<.5)].copy(); d['cohort']=np.where(d.mn_history>=0,'high','low'); d['rbin']=np.floor((d.R_Rzphi-7)/.5).astype(int); d['zslab']=np.where(np.abs(d.z_Rzphi)<.25,0,1)
    rows=[]; grads={}
    for zs in [0,1]:
        dz=d[d.zslab==zs]; pooled=[]
        for rb in range(4):
            x=dz[dz.rbin==rb]; R=7.25+.5*rb
            if len(x)>=100 and np.std(x.vR_Rzphi,ddof=1)>0: pooled.append((R,len(x)/(R*.5*.25),np.std(x.vR_Rzphi,ddof=1)))
        if len(pooled)>=2:
            a=np.array(pooled,float); grads[zs]=float(np.polyfit(np.log(a[:,0]),np.log(a[:,1]*a[:,2]**2),1)[0])
        else: grads[zs]=math.nan
        for rb in range(4):
            for co in ['low','high']:
                x=dz[(dz.rbin==rb)&(dz.cohort==co)]
                if len(x)>=50: rows.append({'zslab':zs,'rbin':rb,'cohort':co,'n':len(x),'mean_vT':float(np.mean(x.vT_Rzphi)),'sigma_R':float(np.std(x.vR_Rzphi,ddof=1)),'sigma_T':float(np.std(x.vT_Rzphi,ddof=1))})
    tab=pd.DataFrame(rows); diffs=[]
    for (zs,rb),g in tab.groupby(['zslab','rbin']):
        if set(g.cohort)=={'low','high'} and np.isfinite(grads[zs]):
            r={x.cohort:x for x in g.itertuples()}; pred={}
            for co in ['low','high']:
                x=r[co]; D=x.sigma_T**2-x.sigma_R**2*(1+grads[zs]); pred[co]=math.sqrt(max(233.1**2-D,0))
            diffs.append({'zslab':int(zs),'rbin':int(rb),'obs_delta_high_minus_low':r['high'].mean_vT-r['low'].mean_vT,'pred_delta_AD_high_minus_low':pred['high']-pred['low']})
    dif=pd.DataFrame(diffs)
    if dif.empty:return {'classification':'underpowered','near_solar_rows':len(d),'gradients':grads}
    point=float(np.mean(dif.obs_delta_high_minus_low-dif.pred_delta_AD_high_minus_low)); rng=np.random.default_rng(20260903); vals=np.empty(2000); cells={(zs,rb,co):x.index.to_numpy() for (zs,rb,co),x in d.groupby(['zslab','rbin','cohort']) if len(x)>=50}
    for k in range(2000):
        rr=[]; gg={}
        for zs in [0,1]:
            pool=[]; sampled={}
            for rb in range(4):
                for co in ['low','high']:
                    key=(zs,rb,co)
                    if key in cells:
                        ix=cells[key]; si=rng.choice(ix,size=len(ix),replace=True); sampled[(rb,co)]=d.loc[si]
                xs=[sampled[(rb,c)] for c in ['low','high'] if (rb,c) in sampled]
                if xs:
                    x=pd.concat(xs); R=7.25+.5*rb
                    if len(x)>=100 and np.std(x.vR_Rzphi,ddof=1)>0: pool.append((R,len(x)/(R*.5*.25),np.std(x.vR_Rzphi,ddof=1)))
            if len(pool)>=2:
                a=np.array(pool,float); gg[zs]=float(np.polyfit(np.log(a[:,0]),np.log(a[:,1]*a[:,2]**2),1)[0])
            else: gg[zs]=math.nan
            for rb in range(4):
                if (rb,'low') in sampled and (rb,'high') in sampled and np.isfinite(gg[zs]):
                    pred={}; obs={}
                    for co in ['low','high']:
                        x=sampled[(rb,co)]; sr=np.std(x.vR_Rzphi,ddof=1); st=np.std(x.vT_Rzphi,ddof=1); D=st**2-sr**2*(1+gg[zs]); pred[co]=math.sqrt(max(233.1**2-D,0)); obs[co]=np.mean(x.vT_Rzphi)
                    rr.append((obs['high']-obs['low'])-(pred['high']-pred['low']))
        vals[k]=np.mean(rr) if rr else np.nan
    lo,hi=np.nanquantile(vals,[.025,.975]); return {'classification':'asymmetric_drift_sufficient' if lo<=0<=hi else 'asymmetric_drift_insufficient','near_solar_rows':len(d),'supported_bin_pairs':len(dif),'gradient_by_z_slab':{str(k):v for k,v in grads.items()},'equal_bin_observed_delta_vT_kms':float(dif.obs_delta_high_minus_low.mean()),'equal_bin_predicted_delta_vT_AD_kms':float(dif.pred_delta_AD_high_minus_low.mean()),'observed_minus_predicted_kms':point,'bootstrap_resamples':2000,'bootstrap_interval_95_kms':[float(lo),float(hi)]}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',type=Path,required=True); ap.add_argument('--parent-summary',type=Path,required=True); ap.add_argument('--allstar',type=Path,required=True); ap.add_argument('--dynamics',type=Path,required=True); ap.add_argument('--ages',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); p=json.loads(a.protocol.read_text())
    if p.get('status')!='frozen_pre_challenge_outcome': raise RuntimeError('challenge protocol not frozen')
    parent=json.loads(a.parent_summary.read_text()); c=parent['primary']['components']; T=parent['primary']['T_Mn_3D']; fT=float(c['vT_Rzphi']['t']**2/T)
    ac=['sobject_id','flag_sp','snr_px_ccd3','teff','logg','fe_h','mg_fe','mn_fe','e_mn_fe','flag_mn_fe','phot_g_mean_mag','bp_rp','ruwe','age','survey_name','field_id']+RICH+[f'flag_{x}' for x in RICH]
    dc=['sobject_id','R_Rzphi','z_Rzphi','phi_Rzphi','vR_Rzphi','vT_Rzphi','vz_Rzphi']+ORBIT; gc=['sobject_id','age_bstep','e_age_bstep']; aa=b.read_cols(a.allstar,ac); dd=b.read_cols(a.dynamics,dc); gg=b.read_cols(a.ages,gc); q=base_quality(aa,dd,gg)
    rich=q.copy()
    for x in RICH: rich=rich[(rich[f'flag_{x}']==0)&np.isfinite(rich[x].to_numpy(float))]
    tests={'A_component_dominance':{'f_T':fT,'threshold':.80,'vT_dominated':bool(fT>=.80)},'B_rich_chemistry':model_test(rich,RICH,False,SEED,'rich_chemistry'),'C_field_selection':model_test(q,(),True,SEED+1,'field_selection'),'D_vertical_structure':{},'E_orbital_population':model_test(q,ORBIT,False,SEED+5,'orbital_population')}
    slabs=[(0,.2),(.2,.5),(.5,1.0)]
    for i,(lo,hi) in enumerate(slabs): tests['D_vertical_structure'][f'{lo:.1f}_{hi:.1f}']=model_test(q[(np.abs(q.z_Rzphi)>=lo)&(np.abs(q.z_Rzphi)<hi)],(),False,SEED+2+i,f'z_{lo}_{hi}')
    mhmap=primary_mn_history(q); tests['F_asymmetric_drift']=ad_summary(q,mhmap)
    parent_sign=np.sign(c['vR_Rzphi']['beta_kms_per_dex']); B=tests['B_rich_chemistry']; C=tests['C_field_selection']; E=tests['E_orbital_population']; D=tests['D_vertical_structure']
    def rsurv(x): return x.get('components',{}).get('vR_Rzphi',{}).get('component_permutation_p_two_sided',1)<=.01 and np.sign(x.get('components',{}).get('vR_Rzphi',{}).get('beta_kms_per_dex',0))==parent_sign
    poweredD=[x for x in D.values() if x.get('power_gate_pass')]; sameD=sum(np.sign(x.get('components',{}).get('vR_Rzphi',{}).get('beta_kms_per_dex',0))==parent_sign for x in poweredD); sigD=sum(rsurv(x) for x in poweredD)
    survive=bool(B.get('omnibus_permutation_p',1)<=.01 and rsurv(B) and C.get('classification')!='underpowered_selection_permutation' and rsurv(C) and len(poweredD)>=2 and sameD>=2 and sigD>=1 and rsurv(E))
    out={'protocol_id':p['protocol_id'],'parent_primary':{'T_Mn_3D':T,'permutation_p':parent['primary']['permutation_p'],'beta_R':c['vR_Rzphi']['beta_kms_per_dex'],'beta_T':c['vT_Rzphi']['beta_kms_per_dex'],'beta_z':c['vz_Rzphi']['beta_kms_per_dex']},'quality_rows':len(q),'tests':tests,'survival_rule_pass':survive,'classification':'manganese_history_signal_survives_GALAH_conventional_challenge' if survive else 'manganese_history_signal_does_not_survive_full_GALAH_conventional_challenge','guardrail':'Neither classification is a detection of gravitational persistence.'}
    a.out.mkdir(parents=True,exist_ok=True); (a.out/'challenge_summary.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
