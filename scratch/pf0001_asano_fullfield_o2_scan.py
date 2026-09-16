#!/usr/bin/env python3
"""Actual 3-D Asano cubic writer -> exact internal O(2) soft-mode scan.

The spatial basis here is the finite-volume plane-wave eigenbasis of the
homogeneous O(2) operator.  This removes the old ad-hoc m2_zodd template, but it
is still not the final inhomogeneous galactic retarded eigenbasis.
"""
from __future__ import annotations
import argparse, json, math, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from pf0001_asano_weyl_3d_stream_physical import DT,GAMMA,M0,npy_header,kernel_ffts,frame_field,bandpass_step,tr_s3

C_KPC_MYR=306.6013937879527
A0=2.5e-5

def coeffs(k_kpc,cs,m0,op,a,b):
    k=k_kpc*C_KPC_MYR; g=math.sqrt(2)*op
    Delta=a*k*k+g*g; Q=2*k*k-3*g*g
    Kz=2*(2+3*b)/b; Kc=a*k*k/Delta
    Czc=g*(Q/Delta-2/b)
    Mzz=2*k*k-Q*Q/Delta
    Mss=-cs*cs*k*k-4*m0*m0*g*g/Delta
    Mcc=-cs*cs*k*k+g*g/b
    Czs=2*m0*g*Q/Delta
    return k,Kz,Kc,Czc,Mzz,Mss,Mcc,Czs

def Dmat(w,k_kpc,cs,m0,op,a,b):
    k,Kz,Kc,Czc,Mzz,Mss,Mcc,Czs=coeffs(k_kpc,cs,m0,op,a,b)
    return np.array([[Kz*w*w+Mzz,Czs,-1j*w*Czc],[Czs,w*w+Mss,-2j*m0*w*Kc],[1j*w*Czc,2j*m0*w*Kc,Kc*w*w+Mcc]],complex)

def Dprime(w,k_kpc,cs,m0,op,a,b):
    k,Kz,Kc,Czc,Mzz,Mss,Mcc,Czs=coeffs(k_kpc,cs,m0,op,a,b)
    return np.array([[2*Kz*w,0,-1j*Czc],[0,2*w,-2j*m0*Kc],[1j*Czc,2j*m0*Kc,2*Kc*w]],complex)

def det_poly(k_kpc,cs,m0,op,a,b):
    k,Kz,Kc,C,Mzz,Mss,Mcc,B=coeffs(k_kpc,cs,m0,op,a,b)
    A=np.array([Mzz,Kz]); D=np.array([Mss,1.]); F=np.array([Mcc,Kc])
    DF=np.convolve(D,F); DF[1]-=4*m0*m0*Kc*Kc
    p=np.convolve(A,DF); p[:2]-=B*B*F; p[1]+=4*B*m0*Kc*C; p[1]-=C*C*Mss; p[2]-=C*C
    return p

def soft_mode(k_kpc,cs,m0,op,a,b):
    roots=np.roots(det_poly(k_kpc,cs,m0,op,a,b)[::-1]); ys=[]
    for y in roots:
        tol=1e-7*max(1.,abs(y.real))
        if abs(y.imag)<=tol and y.real>0: ys.append(y.real)
        elif abs(y.imag)<=tol and y.real<=0: return None
    if len(ys)!=3: return None
    w=math.sqrt(min(ys)); H=Dmat(w,k_kpc,cs,m0,op,a,b)
    ev,U=np.linalg.eigh(H); r=U[:,np.argmin(np.abs(ev))]
    q=r[2] if abs(r[2])>1e-14 else r[np.argmax(np.abs(r))]
    r=r*np.exp(-1j*np.angle(q)); l=r.copy()
    den=np.vdot(l,Dprime(w,k_kpc,cs,m0,op,a,b)@r); Z=1/den
    return dict(w=w,r=r,l=l,Z=Z,null=float(np.min(np.abs(ev))))

def critical_cs(k_kpc,op,b):
    return math.sqrt(2)*op/(math.sqrt(b)*(k_kpc*C_KPC_MYR))

def signed_indices(n):
    q=np.arange(n,dtype=int); return np.where(q<=n//2,q,q-n)

def selected_modes(n,half,kmax):
    L=2*half; q=signed_indices(n); out=[]
    for i,nx in enumerate(q):
      for j,ny in enumerate(q):
       for k,nz in enumerate(q):
        n2=int(nx*nx+ny*ny+nz*nz)
        if n2==0: continue
        kmag=2*math.pi/L*math.sqrt(n2)
        if kmag<=kmax+1e-12: out.append((i,j,k,int(nx),int(ny),int(nz),n2,kmag))
    out.sort(key=lambda z:(z[6],z[3],z[4],z[5])); return out

def fft_coeff(field,n,half,modes):
    F=np.fft.fftn(field); dx=2*half/n; V=(2*half)**3; dV=dx**3
    vals=[]; fac=2*math.pi/(2*half)
    for i,j,k,nx,ny,nz,n2,kmag in modes:
        phase=np.exp(-1j*fac*(nx*(0.5*dx-half)+ny*(0.5*dx-half)+nz*(0.5*dx-half)))
        vals.append(F[i,j,k]*phase*dV/math.sqrt(V))
    return np.asarray(vals,np.complex128)

def extract(npz_path,start_gyr,stop_gyr,stride,ngrid,half,aperture,eps,eval_dt,kmax,out_path,length_unit_kpc):
    modes=selected_modes(ngrid,half,kmax)
    nvec=np.asarray([[x[3],x[4],x[5]] for x in modes],np.int16); n2=np.asarray([x[6] for x in modes],np.int16); kk=np.asarray([x[7] for x in modes],float)
    dx=2*half/ngrid; x=(np.arange(ngrid)+0.5)*dx-half
    X,Y,Z=np.meshgrid(x,x,x,indexing='ij'); mask=(X*X+Y*Y+Z*Z<=aperture*aperture).astype(float)
    Kfft=kernel_ffts(ngrid,half,eps); times=[]; coeff=[]
    with zipfile.ZipFile(npz_path,'r') as zf:
      member='arr_0.npy' if 'arr_0.npy' in zf.namelist() else next(n for n in zf.namelist() if n.endswith('.npy'))
      with zf.open(member,'r') as fh:
        shape,fortran,dtype=npy_header(fh)
        if fortran: raise RuntimeError('Fortran-order unsupported')
        T,N,D=shape; frame_bytes=N*D*dtype.itemsize
        start=max(0,int(math.floor(start_gyr*1000/DT))); stop=min(T,int(math.ceil(stop_gyr*1000/DT))+1); idx=np.arange(0,N,stride,dtype=np.int64)
        if start>0: fh.seek(start*frame_bytes,1)
        Eprev=Wprev=Xr=S=tprev=None
        for iframe in range(start,stop):
            buf=fh.read(frame_bytes)
            if len(buf)!=frame_bytes: raise EOFError(iframe)
            frame=np.frombuffer(buf,dtype=dtype,count=N*D).reshape((N,D))
            E,W,*_=frame_field(frame,idx,ngrid,half,eps,Kfft,aperture,False,length_unit_kpc); t=iframe*DT
            if S is None:
                Xr=E/GAMMA; S=np.zeros_like(E); tprev=t; I3=tr_s3(S); times.append(t); coeff.append(fft_coeff(mask*I3,ngrid,half,modes))
            else:
                dtn=t-(iframe-1)*DT; nsub=max(1,int(math.ceil(dtn/eval_dt)))
                for js in range(nsub):
                    fa=js/nsub; fb=(js+1)/nsub; tb=(iframe-1)*DT+fb*dtn
                    Ea=(1-fa)*Eprev+fa*E; Eb=(1-fb)*Eprev+fb*E
                    Xr,S=bandpass_step(Xr,S,Ea,Eb,GAMMA,tb-tprev); I3=tr_s3(S)
                    times.append(tb); coeff.append(fft_coeff(mask*I3,ngrid,half,modes)); tprev=tb
            Eprev,Wprev=E,W
            if (iframe-start)%25==0 or iframe==stop-1: print(f'extract n={ngrid} frame={iframe}/{stop-1} modes={len(modes)}',flush=True)
    times=np.asarray(times,float); coeff=np.asarray(coeff)
    np.savez_compressed(out_path,times=times,I_k=coeff,nvec=nvec,n2=n2,k_kpc=kk,ngrid=ngrid,half=half,aperture=aperture,stride=stride,kmax=kmax,dx=dx)
    print(json.dumps(dict(out=out_path,ngrid=ngrid,nt=len(times),nmodes=len(modes),dt=float(np.median(np.diff(times))),kmin=float(kk.min()),kmax=float(kk.max()))),flush=True)

def load(path):
    z=np.load(path,allow_pickle=True); return {k:z[k] for k in z.files}

def build_source(d,s=-1):
    t=d['times']; I=d['I_k']; dt=float(np.median(np.diff(t))); dI=np.gradient(I,dt,axis=0,edge_order=2)
    c=np.cos(M0*t)[:,None]; sn=np.sin(M0*t)[:,None]; J2=s*dI/M0
    return t,(c*I+sn*J2)/math.sqrt(2),(-sn*I+c*J2)/math.sqrt(2)

def prepare(d,n2,nfft=16384):
    t,Js,Jc=build_source(d); idx=np.where(d['n2']==n2)[0]; dt=float(np.median(np.diff(t))); nf=max(nfft,1<<(len(t)-1).bit_length())
    return dict(t=t,Js=Js[:,idx],Jc=Jc[:,idx],Fs=np.fft.ifft(Js[:,idx],n=nf,axis=0)*nf*dt,Fc=np.fft.ifft(Jc[:,idx],n=nf,axis=0)*nf*dt,dw=2*math.pi/(nf*dt),nfft=nf,k=float(d['k_kpc'][idx[0]]))

def interp(sh,w,key):
    x=w/sh['dw']; i=int(math.floor(x)); f=x-i
    if i<0 or i+1>=sh['nfft']//2: return None
    return ((1-f)*sh[key][i]+f*sh[key][i+1])*np.exp(1j*w*sh['t'][0])

def power(sh,md):
    Fs=interp(sh,md['w'],'Fs'); Fc=interp(sh,md['w'],'Fc'); l=md['l']; O=np.conj(l[1])*Fs+np.conj(l[2])*Fc
    return float(abs(md['Z'])**2*np.sum(np.abs(O)**2))

def coherence(pre,post,md):
    w=md['w']; P=2*math.pi/w; l=md['l']; num=den=0.
    for sh in (pre,post):
        t=sh['t']; Y=np.conj(l[1])*sh['Js']+np.conj(l[2])*sh['Jc']; edges=np.arange(t[0],t[-1]+P,P)
        if edges[-1]<t[-1]-1e-9: edges=np.r_[edges,t[-1]]
        else: edges[-1]=t[-1]
        sums=np.zeros(Y.shape[1],complex); cyc=[]
        for aa,bb in zip(edges[:-1],edges[1:]):
            m=(t>=aa)&(t<=bb)
            if np.count_nonzero(m)<2: continue
            z=np.trapezoid(Y[m]*np.exp(1j*w*t[m])[:,None],t[m],axis=0); sums+=z; cyc.append(z)
        if cyc: num+=float(np.sum(np.abs(sums)**2)); den+=float(np.sum(np.abs(np.asarray(cyc))**2))
    return num/den if den else np.nan

def analyze(specs,outdir):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); data={}
    for s in specs:
        label,path=s.split('=',1); data[label]=load(path)
    resolutions=sorted({int(x.split('_')[0][1:]) for x in data}); lo,hi=resolutions[-2],resolutions[-1]
    common=set.intersection(*[set(np.unique(d['n2']).astype(int)) for d in data.values()]); common=sorted(common)
    ratios=[.05,.075,.10,.125,.15]; afacs=[.5,.75,1.0]; bfacs=[.75,1.,1.25]; epsgrid=np.logspace(-6,-2,81); rows=[]
    shells={n2:{lab:prepare(d,n2) for lab,d in data.items()} for n2 in common}
    for n2,shs in shells.items():
      k=shs[f'r{hi}_pre']['k']
      for rr in ratios:
       for af in afacs:
        a=A0*af; bl=a/(1-2*a)
        for bf in bfacs:
         b=bl*bf; op=rr*M0; cj=critical_cs(k,op,b)
         for eps in epsgrid:
          cs=cj*(1+eps)
          if cs>=1: continue
          md=soft_mode(k,cs,M0,op,a,b)
          if md is None: continue
          per=2*math.pi/md['w']
          if not 18<=per<=500: continue
          pp={r:power(shs[f'r{r}_pre'],md)+power(shs[f'r{r}_post'],md) for r in resolutions}
          conv=min(pp[lo],pp[hi])/max(pp[lo],pp[hi]) if max(pp[lo],pp[hi]) else np.nan
          rows.append(dict(n2=n2,k_kpc=k,OmegaP_over_m0=rr,a_factor=af,b_factor=bf,a=a,b=b,eps_above_critical=eps,cs_critical=cj,cs=cs,omega=md['w'],period_myr=per,Z_abs=abs(md['Z']),Z_re=md['Z'].real,Z_im=md['Z'].imag,r_zeta_abs=abs(md['r'][0]),r_sigma_abs=abs(md['r'][1]),r_chi_abs=abs(md['r'][2]),convergence_ratio=conv,**{f'power_r{r}':pp[r] for r in resolutions}))
    df=pd.DataFrame(rows); df.to_csv(out/'fullfield_parameter_scan.csv',index=False)
    best=[]
    for key,g in df.groupby(['n2','OmegaP_over_m0','a_factor','b_factor']):
        p1=g[f'power_r{lo}']; p2=g[f'power_r{hi}']; shared=np.minimum(p1/p1.max(),p2/p2.max()); gg=g.copy(); gg['shared_relative']=shared
        best.append(gg.sort_values(['shared_relative','convergence_ratio'],ascending=False).iloc[0].to_dict())
    bd=pd.DataFrame(best); bd.to_csv(out/'coefficient_surface_best.csv',index=False)
    baseline=[]
    for _,row in bd[(bd.OmegaP_over_m0==.1)&(bd.a_factor==1)&(bd.b_factor==1)].iterrows():
        n2=int(row.n2); k=float(row.k_kpc); a=A0; b=a/(1-2*a); md=soft_mode(k,float(row.cs),M0,.1*M0,a,b); d=row.to_dict()
        for r in resolutions: d[f'C_r{r}']=coherence(shells[n2][f'r{r}_pre'],shells[n2][f'r{r}_post'],md)
        d['C_min']=min(d[f'C_r{r}'] for r in resolutions); baseline.append(d)
    base=pd.DataFrame(baseline).sort_values(['C_min','convergence_ratio'],ascending=False); base.to_csv(out/'baseline_shell_best.csv',index=False)
    (out/'summary.json').write_text(json.dumps(dict(resolutions=resolutions,convergence_pair=[lo,hi],common_shells=common,spatial_basis='finite-volume homogeneous plane waves',seam='pre/post powers only; no cross-seam phase'),indent=2)+'\n')
    print(base.head(20).to_string(index=False),flush=True)

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('extract'); e.add_argument('npz'); e.add_argument('--start-gyr',type=float,required=True); e.add_argument('--stop-gyr',type=float,required=True); e.add_argument('--stride',type=int,default=16); e.add_argument('--ngrid',type=int,required=True); e.add_argument('--half-size-kpc',type=float,default=15.); e.add_argument('--aperture-kpc',type=float,default=12.); e.add_argument('--softening-kpc',type=float,default=.5); e.add_argument('--eval-dt-myr',type=float,default=2.); e.add_argument('--kmax-kpc',type=float,default=1.0); e.add_argument('--length-unit-kpc',type=float,default=50.); e.add_argument('--out',required=True)
    a=sub.add_parser('analyze'); a.add_argument('--input',action='append',required=True); a.add_argument('--outdir',required=True)
    x=ap.parse_args()
    if x.cmd=='extract': extract(x.npz,x.start_gyr,x.stop_gyr,x.stride,x.ngrid,x.half_size_kpc,x.aperture_kpc,x.softening_kpc,x.eval_dt_myr,x.kmax_kpc,x.out,x.length_unit_kpc)
    else: analyze(x.input,x.outdir)
if __name__=='__main__': main()
