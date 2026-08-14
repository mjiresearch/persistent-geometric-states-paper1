#!/usr/bin/env python3
"""Quantify Leroy+2008 Table-7 H I radial extent versus r25 and SPARC grid.

This is a source-extent audit only. It does not evaluate velocities, persistence
parameters, or blind outcomes.
"""
from __future__ import annotations
import csv,json
from collections import defaultdict
from pathlib import Path
from urllib.request import Request,urlopen
MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
LEROY=Path('data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv')
OUT=Path('validation/stationary/leroy2008_profile_extent_vs_stationary_grid_v1.json')
T4='https://cdsarc.cds.unistra.fr/ftp/J/AJ/136/2782/table4.dat';UA='PersistenceFrameworkPaperI/1.0'

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def canon(s):return ''.join(s.split())
def main():
 lr=defaultdict(list)
 for r in read_csv(LEROY):
  if r['source_sigmaHI_including_helium_msun_pc2'].strip():lr[r['galaxy']].append(float(r['source_radius_kpc']))
 master=defaultdict(list)
 for r in read_csv(MASTER):master[r['galaxy']].append(float(r['radius_kpc']))
 with urlopen(Request(T4,headers={'User-Agent':UA}),timeout=60) as h:text=h.read().decode('ascii','replace')
 meta={}
 for line in text.splitlines():
  if len(line)<37:continue
  g=canon(line[0:8])
  if g in lr:
   meta[g]={'source_distance_mpc':float(line[9:13]),'r25_kpc':float(line[32:36])}
 rows=[]
 for g in sorted(lr):
  m=meta[g]; pmax=max(lr[g]); rmax=max(master[g])
  rows.append({'galaxy':g,'source_profile_rmax_kpc':pmax,'r25_kpc':m['r25_kpc'],'source_profile_rmax_over_r25':pmax/m['r25_kpc'],
   'stationary_rotation_rmax_kpc':rmax,'rotation_rmax_over_source_profile_rmax':rmax/pmax,'outer_gap_kpc':max(0,rmax-pmax)})
 result={'status':'LEROY2008_PROFILE_EXTENT_AUDITED','n_galaxies':len(rows),'rows':rows,
  'median_source_profile_rmax_over_r25':sorted(x['source_profile_rmax_over_r25'] for x in rows)[len(rows)//2],
  'max_source_profile_rmax_over_r25':max(x['source_profile_rmax_over_r25'] for x in rows),
  'n_rotation_grids_extending_beyond_leroy_profile':sum(x['outer_gap_kpc']>0 for x in rows),
  'interpretation':'Leroy Table 7 is a bounded star-formation/gas radial-profile product and is not assumed to represent the full THINGS H I disk when the stationary rotation grid extends beyond its last finite H I bin.',
  'boundary':'Radial extent only; no velocities, residuals, persistence parameters, or blind outcomes evaluated.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
