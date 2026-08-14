#!/usr/bin/env python3
"""Read FITS headers for public THINGS natural-weighted MOM0 maps.

Header/provenance audit only. No science pixels are interpreted and no radial
profiles or persistence quantities are evaluated.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.request import Request,urlopen
BASE='https://things.www3.mpia.de/Data_files/'
TARGET_FILES={
'DDO154':'DDO154_NA_MOM0_THINGS.FITS','IC2574':'IC2574_NA_MOM0_THINGS.FITS',
'NGC2403':'NGC_2403_NA_MOM0_THINGS.FITS','NGC2841':'NGC_2841_NA_MOM0_THINGS.FITS',
'NGC2976':'NGC_2976_NA_MOM0_THINGS.FITS','NGC3198':'NGC_3198_NA_MOM0_THINGS.FITS',
'NGC3521':'NGC_3521_NA_MOM0_THINGS.FITS','NGC5055':'NGC_5055_NA_MOM0_THINGS.FITS',
'NGC6946':'NGC_6946_NA_MOM0_THINGS.FITS','NGC7331':'NGC_7331_NA_MOM0_THINGS.FITS',
'NGC7793':'NGC_7793_NA_MOM0_THINGS.FITS'}
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/things_mom0_fits_header_audit_v1.json')
KEYS=['SIMPLE','BITPIX','NAXIS','NAXIS1','NAXIS2','BUNIT','BMAJ','BMIN','BPA','CTYPE1','CTYPE2','CRVAL1','CRVAL2','CRPIX1','CRPIX2','CDELT1','CDELT2','CROTA1','CROTA2','EQUINOX','OBJECT','TELESCOP','INSTRUME','DATAMIN','DATAMAX']
def cards_from_bytes(b):
 cards=[]
 for i in range(0,len(b)-79,80):
  s=b[i:i+80].decode('ascii','replace');cards.append(s)
  if s.startswith('END '):break
 return cards
def parse(cards):
 d={}
 for c in cards:
  k=c[:8].strip()
  if not k or k in {'COMMENT','HISTORY','END'} or c[8:10]!='= ':continue
  v=c[10:].split('/',1)[0].strip()
  if v.startswith("'") and "'" in v[1:]:v=v[1:v[1:].find("'")+1]
  else:
   if v in {'T','F'}:v=(v=='T')
   else:
    try:v=float(v.replace('D','E')) if any(ch in v for ch in '.EeDd') else int(v)
    except:pass
  d[k]=v
 return d
def fetch_header(url):
 req=Request(url,headers={'User-Agent':UA,'Range':'bytes=0-28799'})
 with urlopen(req,timeout=60) as h:
  b=h.read(28800);return {'status':getattr(h,'status',200),'final_url':h.geturl(),'content_type':h.headers.get('Content-Type',''),'content_length':h.headers.get('Content-Length'),'content_range':h.headers.get('Content-Range'),'bytes_read':len(b),'cards':cards_from_bytes(b)}
def main():
 rows=[]
 for g,f in TARGET_FILES.items():
  url=BASE+f
  try:
   x=fetch_header(url);p=parse(x.pop('cards'));rows.append({'galaxy':g,'filename':f,'url':url,**x,'header':{k:p.get(k) for k in KEYS if k in p},'all_header_keys':sorted(p)})
  except Exception as e:rows.append({'galaxy':g,'filename':f,'url':url,'error':repr(e)})
 result={'status':'THINGS_MOM0_FITS_HEADERS_AUDITED','n_targets':len(rows),'n_success':sum('header' in r for r in rows),'rows':rows,
  'boundary':'FITS header/provenance audit only; no science-pixel interpretation, radial profile reconstruction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if result['n_success']!=len(rows):raise SystemExit(1)
if __name__=='__main__':main()
