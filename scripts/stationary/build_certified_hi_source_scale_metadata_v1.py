#!/usr/bin/env python3
"""Build source-distance metadata for certified H I products whose radii are in kpc.

The frozen distance is always read from stationary_master_v1. Source distances
come from the same publication/catalogue that defines each recovered kpc profile.
No profile values are transformed here.
"""
from __future__ import annotations
import csv,json
from pathlib import Path
from urllib.request import Request,urlopen

MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
OUT=Path('data/stationary/source_reconstruction/certified_hi_source_scale_metadata_v1.csv')
SUMMARY=Path('validation/stationary/certified_hi_source_scale_metadata_v1_summary.json')
LEROY='https://cdsarc.cds.unistra.fr/ftp/J/AJ/136/2782/table4.dat'
UA='PersistenceFrameworkPaperI/1.0'
LEROY_TARGETS={'DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793'}
# Jadhav & Banerjee 2019 Table 3, source package arXiv:1906.10039.
JADHAV={
 'F568-3':(77.0,40.0),'F568-V1':(80.0,40.0),'F574-1':(72.0,65.0),
 'F583-1':(24.0,63.0),'F583-4':(37.0,55.0)}
# Hallenbeck+2014 Table 1/text: UGC 9037 D=88.5 Mpc; UGC 12506 D=98 Mpc.
HA14={'UGC09037':(88.5,None),'UGC12506':(98.0,86.0)}
# HEROES distance scale used for NGC5907: 16.3 Mpc (Verstappen+2013 scale;
# also tabulated for HEROES galaxies in later source summaries).
HEROES={'NGC5907':(16.3,87.2)}

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def canonical(s):return ''.join(s.split())
def frozen_distances():
 d={}
 for r in read_csv(MASTER):d.setdefault(r['galaxy'],float(r['distance_mpc']))
 return d

def fetch_leroy():
 with urlopen(Request(LEROY,headers={'User-Agent':UA}),timeout=60) as h:text=h.read().decode('ascii','replace')
 got={}
 for line in text.splitlines():
  if len(line)<16:continue
  g=canonical(line[0:8])
  if g not in LEROY_TARGETS:continue
  got[g]=(float(line[9:13]),float(line[14:16]))
 if set(got)!=LEROY_TARGETS:raise RuntimeError(f'Leroy table4 target mismatch: {sorted(set(LEROY_TARGETS)-set(got))}')
 return got

def main():
 frozen=frozen_distances(); rows=[]
 def add(g,fam,d,i,bib,basis):
  fd=frozen[g];rows.append({'galaxy':g,'stationary_role':next(r['stationary_role'] for r in read_csv(MASTER) if r['galaxy']==g),
   'source_family':fam,'source_distance_mpc':f'{d:g}','source_inclination_deg':'' if i is None else f'{i:g}',
   'frozen_distance_mpc':f'{fd:g}','radius_scale_frozen_over_source':f'{fd/d:.12g}',
   'source_bibcode':bib,'source_distance_basis':basis})
 for g,(d,i) in sorted(fetch_leroy().items()):add(g,'Leroy2008_THINGS',d,i,'2008AJ....136.2782L','VizieR J/AJ/136/2782 table4.dat; same catalogue as radial table7')
 for g,(d,i) in JADHAV.items():add(g,'JadhavBanerjee2019_LSB_analytic',d,i,'2019MNRAS.488..547J','Jadhav & Banerjee 2019 Table 3; Table 7 analytic radii are in kpc on this paper scale')
 for g,(d,i) in HA14.items():add(g,'Hallenbeck2014_HIghMass',d,i,'2014AJ....148...69H','Hallenbeck et al. 2014 Table 1/text; Figure 9 radial axis is kpc')
 for g,(d,i) in HEROES.items():add(g,'Allaert2015_HEROES',d,i,'2015A&A...582A..18A','HEROES adopted distance scale for NGC5907; recovered Figure 29 side profiles are on source kpc scale')
 rows.sort(key=lambda x:x['galaxy']); OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result={'status':'CERTIFIED_HI_SOURCE_SCALE_METADATA_V1_BUILT','n_rows':len(rows),'n_families':len({r['source_family'] for r in rows}),
  'family_counts':{f:sum(r['source_family']==f for r in rows) for f in sorted({r['source_family'] for r in rows})},
  'galaxies':[r['galaxy'] for r in rows],
  'boundary':'Source/frozen scale metadata only. No profile rescaling, inclination-amplitude correction, interpolation, persistence parameters, or blind outcomes.'}
 SUMMARY.parent.mkdir(parents=True,exist_ok=True);SUMMARY.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
