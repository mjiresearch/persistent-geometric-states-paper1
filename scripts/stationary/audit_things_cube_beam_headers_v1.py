#!/usr/bin/env python3
"""Audit beam metadata in public THINGS natural-weighted cubes for MOM0 reconstruction.

Header/provenance only. No cube science pixels are interpreted.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen
PAGE='https://things.www3.mpia.de/Data.html';UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/things_cube_beam_header_audit_v1.json')
TARGETS=['DDO154','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']
def compact(s):return re.sub(r'[^A-Z0-9]','',s.upper())
def get(url,headers=None,limit=28800):
 h={'User-Agent':UA};h.update(headers or {})
 with urlopen(Request(url,headers=h),timeout=90) as r:return r,r.read(limit)
def resolve():
 r,b=get(PAGE,limit=1_000_000);t=b.decode('latin-1','replace');base=r.geturl();links=[urljoin(base,h) for h in re.findall(r'href\s*=\s*["\']([^"\']+)["\']',t,re.I)]
 out={}
 for g in TARGETS:
  cg=compact(g);out[g]=[u for u in links if cg in compact(u.rsplit('/',1)[-1]) and '_NA_CUBE_THINGS.FITS' in u.upper()]
 return out
def cards(b):
 out=[]
 for i in range(0,len(b)-79,80):
  s=b[i:i+80].decode('ascii','replace');out.append(s)
  if s.startswith('END '):break
 return out
def value(card):
 s=card[10:];inq=False
 for i,ch in enumerate(s):
  if ch=="'":inq=not inq
  elif ch=='/' and not inq:s=s[:i];break
 v=s.strip()
 if len(v)>=2 and v[0]=="'" and v[-1]=="'":return v[1:-1].rstrip()
 if v in {'T','F'}:return v=='T'
 try:return float(v.replace('D','E')) if any(c in v for c in '.EeDd') else int(v)
 except:return v
def parse(cs):
 d={}
 for c in cs:
  k=c[:8].strip()
  if k and k not in {'END','HISTORY','COMMENT'} and c[8:10]=='= ':d[k]=value(c)
 return d
def main():
 links=resolve();rows=[]
 for g,cands in links.items():
  rec={'galaxy':g,'resolved_candidates':cands}
  if len(cands)==1:
   try:
    r,b=get(cands[0],headers={'Range':'bytes=0-28799'});h=parse(cards(b));rec.update({'status':getattr(r,'status',200),'url':r.geturl(),'header':h,'beam':{k:h.get(k) for k in ['BMAJ','BMIN','BPA']},'bunit':h.get('BUNIT'),'pixel_deg':abs(float(h.get('CDELT1',0)))})
   except Exception as e:rec['error']=repr(e)
  rows.append(rec)
 ok=[r for r in rows if r.get('beam',{}).get('BMAJ') and r.get('beam',{}).get('BMIN')]
 result={'status':'THINGS_CUBE_BEAM_HEADERS_AUDITED','n_targets':len(rows),'n_beam_success':len(ok),'rows':rows,
  'boundary':'Cube FITS header/provenance only; no science-pixel interpretation, radial reconstruction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if len(ok)!=len(rows):raise SystemExit(1)
if __name__=='__main__':main()
