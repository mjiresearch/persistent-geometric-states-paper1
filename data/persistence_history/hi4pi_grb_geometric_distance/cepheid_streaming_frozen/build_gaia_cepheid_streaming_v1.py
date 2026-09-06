#!/usr/bin/env python3
"""Build frozen Gaia-Cepheid arm-conditioned U,V streaming field V1.

Outcome-blind: this script is forbidden from reading H I spectra/velocities/
residuals or Persistence predictions. See GAIA_CEPHEID_STREAMING_FREEZE_V1.md.
"""
from __future__ import annotations
import csv, io, json, math, time
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np, pandas as pd, requests
import astropy.units as u
from astropy.coordinates import SkyCoord, Galactocentric, CartesianDifferential

HERE=Path(__file__).resolve().parent
RAW=HERE/'gaia_dr3_classical_cepheids_table2.dat'
GAIA_CACHE=HERE/'gaia_dr3_6d_join.csv'
OUT=HERE/'outputs_v1'; OUT.mkdir(parents=True,exist_ok=True)
CEP_URL='https://cdsarc.cds.unistra.fr/ftp/J/A+A/674/A37/table2.dat'
TAP='https://gea.esac.esa.int/tap-server/tap/sync'
R0=8.15; ZSUN=0.0055; USUN=10.6; VSUN=10.7; WSUN=7.6; THETA0=236.; A2=.96; A3=1.62
SIGMA_INT=7.; HGRID=np.array([1.,2.,3.,4.,5.,7.,10.])
MC=256; MCSEED=20260918; BOOT=2000; BOOTSEED=20260919
OUTER=(2.0373888808067595,0.15578848229141543,0.8489392303918806)
OSC=(2.4652064775186884,0.23270728955462788,1.0)
TARGETS=[
 dict(target='GRB_221009A',arm='Outer',l=52.96,b=4.32,d=13.9),
 dict(target='GRB_221009A',arm='OSC',l=52.96,b=4.32,d=19.0),
 dict(target='GRB_160623A',arm='Outer',l=84.17,b=-2.69,d=9.9),
]

def urc(R):
 R=np.asarray(R,float); lam=(A3/1.5)**5; rho=R/(A2*R0); q=np.log10(lam)
 t1=200*lam**.41; t2=np.sqrt(.80+.49*q+.75*np.exp(-.4*lam)/(.47+2.25*lam**.4))
 t3=(.72+.44*q)*(1.97*rho**1.22/(rho**2+.61)**1.43); t4=1.6*np.exp(-.4*lam)*(rho**2/(rho**2+2.25*lam**.4))
 return (t1/t2)*np.sqrt(t3+t4)

def frame():
 return Galactocentric(galcen_distance=R0*u.kpc,z_sun=ZSUN*u.kpc,
   galcen_v_sun=CartesianDifferential([USUN,THETA0+VSUN,WSUN]*(u.km/u.s)))

def download():
 if RAW.exists() and RAW.stat().st_size>1000:return
 req=Request(CEP_URL,headers={'User-Agent':'PGS-Gaia-Cepheid-stream-v1/1.0'})
 with urlopen(req,timeout=120) as r,open(RAW,'wb') as f:f.write(r.read())

def parse_ceps():
 rows=[]
 for line in RAW.read_text(errors='replace').splitlines():
  if not line.strip():continue
  try:
   sid=int(line[0:19].strip()); glon=float(line[20:29]); glat=float(line[30:39]); dist=float(line[42:47]); emu=float(line[56:61])
   if dist<=0:continue
   rows.append(dict(source_id=sid,GLON=glon,GLAT=glat,Dist=dist,e_mu=emu))
  except:continue
 return pd.DataFrame(rows)

def gaia_join(ids):
 if GAIA_CACHE.exists() and GAIA_CACHE.stat().st_size>1000:return pd.read_csv(GAIA_CACHE)
 cols='source_id,ra,dec,pmra,pmra_error,pmdec,pmdec_error,radial_velocity,radial_velocity_error,rv_nb_transits,ruwe'
 parts=[]
 for j in range(0,len(ids),100):
  chunk=ids[j:j+100]; q=f"SELECT {cols} FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(str(int(x)) for x in chunk)})"
  last=None
  for attempt in range(4):
   try:
    r=requests.post(TAP,data={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q},timeout=180)
    r.raise_for_status(); d=pd.read_csv(io.StringIO(r.text)); parts.append(d); last=None; break
   except Exception as e: last=e; time.sleep(3*(attempt+1))
  if last is not None: raise RuntimeError(f'Gaia TAP failed chunk {j}: {last}')
 out=pd.concat(parts,ignore_index=True).drop_duplicates('source_id'); out.to_csv(GAIA_CACHE,index=False); return out

def phase(ra,dec,d,pmra,pmdec,rv):
 c=SkyCoord(ra=np.asarray(ra)*u.deg,dec=np.asarray(dec)*u.deg,distance=np.asarray(d)*u.kpc,
   pm_ra_cosdec=np.asarray(pmra)*u.mas/u.yr,pm_dec=np.asarray(pmdec)*u.mas/u.yr,
   radial_velocity=np.asarray(rv)*u.km/u.s,frame='icrs').transform_to(frame())
 x=c.x.to_value(u.kpc); y=c.y.to_value(u.kpc); z=c.z.to_value(u.kpc); vx=c.v_x.to_value(u.km/u.s); vy=c.v_y.to_value(u.km/u.s); vz=c.v_z.to_value(u.km/u.s)
 R=np.hypot(x,y); vR=(x*vx+y*vy)/R; vrot=(y*vx-x*vy)/R
 return x,y,z,R,-vR,vrot-urc(R),vz

def target_pos(t):
 c=SkyCoord(l=t['l']*u.deg,b=t['b']*u.deg,distance=t['d']*u.kpc,frame='galactic').transform_to(frame())
 x=float(c.x.to_value(u.kpc)); y=float(c.y.to_value(u.kpc)); z=float(c.z.to_value(u.kpc)); return x,y,z,float(np.hypot(x,y)),float(np.arctan2(y,x))

def los_coeff(t):
 eps=1e-4
 c0=SkyCoord(l=t['l']*u.deg,b=t['b']*u.deg,distance=t['d']*u.kpc,frame='galactic').transform_to(frame())
 c1=SkyCoord(l=t['l']*u.deg,b=t['b']*u.deg,distance=(t['d']+eps)*u.kpc,frame='galactic').transform_to(frame())
 p0=np.array([c0.x.to_value(u.kpc),c0.y.to_value(u.kpc),c0.z.to_value(u.kpc)]); p1=np.array([c1.x.to_value(u.kpc),c1.y.to_value(u.kpc),c1.z.to_value(u.kpc)])
 n=(p1-p0); n/=np.linalg.norm(n); x,y,_=p0; R=np.hypot(x,y)
 eU=np.array([-x/R,-y/R,0]); eV=np.array([y/R,-x/R,0]); return float(n@eU),float(n@eV)

def wrap(phi,c): return c+((np.asarray(phi)-c+np.pi)%(2*np.pi)-np.pi)
def armpars(a): return OUTER if a=='Outer' else OSC

def armcoords(R,phi,pars,pt):
 a,b,sig=pars; pu=wrap(phi,pt); rf=np.exp(a+b*pu); rft=float(np.exp(a+b*pt)); s=np.sqrt(1+b*b)/b*(rf-rft); dp=(np.asarray(R)-rf)/np.sqrt(1+b*b); return s,dp,rft

def build_sample(df):
 out=[]
 for i,r in df.iterrows():
  vals=[r.pmra,r.pmra_error,r.pmdec,r.pmdec_error,r.radial_velocity,r.radial_velocity_error,r.ruwe,r.rv_nb_transits,r.e_mu]
  if not all(np.isfinite(vals)):continue
  if r.ruwe>=1.4 or r.rv_nb_transits<8 or r.radial_velocity_error>5:continue
  frac=math.log(10)/5*r.e_mu
  if frac>0.20:continue
  x,y,z,R,U,V,W=phase([r.ra],[r.dec],[r.Dist],[r.pmra],[r.pmdec],[r.radial_velocity])
  if R[0]<4:continue
  rng=np.random.default_rng(MCSEED+i)
  dm=rng.normal(0,r.e_mu,MC); dd=r.Dist*10**(dm/5); pra=rng.normal(r.pmra,r.pmra_error,MC); pde=rng.normal(r.pmdec,r.pmdec_error,MC); vr=rng.normal(r.radial_velocity,r.radial_velocity_error,MC)
  _,_,_,_,Um,Vm,_=phase(np.repeat(r.ra,MC),np.repeat(r.dec,MC),dd,pra,pde,vr)
  eU=float(np.std(Um,ddof=1)); eV=float(np.std(Vm,ddof=1))
  if max(eU,eV)>20:continue
  out.append(dict(source_id=int(r.source_id),x=x[0],y=y[0],z=z[0],R=R[0],phi=float(np.arctan2(y[0],x[0])),U=U[0],V=V[0],eU=eU,eV=eV,Dist=r.Dist,e_mu=r.e_mu,ruwe=r.ruwe,rv_nb_transits=int(r.rv_nb_transits),rv_error=r.radial_velocity_error))
 return pd.DataFrame(out)

def members(sample,arm,pt):
 pars=armpars(arm); s,dp,_=armcoords(sample.R.to_numpy(),sample.phi.to_numpy(),pars,pt); lim=2*pars[2]
 m=np.abs(dp)<=lim; d=sample.loc[m].copy(); d['s']=s[m]; d['dperp']=dp[m]; return d,lim

def pred(d,h,comp):
 sig=d['e'+comp].to_numpy(); val=d[comp].to_numpy(); w=np.exp(-.5*(d.s.to_numpy()/h)**2)*np.exp(-.5*(d.dperp.to_numpy()/armpars(d.attrs['arm'])[2])**2)/(sig*sig+SIGMA_INT**2)
 if w.sum()<=0:return np.nan,0,np.nan,np.nan
 p=float(np.sum(w*val)/w.sum()); ne=float(w.sum()**2/np.sum(w*w)); sc=float(np.sqrt(np.sum(w*(val-p)**2)/w.sum())); near=float(np.min(np.abs(d.s)))
 return p,ne,sc,near

def cv(d,h,arm):
 d=d.reset_index(drop=True); d.attrs['arm']=arm; s=0.; n=0
 for i in range(len(d)):
  tr=d.drop(i).copy(); tr.attrs['arm']=arm
  for c in ['U','V']:
   p,_,_,_=pred(tr,h,c)
   if np.isfinite(p): s+=(d.loc[i,c]-p)**2/(d.loc[i,'e'+c]**2+SIGMA_INT**2); n+=1
 return s/n if n else np.inf

def choose(sample,arm,targets):
 phis=[target_pos(t)[4] for t in targets]; pc=float(np.median(phis)); d,_=members(sample,arm,pc); d.attrs['arm']=arm
 rec=[]; good=[]
 for h in HGRID:
  score=cv(d,h,arm); ok=True; detail=[]
  for t in targets:
   pt=target_pos(t)[4]; dt,_=members(sample,arm,pt); dt.attrs['arm']=arm
   pu,nu,_,near=pred(dt,h,'U'); pv,nv,_,_=pred(dt,h,'V'); Rt=target_pos(t)[3]; rft=armcoords(np.array([Rt]),np.array([pt]),armpars(arm),pt)[2]; dp=(Rt-rft)/np.sqrt(1+armpars(arm)[1]**2)
   q=nu>=3 and nv>=3 and near<=2*h and abs(dp)<=2*armpars(arm)[2]; ok=ok and q; detail.append((t['target'],nu,nv,near,dp,q))
  rec.append(dict(h=float(h),cv=float(score),qualified=bool(ok),detail=detail));
  if ok:good.append((score,float(h)))
 return (min(good)[1] if good else None),rec

def bootstrap(d,h,arm,cU,cV):
 rng=np.random.default_rng(BOOTSEED); vals=[]; n=len(d)
 for _ in range(BOOT):
  b=d.iloc[rng.integers(0,n,n)].copy(); b.attrs['arm']=arm; U,_,_,_=pred(b,h,'U'); V,_,_,_=pred(b,h,'V'); vals.append(cU*U+cV*V)
 return [float(x) for x in np.percentile(vals,[16,50,84])]

def main():
 download(); c=parse_ceps(); g=gaia_join(c.source_id.tolist()); df=c.merge(g,on='source_id',how='inner'); sample=build_sample(df); sample.to_csv(OUT/'eligible_6d_cepheids_v1.csv',index=False)
 results=[]; choices={}
 for arm in ['Outer','OSC']:
  ts=[t for t in TARGETS if t['arm']==arm]; h,grid=choose(sample,arm,ts); choices[arm]=dict(selected_h_kpc=h,grid=grid)
  for t in ts:
   x,y,z,R,pt=target_pos(t); d,lim=members(sample,arm,pt); d.attrs['arm']=arm; cU,cV=los_coeff(t); pars=armpars(arm); _,_,rft=armcoords(np.array([R]),np.array([pt]),pars,pt); dp=(R-rft)/np.sqrt(1+pars[1]**2)
   row=dict(target=t['target'],arm=arm,eligible_same_arm_6d=len(d),selected_h_kpc=h,R_kpc=R,phi_rad=pt,d_perp_kpc=dp,cU=cU,cV=cV)
   if h is None: row.update(status='NO_PREDICTION',U_pred_kms=None,V_pred_kms=None,Neff_U=None,Neff_V=None,nearest_phase_kpc=None,delta_v_los_inplane_kms=None,bootstrap_p16=None,bootstrap_p50=None,bootstrap_p84=None)
   else:
    U,nU,sU,near=pred(d,h,'U'); V,nV,sV,_=pred(d,h,'V'); q=bootstrap(d,h,arm,cU,cV); row.update(status='FROZEN_PREDICTION',U_pred_kms=U,V_pred_kms=V,U_scatter_kms=sU,V_scatter_kms=sV,Neff_U=nU,Neff_V=nV,nearest_phase_kpc=near,delta_v_los_inplane_kms=cU*U+cV*V,bootstrap_p16=q[0],bootstrap_p50=q[1],bootstrap_p84=q[2])
   results.append(row)
 pd.DataFrame(results).to_csv(OUT/'frozen_gaia_cepheid_streaming_predictions_v1.csv',index=False)
 summary=dict(protocol='GAIA_CEPHEID_STREAMING_FREEZE_V1',status='FROZEN_BEFORE_HI_COMPARISON',catalog_rows=len(c),gaia_join_rows=len(g),eligible_6d_rows=len(sample),quality=dict(ruwe_lt=1.4,rv_nb_transits_ge=8,rv_error_le_kms=5,frac_distance_error_le=.20,R_ge_kpc=4,propagated_UV_error_le_kms=20),choices=choices,guardrail='No H I spectrum, velocity, residual, conventional outcome, or Persistence prediction was read.',predictions=results)
 (OUT/'freeze_summary_v1.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
