#!/usr/bin/env python3
"""Recover the product-matched DDO154 H I diameter from Wang et al. (2016).

Wang et al. measure D_HI from natural-weighted THINGS H I intensity maps at the
azimuthally averaged raw-HI surface-density threshold Sigma_HI=1 Msun/pc^2 and
apply a beam-smearing correction. This audit retrieves their machine-readable
VizieR catalogue and records the DDO154 THINGS row, explicitly excluding the
separate LITTLE THINGS entry. Source-domain metadata only; no rotation residuals
or persistence quantities are evaluated.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.request import Request,urlopen

OUT=Path('validation/stationary/wang2016_ddo154_things_hi_diameter_v1.json')
UA='PersistenceFrameworkPaperI/1.0'
URLS=[
 'https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/460/2143/table2.dat',
 'https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/MNRAS/460/2143/table2&-out.all&-out.max=1000',
 'https://vizier.u-strasbg.fr/viz-bin/asu-tsv?-source=J/MNRAS/460/2143/table2&-out.all&-out.max=1000',
]

def fetch():
 errs=[]
 for u in URLS:
  try:
   with urlopen(Request(u,headers={'User-Agent':UA}),timeout=60) as h:
    b=h.read()
    if len(b)<1000:raise RuntimeError(f'short response {len(b)} bytes')
    return u,h.geturl(),b.decode('utf-8','replace')
  except Exception as e:errs.append({'url':u,'error':repr(e)})
 raise RuntimeError(f'no VizieR/CDS endpoint succeeded: {errs}')

def parse_fixed(text):
 rows=[]
 for line in text.splitlines():
  if len(line)<70:continue
  name=line[0:11].strip()
  try:dhi=float(line[11:17]);logm=float(line[18:23]);dist=float(line[24:29])
  except:continue
  rows.append({'Name':name,'DHI_kpc':dhi,'logMHI':logm,'Dist_Mpc':dist,'PA_deg':line[30:35].strip(),'b_over_a':line[36:40].strip(),'BMAG':line[41:48].strip(),'D25_kpc':line[49:54].strip(),'Sample':line[55:68].strip(),'Ref':line[69:115].strip()})
 return rows

def parse_tsv(text):
 data=[]
 lines=[l for l in text.splitlines() if l and not l.startswith('#')]
 header_i=None
 for i,l in enumerate(lines):
  cols=l.split('\t')
  if 'Name' in cols and 'DHI' in cols:
   header_i=i;header=cols;break
 if header_i is None:return []
 for l in lines[header_i+1:]:
  cols=l.split('\t')
  if len(cols)!=len(header):continue
  r=dict(zip(header,cols))
  try:
   data.append({'Name':r['Name'].strip(),'DHI_kpc':float(r['DHI']),'logMHI':float(r['logMHI']),'Dist_Mpc':float(r['Dist']),
    'PA_deg':r.get('PA','').strip(),'b_over_a':r.get('b/a','').strip(),'BMAG':r.get('BMAG','').strip(),'D25_kpc':r.get('D25','').strip(),'Sample':r.get('Sample','').strip(),'Ref':r.get('Ref','').strip()})
  except:pass
 return data

def compact(s):return re.sub(r'[^a-z0-9]','',s.lower())

def main():
 u,final,text=fetch();rows=parse_fixed(text)
 if not rows:rows=parse_tsv(text)
 name_matches=[r for r in rows if compact(r['Name'])=='ddo154']
 matches=[r for r in name_matches if compact(r['Sample'])=='things']
 if len(matches)!=1:raise RuntimeError(f'expected one product-matched DDO154 THINGS row; name matches={name_matches}')
 r=matches[0]
 result={'status':'WANG2016_DDO154_THINGS_HI_DIAMETER_AUDITED','catalog':'J/MNRAS/460/2143/table2','retrieval_url':u,'final_url':final,'n_catalog_rows_parsed':len(rows),'n_ddo154_name_matches':len(name_matches),'row':r,
  'r_hi_kpc':r['DHI_kpc']/2.0,
  'excluded_same_name_rows':[x for x in name_matches if x is not r],
  'definition':'Wang et al. 2016: D_HI is the major axis of a fitted ellipse where the azimuthally averaged Sigma_HI reaches 1 Msun pc^-2; natural-weighted H I images are used whenever possible; D_HI is corrected for beam smearing with sqrt(D_HI,0^2-Bmaj*Bmin).',
  'article':'Wang et al. 2016, MNRAS 460, 2143, doi:10.1093/mnras/stw1099',
  'provenance_note':'The product-matched DDO154 row is Sample=THINGS at D=4.3 Mpc; the separate LITTLE THINGS row at D=3.7 Mpc is explicitly excluded. For THINGS Wang et al. use Walter et al. 2008 interferometric data.',
  'boundary':'Published H I size metadata only; no rotation velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcomes evaluated.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
