#!/usr/bin/env python3
"""Frozen Gaia-Cepheid streaming augmentation V3.

Preserves V1 generic Gaia-RVS support, upgrades RVs where higher-quality
Cepheid-specific/VELOCE data exist, and adds Mel'nik+2015 HRVs only as a
fallback. No H I or Persistence outcomes may be read.
"""
from __future__ import annotations
import importlib.util, io, json, math
from pathlib import Path
import numpy as np, pandas as pd, requests
from astropy.coordinates import SkyCoord
import astropy.units as u

HERE=Path(__file__).resolve().parent
OUT=HERE/'outputs_v3'; OUT.mkdir(parents=True,exist_ok=True)
MELNIK_RAW=HERE/'melnik2015_cepheid_hrv.tsv'
MELNIK_URL='https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J%2FAN%2F336%2F70%2Ftable1&-out=_RA,_DE,HRV,e_HRV,GCVS&-out.max=1000'
MC=256; MCSEED=20260922; BOOT=2000; BOOTSEED=20260923

# Frozen implementations.
def loadmod(name,path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
v1=loadmod('v1',HERE/'build_gaia_cepheid_streaming_v1.py')
v2=loadmod('v2',HERE/'build_gaia_cepheid_streaming_v2.py')


def melnik_catalog():
 if not MELNIK_RAW.exists() or MELNIK_RAW.stat().st_size<1000:
  r=requests.get(MELNIK_URL,timeout=120); r.raise_for_status(); MELNIK_RAW.write_text(r.text)
 lines=[x for x in MELNIK_RAW.read_text(errors='replace').splitlines() if x.strip() and not x.startswith('#')]
 header_i=next(i for i,x in enumerate(lines) if '_RA' in x and 'HRV' in x)
 hdr=[h.strip() for h in lines[header_i].split('\t')]
 out=[]
 for line in lines[header_i+1:]:
  p=line.split('\t')
  if len(p)!=len(hdr): continue
  d=dict(zip(hdr,p))
  try:
   ra=float(d['_RA']); de=float(d['_DE']); rv=float(d['HRV']); erv=float(d['e_HRV'])
   out.append(dict(melnik_ra=ra,melnik_dec=de,melnik_rv=rv,melnik_erv=erv,melnik_name=d.get('GCVS','').strip()))
  except: continue
 return pd.DataFrame(out)


def attach_melnik(df,m):
 df=df.copy(); df['melnik_rv']=np.nan; df['melnik_erv']=np.nan; df['melnik_sep_arcsec']=np.nan; df['melnik_name']=''
 if len(m)==0:return df
 c=SkyCoord(df.ra.to_numpy()*u.deg,df.dec.to_numpy()*u.deg)
 cm=SkyCoord(m.melnik_ra.to_numpy()*u.deg,m.melnik_dec.to_numpy()*u.deg)
 idx,sep,_=c.match_to_catalog_sky(cm)
 ok=sep.arcsec<=2.0
 df.loc[ok,'melnik_rv']=m.iloc[idx[ok]].melnik_rv.to_numpy()
 df.loc[ok,'melnik_erv']=m.iloc[idx[ok]].melnik_erv.to_numpy()
 df.loc[ok,'melnik_sep_arcsec']=sep.arcsec[ok]
 df.loc[ok,'melnik_name']=m.iloc[idx[ok]].melnik_name.to_numpy()
 return df


def build_sample(df,veloce):
 out=[]
 for i,r in df.iterrows():
  basics=[r.pmra,r.pmra_error,r.pmdec,r.pmdec_error,r.ruwe,r.e_mu]
  if not all(np.isfinite(basics)) or r.ruwe>=1.4:continue
  if math.log(10)/5*r.e_mu>0.20:continue
  sid=int(r.source_id); rv=erv=src=None; epochs=None
  vr=veloce.get(sid)
  if vr is not None and vr['binflag']=='F' and vr['nrv']>=8:
   rv=float(vr['vgamma']); erv=1.0; src='veloce_dr1_vgamma'; epochs=int(vr['nrv'])
  elif np.isfinite(r.average_rv) and np.isfinite(r.average_rv_error) and np.isfinite(r.num_clean_epochs_rv) and r.num_clean_epochs_rv>=8 and r.average_rv_error<=5:
   rv=float(r.average_rv); erv=float(r.average_rv_error); src='gaia_vari_cepheid'; epochs=int(r.num_clean_epochs_rv)
  elif np.isfinite(r.radial_velocity) and np.isfinite(r.radial_velocity_error) and np.isfinite(r.rv_nb_transits) and r.rv_nb_transits>=8 and r.radial_velocity_error<=5:
   rv=float(r.radial_velocity); erv=float(r.radial_velocity_error); src='gaia_source_rvs'; epochs=int(r.rv_nb_transits)
  elif np.isfinite(r.melnik_rv) and np.isfinite(r.melnik_erv) and r.melnik_erv<=5:
   rv=float(r.melnik_rv); erv=float(r.melnik_erv); src='melnik2015_hrv'; epochs=None
  if rv is None:continue
  x,y,z,R,U,V,W=v1.phase([r.ra],[r.dec],[r.Dist],[r.pmra],[r.pmdec],[rv])
  if R[0]<4:continue
  rng=np.random.default_rng(MCSEED+i); dm=rng.normal(0,r.e_mu,MC); dd=r.Dist*10**(dm/5)
  pra=rng.normal(r.pmra,r.pmra_error,MC); pde=rng.normal(r.pmdec,r.pmdec_error,MC); vrr=rng.normal(rv,erv,MC)
  _,_,_,_,Um,Vm,_=v1.phase(np.repeat(r.ra,MC),np.repeat(r.dec,MC),dd,pra,pde,vrr)
  eU=float(np.std(Um,ddof=1)); eV=float(np.std(Vm,ddof=1))
  if max(eU,eV)>20:continue
  out.append(dict(source_id=sid,x=x[0],y=y[0],z=z[0],R=R[0],phi=float(np.arctan2(y[0],x[0])),U=U[0],V=V[0],eU=eU,eV=eV,Dist=r.Dist,e_mu=r.e_mu,ruwe=r.ruwe,rv_kms=rv,rv_error_kms=erv,rv_source=src,rv_epochs=epochs))
 return pd.DataFrame(out)


def boot(d,h,arm,cU,cV):
 rng=np.random.default_rng(BOOTSEED); vals=[]; n=len(d)
 for _ in range(BOOT):
  b=d.iloc[rng.integers(0,n,n)].copy(); b.attrs['arm']=arm
  U,_,_,_=v1.pred(b,h,'U'); V,_,_,_=v1.pred(b,h,'V'); vals.append(cU*U+cV*V)
 return [float(x) for x in np.percentile(vals,[16,50,84])]

def native(o):
 if isinstance(o,np.bool_):return bool(o)
 if isinstance(o,np.integer):return int(o)
 if isinstance(o,np.floating):return float(o)
 raise TypeError(type(o).__name__)


def main():
 v1.download(); ceps=v1.parse_ceps()
 gen=v1.gaia_join(ceps.source_id.tolist()).rename(columns={})
 spec=v2.gaia_cepheid_join(ceps.source_id.tolist())
 # Use astrometry from generic Gaia join; append Cepheid-specific RV columns.
 keep=['source_id','average_rv','average_rv_error','num_clean_epochs_rv']
 df=ceps.merge(gen,on='source_id',how='inner').merge(spec[keep],on='source_id',how='left')
 mel=melnik_catalog(); df=attach_melnik(df,mel); veloce=v2.parse_veloce()
 sample=build_sample(df,veloce); sample.to_csv(OUT/'eligible_6d_cepheids_v3.csv',index=False)
 results=[]; choices={}
 for arm in ['Outer','OSC']:
  ts=[t for t in v1.TARGETS if t['arm']==arm]; h,grid=v1.choose(sample,arm,ts); choices[arm]=dict(selected_h_kpc=h,grid=grid)
  for t in ts:
   _,_,_,R,pt=v1.target_pos(t); d,_=v1.members(sample,arm,pt); d.attrs['arm']=arm; cU,cV=v1.los_coeff(t); pars=v1.armpars(arm); _,_,rft=v1.armcoords(np.array([R]),np.array([pt]),pars,pt); dp=(R-rft)/np.sqrt(1+pars[1]**2)
   row=dict(target=t['target'],arm=arm,eligible_same_arm_6d=len(d),rv_source_counts=d.rv_source.value_counts().to_dict() if len(d) else {},selected_h_kpc=h,R_kpc=R,phi_rad=pt,d_perp_kpc=dp,cU=cU,cV=cV)
   if h is None:row.update(status='NO_PREDICTION',U_pred_kms=None,V_pred_kms=None,Neff_U=None,Neff_V=None,nearest_phase_kpc=None,delta_v_los_inplane_kms=None,bootstrap_p16=None,bootstrap_p50=None,bootstrap_p84=None)
   else:
    U,nU,sU,near=v1.pred(d,h,'U'); V,nV,sV,_=v1.pred(d,h,'V'); q=boot(d,h,arm,cU,cV); row.update(status='FROZEN_PREDICTION',U_pred_kms=U,V_pred_kms=V,U_scatter_kms=sU,V_scatter_kms=sV,Neff_U=nU,Neff_V=nV,nearest_phase_kpc=near,delta_v_los_inplane_kms=cU*U+cV*V,bootstrap_p16=q[0],bootstrap_p50=q[1],bootstrap_p84=q[2])
   results.append(row)
 flat=[]
 for r in results:q=dict(r); q['rv_source_counts']=json.dumps(q['rv_source_counts'],sort_keys=True); flat.append(q)
 pd.DataFrame(flat).to_csv(OUT/'frozen_gaia_cepheid_streaming_predictions_v3.csv',index=False)
 summary=dict(protocol='GAIA_CEPHEID_STREAMING_AUGMENT_V3',status='FROZEN_BEFORE_HI_COMPARISON',catalog_rows=len(ceps),melnik_rows=len(mel),veloce_modeled_rows=len(veloce),eligible_6d_rows=len(sample),rv_source_counts=sample.rv_source.value_counts().to_dict(),choices=choices,guardrail='No H I spectrum, H I velocity, H I residual, GRB conventional outcome, or Persistence prediction was read.',predictions=results)
 txt=json.dumps(summary,indent=2,default=native)+'\n'; (OUT/'freeze_summary_v3.json').write_text(txt); print(txt)
if __name__=='__main__':main()
