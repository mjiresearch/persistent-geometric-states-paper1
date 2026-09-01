#!/usr/bin/env python3
"""Execute the frozen GALAH DR4 manganese chemical-history v0.2 protocol."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits

VOX=(0.25,0.25,0.10); MIN_PER_VOX=20; MIN_VOX=12; N_PERM=5000; SEED=20260901; ALPHA=0.01
VELS=["vR_Rzphi","vT_Rzphi","vz_Rzphi"]


def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()


def native(a):
    a=np.asarray(a)
    if a.dtype.byteorder not in ('=','|'):
        a=a.byteswap().view(a.dtype.newbyteorder('='))
    return np.array(a,copy=True)


def read_cols(p:Path,cols:list[str])->pd.DataFrame:
    with fits.open(p,memmap=True) as h:
        d=h[1].data; names=set(d.names)
        miss=[c for c in cols if c not in names]
        if miss: raise RuntimeError(f'{p.name}: missing required columns: {miss}')
        return pd.DataFrame({c:native(d[c]) for c in cols})


def zscore(a):
    a=np.asarray(a,float); s=np.nanstd(a)
    if not np.isfinite(s) or s<=0: raise RuntimeError('nonfinite/zero nuisance scale')
    return (a-np.nanmean(a))/s


def codes(frame):
    c,_=pd.factorize(pd.MultiIndex.from_frame(frame),sort=True)
    return c.astype(np.int64)


def demean(a,g):
    a=np.asarray(a,float); g=np.asarray(g,np.int64); ng=int(g.max())+1; n=np.bincount(g,minlength=ng)
    if a.ndim==1: return a-np.bincount(g,weights=a,minlength=ng)[g]/n[g]
    out=np.empty_like(a,float)
    for j in range(a.shape[1]): out[:,j]=a[:,j]-np.bincount(g,weights=a[:,j],minlength=ng)[g]/n[g]
    return out


def residualize(y,X,g):
    yw=demean(y,g); Xw=demean(X,g); b,*_=np.linalg.lstsq(Xw,yw,rcond=None)
    return yw-Xw@b,b


def robust_partial(x,y,kfull):
    x=np.asarray(x,float); y=np.asarray(y,float); den=float(x@x)
    if den<=0: return math.nan,math.nan,math.nan
    b=float(x@y/den); e=y-b*x; n=len(x)
    if n<=kfull: return b,math.nan,math.nan
    var=(n/(n-kfull))*float(np.sum((x*e)**2))/(den**2)
    se=math.sqrt(max(var,0.0)); return b,se,(b/se if se>0 else math.nan)


def add_vox(d):
    d=d.copy(); R=d.R_Rzphi.to_numpy(float); ph=d.phi_Rzphi.to_numpy(float); zz=d.z_Rzphi.to_numpy(float)
    d['vxbin']=np.floor((R*np.cos(ph))/VOX[0]).astype(np.int32)
    d['vybin']=np.floor((R*np.sin(ph))/VOX[1]).astype(np.int32)
    d['vzbin']=np.floor(zz/VOX[2]).astype(np.int32)
    return d


def support(d):
    c=d.groupby(['vxbin','vybin','vzbin'],sort=True).size().rename('n').reset_index(); k=c[c.n>=MIN_PER_VOX]
    if k.empty:return d.iloc[:0].copy(),k
    return d.merge(k[['vxbin','vybin','vzbin']],on=['vxbin','vybin','vzbin'],how='inner'),k


def design(d,age):
    cols=['fe_h','mg_fe',age,'teff','logg','phot_g_mean_mag','bp_rp','ruwe']; z={c:zscore(d[c]) for c in cols}
    names=cols+['fe_h_z2',f'{age}_z2']; X=np.column_stack([z[c] for c in cols]+[z['fe_h']**2,z[age]**2])
    return X,names


def perm_groups(d,vg,age):
    s=pd.DataFrame({'voxel':vg,'age':np.floor(d[age].to_numpy(float)).astype(np.int32),'feh':np.floor(d.fe_h.to_numpy(float)/.20).astype(np.int32),'mg':np.floor(d.mg_fe.to_numpy(float)/.10).astype(np.int32)})
    sc=codes(s); order=np.argsort(sc,kind='stable'); ss=sc[order]; br=np.flatnonzero(np.r_[True,ss[1:]!=ss[:-1],True])
    groups=[order[br[i]:br[i+1]] for i in range(len(br)-1) if br[i+1]-br[i]>1]; sizes=np.array([len(g) for g in groups],int)
    packs={int(q):np.stack([g for g in groups if len(g)==q]) for q in np.unique(sizes)} if len(sizes) else {}
    info={'population_strata_total':int(sc.max()+1 if len(sc) else 0),'permutable_strata':len(groups),'stars_in_permutable_strata':int(sizes.sum()) if len(sizes) else 0,'median_permutable_stratum_size':float(np.median(sizes)) if len(sizes) else 0.0,'max_permutable_stratum_size':int(sizes.max()) if len(sizes) else 0}
    return packs,info


def analyze(df,age,nperm,seed):
    d=df[np.isfinite(df[age].to_numpy(float))].copy(); d,vc=support(d)
    out={'age_column':age,'rows_after_age_and_support':len(d),'supported_voxels':len(vc),'minimum_stars_per_voxel':MIN_PER_VOX,'minimum_supported_voxels':MIN_VOX,'power_gate_pass':bool(len(vc)>=MIN_VOX)}
    if len(vc)<MIN_VOX: out['classification']='underpowered_frozen_v0.2'; return out
    vg=codes(d[['vxbin','vybin','vzbin']]); X,names=design(d,age); mh,mb=residualize(d.mn_fe.to_numpy(float),X,vg)
    nvox=int(vg.max()+1); kfull=nvox+X.shape[1]+1; vres={}; comp={}
    for v in VELS:
        r,_=residualize(d[v].to_numpy(float),X,vg); vres[v]=r; b,se,t=robust_partial(mh,r,kfull); comp[v]={'beta_kms_per_dex':b,'hc1_se':se,'t':t}
    T=float(sum(v['t']**2 for v in comp.values())); packs,pinfo=perm_groups(d,vg,age); rng=np.random.default_rng(seed); base=mh.copy(); work=mh.copy(); null=np.empty(nperm)
    for i in range(nperm):
        work[:]=base
        for idx in packs.values():
            rank=np.argsort(rng.random(idx.shape),axis=1); src=np.take_along_axis(idx,rank,axis=1); work[idx]=base[src]
        null[i]=sum(robust_partial(work,vres[v],kfull)[2]**2 for v in VELS)
    p=float((1+np.count_nonzero(null>=T))/(nperm+1))
    out.update({'nuisance_columns':names,'full_model_parameter_count_for_hc1':kfull,'mn_nuisance_coefficients_within_voxel':{k:float(v) for k,v in zip(names,mb)},'mn_history_sd_dex':float(np.std(mh,ddof=1)),'components':comp,'T_Mn_3D':T,'permutations':nperm,'permutation_seed':seed,'permutation_p':p,'alpha':ALPHA,'null_T_quantiles':{q:float(np.quantile(null,f)) for q,f in [('q50',.5),('q90',.9),('q95',.95),('q99',.99)]},'permutation_grouping':pinfo,'classification':'manganese_history_sensitive' if p<=ALPHA else 'null_primary_v0.2'})
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',type=Path,required=True); ap.add_argument('--allstar',type=Path,required=True); ap.add_argument('--dynamics',type=Path,required=True); ap.add_argument('--ages',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--permutations',type=int,default=N_PERM); a=ap.parse_args()
    p=json.loads(a.protocol.read_text())
    if p.get('protocol_id')!='manganese-chemical-history-v0.2' or p.get('status')!='frozen_pre_outcome' or p.get('outcome_status_at_freeze')!='no_manganese_dynamical_outcome_calculated_or_inspected': raise RuntimeError('v0.2 execution lock failed')
    a.out.mkdir(parents=True,exist_ok=True)
    ac=['sobject_id','flag_sp','snr_px_ccd3','teff','logg','fe_h','mg_fe','mn_fe','e_mn_fe','flag_mn_fe','phot_g_mean_mag','bp_rp','ruwe','age']; dc=['sobject_id','R_Rzphi','z_Rzphi','phi_Rzphi','vR_Rzphi','vT_Rzphi','vz_Rzphi']; gc=['sobject_id','age_bstep','e_age_bstep']
    aa,dd,gg=read_cols(a.allstar,ac),read_cols(a.dynamics,dc),read_cols(a.ages,gc); raw={'allstar':len(aa),'dynamics':len(dd),'ages':len(gg)}
    m=aa.merge(dd,on='sobject_id',how='inner',validate='one_to_one').merge(gg,on='sobject_id',how='inner',validate='one_to_one')
    finite=['teff','logg','fe_h','mg_fe','mn_fe','e_mn_fe','age_bstep','e_age_bstep','R_Rzphi','z_Rzphi','phi_Rzphi','vR_Rzphi','vT_Rzphi','vz_Rzphi','phot_g_mean_mag','bp_rp','ruwe']; mask=(m.flag_sp.to_numpy()==0)&(m.flag_mn_fe.to_numpy()==0)&(m.snr_px_ccd3.to_numpy(float)>30)
    for c in finite: mask&=np.isfinite(m[c].to_numpy(float))
    q=add_vox(m.loc[mask].copy())
    result={'protocol_id':p['protocol_id'],'protocol_version':p['version'],'implementation_note':'FITS numeric arrays converted to native byte order on read; values unchanged. HC1 scalar coefficient variance uses the full absorbed-FE+nuisance+Mn model parameter count.','input_files':{'allstar':{'name':a.allstar.name,'sha256':sha256(a.allstar),'bytes':a.allstar.stat().st_size},'dynamics':{'name':a.dynamics.name,'sha256':sha256(a.dynamics),'bytes':a.dynamics.stat().st_size},'ages':{'name':a.ages.name,'sha256':sha256(a.ages),'bytes':a.ages.stat().st_size}},'raw_row_counts':raw,'joined_rows':len(m),'quality_rows_before_voxel_support':len(q),'voxel_kpc':list(VOX),'primary':analyze(q,'age_bstep',a.permutations,SEED),'main_age_sensitivity':analyze(q,'age',a.permutations,SEED+1),'guardrails':{'direct_gravity_test':False,'persistence_detection_claim_allowed':False,'positive_primary_requires_conventional_challenge':True,'vT_only_signal_not_persistence_evidence':True}}
    (a.out/'galah_manganese_v0_2_summary.json').write_text(json.dumps(result,indent=2)+'\n'); q.groupby(['vxbin','vybin','vzbin']).size().rename('n_quality').reset_index().to_csv(a.out/'galah_manganese_v0_2_voxel_counts.csv',index=False); print(json.dumps(result,indent=2))

if __name__=='__main__': main()
