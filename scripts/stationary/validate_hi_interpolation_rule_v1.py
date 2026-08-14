#!/usr/bin/env python3
"""Mock validation of the candidate stationary H I interpolation rule.

Rule under test: piecewise-linear Sigma(R), constant inward to R=0, zero beyond
last measured radius. Synthetic profiles only; no galaxy persistence evaluation.
"""
from __future__ import annotations
import json,math
from pathlib import Path
OUT=Path('validation/stationary/hi_interpolation_rule_v1_mock_validation.json')

def eval_profile(r,s,x):
 if len(r)!=len(s) or len(r)<2:raise ValueError('need >=2 paired points')
 if any(r[i+1]<=r[i] for i in range(len(r)-1)):raise ValueError('radii must increase')
 if any(v<0 or not math.isfinite(v) for v in s):raise ValueError('Sigma must be finite/nonnegative')
 if x<0:raise ValueError('radius must be nonnegative')
 if x<=r[0]:return s[0]
 if x>r[-1]:return 0.0
 for i in range(len(r)-1):
  if r[i]<=x<=r[i+1]:
   t=(x-r[i])/(r[i+1]-r[i]);return s[i]+t*(s[i+1]-s[i])
 raise RuntimeError('unreachable')

def trapz_mass(r,s,n=20000):
 # 2*pi integral Sigma R dR over measured support, arbitrary consistent units.
 xmax=r[-1]; h=xmax/n; tot=0.0
 for i in range(n):
  a=i*h;b=(i+1)*h
  fa=eval_profile(r,s,a)*a;fb=eval_profile(r,s,b)*b
  tot+=(fa+fb)*0.5*h
 return 2*math.pi*tot

def main():
 tests=[]
 def ck(name,ok,detail=''):tests.append({'name':name,'pass':bool(ok),'detail':detail})
 r=[1.,2.,4.];s=[5.,9.,1.]
 ck('inner_constant',eval_profile(r,s,0.2)==5.)
 ck('node_exactness',all(eval_profile(r,s,x)==y for x,y in zip(r,s)))
 ck('linear_segment',abs(eval_profile(r,s,1.5)-7.)<1e-12)
 ck('outer_zero',eval_profile(r,s,4.01)==0.)
 ck('nonnegative_dense',min(eval_profile(r,s,i*0.001) for i in range(5001))>=0)
 try:eval_profile([1,1,2],[1,2,3],1.5);ok=False
 except ValueError:ok=True
 ck('reject_duplicate_radius',ok)
 try:eval_profile([1,2,3],[1,-1,2],1.5);ok=False
 except ValueError:ok=True
 ck('reject_negative_sigma',ok)
 # For a constant Sigma=S from R=0..Rmax, exact mass is pi*S*Rmax^2.
 rc=[0.,2.,4.];sc=[3.,3.,3.];m=trapz_mass(rc,sc);exact=math.pi*3.*4.**2
 ck('constant_profile_mass',abs(m-exact)/exact<1e-8,f'relerr={abs(m-exact)/exact:.3e}')
 result={'status':'HI_INTERPOLATION_RULE_V1_MOCK_VALIDATED','rule':{
  'interior':'piecewise_linear_in_surface_density_vs_radius','inner':'constant_equal_first_measured_value_to_R0','outer':'zero_beyond_last_measured_radius','negative_sigma':'reject'},
  'n_tests':len(tests),'n_pass':sum(t['pass'] for t in tests),'all_pass':all(t['pass'] for t in tests),'tests':tests,
  'boundary':'Synthetic numerical validation only; no L_A, C_A, tau_A, persistence prediction, or blind outcome evaluated.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not result['all_pass']:raise SystemExit(1)
if __name__=='__main__':main()
