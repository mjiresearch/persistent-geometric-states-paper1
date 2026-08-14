#!/usr/bin/env python3
"""Read restoring-beam metadata from public THINGS natural-weighted cubes.

Header-only provenance audit. No cube science pixels or persistence quantities
are evaluated.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.request import Request,urlopen

SITE=Path('validation/stationary/things_public_data_site_audit_v1.json')
OUT=Path('validation/stationary/things_na_cube_beams_v1.json')
UA='PersistenceFrameworkPaperI/1.0'
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']
KEYS=['SIMPLE','BITPIX','NAXIS','NAXIS1','NAXIS2','NAXIS3','NAXIS4','BUNIT','BMAJ','BMIN','BPA','OBJECT','CTYPE1','CTYPE2','CTYPE3','CDELT1','CDELT2','CDELT3','RESTFREQ','RESTFRQ']

def compact(s):return re.sub(r'[^a-z0-9]','',s.lower())
def cards(b):
 out=[]
 for i in range(0,len(b)-79,80):
  c=b[i:i+80].decode('ascii','replace');out.append(c)
  if c.startswith('END '):break
 return out

def value(raw):
 s=raw.lstrip()
 if s.startswith("'"):
  out=[];i=1
  while i<len(s):
   if s[i]=="'":
    if i+1<len(s) and s[i+1]=="'":out.append("'");i+=2;continue
    break
   out.append(s[i]);i+=1
  return ''.join(out).strip()
 v=raw.split('/',1)[0].strip()
 if v in ('T','F'):return v=='T'
 try:return float(v.replace('D','E')) if any(ch in v for ch in '.EeDd') else int(v)
 except:return v

def parse(cc):
 d={};hist=[]
 for c in cc:
  k=c[:8].strip()
  if k in ('HISTORY','COMMENT'):
   if any(q in c.lower() for q in ('beam','restor')):hist.append(c[8:].strip())
   continue
  if k and k!='END' and c[8:10]=='= ':d[k]=value(c[10:])
 return d,hist

def probe(u):
 with urlopen(Request(u,headers={'User-Agent':UA,'Range':'bytes=0-57599'}),timeout=60) as h:
  b=h.read(57600);p,hist=parse(cards(b))
  return {'url':u,'status':getattr(h,'status',200),'content_type':h.headers.get('Content-Type',''),'content_range':h.headers.get('Content-Range',''),'header':{k:p.get(k) for k in KEYS if k in p},'beam_history':hist}

def main():
 a=json.loads(SITE.read_text());urls=[x['url'] for x in a['candidate_science_links']]
 rows=[]
 for g in TARGETS:
  cg=compact(g);m=[u for u in urls if cg in compact(u) and u.upper().endswith('_NA_CUBE_THINGS.FITS')]
  # IC2574 was not tagged by the simple site-name matcher; resolve from archive naming convention.
  if g=='IC2574' and not m:m=['https://things.www3.mpia.de/Data_files/IC_2574_NA_CUBE_THINGS.FITS']
  if len(m)!=1:raise RuntimeError(f'{g}: expected one natural cube, got {m}')
  r=probe(m[0]);r['galaxy']=g
  h=r['header'];
  if 'BMAJ' in h and 'BMIN' in h:
   r['beam_major_arcsec']=float(h['BMAJ'])*3600.0;r['beam_minor_arcsec']=float(h['BMIN'])*3600.0;r['beam_pa_deg']=h.get('BPA')
  rows.append(r)
 result={'status':'THINGS_NA_CUBE_BEAMS_AUDITED','n_targets':len(rows),'n_with_bmaj_bmin':sum('beam_major_arcsec' in r for r in rows),'rows':rows,'boundary':'Cube-header beam audit only; no science pixels, profile extraction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if result['n_with_bmaj_bmin']!=len(rows):raise SystemExit('one or more cube headers lack BMAJ/BMIN')
if __name__=='__main__':main()
