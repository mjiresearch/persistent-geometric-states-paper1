#!/usr/bin/env python3
"""Build source-distance metadata for certified H I products whose radii are in kpc.

Frozen distance comes from stationary_master_v1; frozen role comes from
stationary_split_v1. No profile values are transformed here.
"""
from __future__ import annotations
import csv,json
from pathlib import Path
from urllib.request import Request,urlopen
MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
SPLIT=Path('validation/stationary/stationary_split_v1.csv')
OUT=Path('data/stationary/source_reconstruction/certified_hi_source_scale_metadata_v2.csv')
SUMMARY=Path('validation/stationary/certified_hi_source_scale_metadata_v2_summary.json')
LEROY='https://cdsarc.cds.unistra.fr/ftp/J/AJ/136/2782/table4.dat'; UA='PersistenceFrameworkPaperI/1.0'
LEROY_TARGETS={'DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793'}
JADHAV={'F568-3':(77.,40.),'F568-V1':(80.,40.),'F574-1':(72.,65.),'F583-1':(24.,63.),'F583-4':(37.,55.)}
HA14={'UGC09037':(88.5,None),'UGC12506':(98.,86.)}
HEROES={'NGC5907':(16.3,87.2)}
def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def canonical(s):return ''.join(s.split())
def fetch_leroy():
 with urlopen(Request(LEROY,headers={'User-Agent':UA}),timeout=60) as h:text=h.read().decode('ascii','replace')
 got={}
 for line in text.splitlines():
  if len(line)<16:continue
  g=canonical(line[0:8])
  if g in LEROY_TARGETS:got[g]=(float(line[9:13]),float(line[14:16]))
 if set(got)!=LEROY_TARGETS:raise RuntimeError('Leroy table4 target mismatch')
 return got
def main():
 frozen={};
 for r in read_csv(MASTER):frozen.setdefault(r['galaxy'],float(r['distance_mpc']))
 roles={r['galaxy']:r['stationary_role'] for r in read_csv(SPLIT)}; rows=[]
 def add(g,fam,d,i,bib,basis):
  fd=frozen[g];rows.append({'galaxy':g,'stationary_role':roles[g],'source_family':fam,
   'source_distance_mpc':f'{d:g}','source_inclination_deg':'' if i is None else f'{i:g}',
   'frozen_distance_mpc':f'{fd:g}','radius_scale_frozen_over_source':f'{fd/d:.12g}',
   'source_bibcode':bib,'source_distance_basis':basis})
 for g,(d,i) in sorted(fetch_leroy().items()):add(g,'Leroy2008_THINGS',d,i,'2008AJ....136.2782L','VizieR J/AJ/136/2782 table4.dat; same catalogue as radial table7')
 for g,(d,i) in JADHAV.items():add(g,'JadhavBanerjee2019_LSB_analytic',d,i,'2019MNRAS.488..547J','Jadhav & Banerjee 2019 Table 3; Table 7 analytic radii are kpc on this paper scale')
 for g,(d,i) in HA14.items():add(g,'Hallenbeck2014_HIghMass',d,i,'2014AJ....148...69H','Hallenbeck et al. 2014 Table 1/text; Figure 9 radial axis is kpc')
 for g,(d,i) in HEROES.items():add(g,'Allaert2015_HEROES',d,i,'2015A&A...582A..18A','HEROES adopted NGC5907 distance scale; recovered Figure 29 side profiles are source-kpc')
 rows.sort(key=lambda x:x['galaxy']);OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result={'status':'CERTIFIED_HI_SOURCE_SCALE_METADATA_V2_BUILT','n_rows':len(rows),'n_families':len({r['source_family'] for r in rows}),
 'family_counts':{f:sum(r['source_family']==f for r in rows) for f in sorted({r['source_family'] for r in rows})},
 'boundary':'Source/frozen scale metadata only; no profile rescaling, inclination-amplitude correction, interpolation, persistence parameters, or blind outcomes.'}
 SUMMARY.parent.mkdir(parents=True,exist_ok=True);SUMMARY.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
