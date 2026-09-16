#!/usr/bin/env python3
"""Streaming 3-D secular false-arming calculation for Asano & Portegies Zwart 2026."""
from __future__ import annotations
import csv, json, math, zipfile
from pathlib import Path
import numpy as np
from scipy.linalg import expm

T0_MYR=0.913
M0=0.1/T0_MYR
GAMMA=1/T0_MYR
QO=1/8
J_W_REF_DIMLESS=3.0373051070570037e-6
ZA_REF_W=(QO**3/T0_MYR**2)*J_W_REF_DIMLESS
KMS_TO_KPCMYR=1.0227121650537077e-3
G=4.30091e-6*KMS_TO_KPCMYR**2
DT=1.0/(100.0*KMS_TO_KPCMYR)
SIGMA0=1.08e9
RD=2.3
MDISC=2*math.pi*SIGMA0*RD**2

def npy_header(fh):
    ver=np.lib.format.read_magic(fh)
    if ver==(1,0): shape,fortran,dtype=np.lib.format.read_array_header_1_0(fh)
    else: shape,fortran,dtype=np.lib.format.read_array_header_2_0(fh)
    return shape,fortran,np.dtype(dtype)

def cic_mass(pos,mass,n,half):
    dx=2*half/n; u=(pos+half)/dx-0.5
    i0=np.floor(u).astype(np.int32); f=u-i0
    out=np.zeros(n**3,dtype=np.float64)
    for bx in (0,1):
      ix=i0[:,0]+bx; wx=(1-f[:,0]) if bx==0 else f[:,0]
      for by in (0,1):
        iy=i0[:,1]+by; wy=(1-f[:,1]) if by==0 else f[:,1]
        for bz in (0,1):
          iz=i0[:,2]+bz; wz=(1-f[:,2]) if bz==0 else f[:,2]
          ok=(ix>=0)&(ix<n)&(iy>=0)&(iy<n)&(iz>=0)&(iz<n)
          if np.any(ok):
            lin=(ix[ok]*n+iy[ok])*n+iz[ok]
            out += np.bincount(lin,weights=mass[ok]*wx[ok]*wy[ok]*wz[ok],minlength=n**3)
    return out.reshape((n,n,n))

def axisym_mass_grid(full,half):
    n=full.shape[0]; dx=2*half/n
    x=(np.arange(n)+0.5)*dx-half
    X,Y=np.meshgrid(x,x,indexing='ij'); R=np.hypot(X,Y)
    rb=np.floor(R/dx).astype(np.int32); nr=int(rb.max())+1
    cnt=np.bincount(rb.ravel(),minlength=nr).astype(float); base=np.zeros_like(full)
    for k in range(n):
        sums=np.bincount(rb.ravel(),weights=full[:,:,k].ravel(),minlength=nr)
        mean=np.divide(sums,cnt,out=np.zeros_like(sums),where=cnt>0); base[:,:,k]=mean[rb]
    return base

def kernel_ffts(n,half,eps,pad=2):
    npad=pad*n; dx=2*half/n
    q=np.arange(npad); q=np.where(q<=npad//2,q,q-npad)*dx
    X,Y,Z=np.meshgrid(q,q,q,indexing='ij'); r2=X*X+Y*Y+Z*Z
    den=(r2+eps*eps)**2.5; K=[]
    for ri,rj,diag in ((X,X,1),(Y,Y,1),(Z,Z,1),(X,Y,0),(X,Z,0),(Y,Z,0)):
        kk=G*(3*ri*rj-r2*diag)/den; kk[0,0,0]=0.0; K.append(np.fft.fftn(kk))
    return K

def tidal_from_mass_grid(dm,Kfft,n,pad=2):
    npad=pad*n; st=(npad-n)//2
    arr=np.zeros((npad,npad,npad),float); arr[st:st+n,st:st+n,st:st+n]=dm
    mf=np.fft.fftn(arr); E=np.empty((6,n,n,n),float)
    for a,kf in enumerate(Kfft): E[a]=np.fft.ifftn(mf*kf).real[st:st+n,st:st+n,st:st+n]
    tr=(E[0]+E[1]+E[2])/3; E[0]-=tr; E[1]-=tr; E[2]-=tr
    return E

def bandpass_step(X,S,E0,E1,gamma,dt):
    beta=(E1-E0)/dt
    M=np.array([[-gamma,0.,1.,0.],[-gamma,-gamma,1.,0.],[0.,0.,0.,1.],[0.,0.,0.,0.]])
    Fm=expm(M*dt)
    X1=Fm[0,0]*X+Fm[0,1]*S+Fm[0,2]*E0+Fm[0,3]*beta
    S1=Fm[1,0]*X+Fm[1,1]*S+Fm[1,2]*E0+Fm[1,3]*beta
    return X1,S1

def tr_s3(S):
    xx,yy,zz,xy,xz,yz=S
    return xx**3+yy**3+zz**3+3*(xx+yy)*xy**2+3*(xx+zz)*xz**2+3*(yy+zz)*yz**2+6*xy*xz*yz

def frame_field(frame,idx,n,half,eps,Kfft,aperture,axisym_subtract,length_unit_kpc):
    pall=np.asarray(frame[:,:3],dtype=np.float64)*length_unit_kpc
    ctr=np.median(pall,axis=0); pall=pall-ctr
    p=pall[idx]
    m=np.full(len(p),MDISC/len(p),dtype=float); inside=np.all(np.abs(p)<half,axis=1)
    pbox=p[inside]; mbox=m[inside]; full=cic_mass(pbox,mbox,n,half)
    source=full-axisym_mass_grid(full,half) if axisym_subtract else full
    E=tidal_from_mass_grid(source,Kfft,n)
    rap=np.linalg.norm(pbox,axis=1)<=aperture; Wm=cic_mass(pbox[rap],mbox[rap],n,half)
    if Wm.sum()<=0: raise RuntimeError('empty aperture')
    W=Wm/Wm.sum()
    return E,W,0.,0.,ctr,0,int(rap.sum()),int(inside.sum())
