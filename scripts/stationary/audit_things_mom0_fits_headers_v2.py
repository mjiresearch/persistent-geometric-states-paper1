#!/usr/bin/env python3
"""Resolve exact public THINGS MOM0 URLs and inspect FITS headers robustly.

This is a provenance/header audit only. It does not interpret science pixels,
construct profiles, evaluate persistence parameters, or inspect blind outcomes.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen

PAGE='https://things.www3.mpia.de/Data.html'
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/things_mom0_fits_header_audit_v2.json')
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']

def compact(s):return re.sub(r'[^A-Z0-9]','',s.upper())
def get(url,headers=None,limit=None):
 h={'User-Agent':UA};h.update(headers or {})
 with urlopen(Request(url,headers=h),timeout=90) as r:
  b=r.read() if limit is None else r.read(limit)
  return r,b

def resolve_urls():
 r,b=get(PAGE,limit=1_000_000);t=b.decode('latin-1','replace');base=r.geturl()
 hrefs=re.findall(r'href\s*=\s*["\']([^"\']+)["\']',t,re.I)
 links=[urljoin(base,h) for h in hrefs]
 out={}
 for g in TARGETS:
  cg=compact(g); cands=[]
  for u in links:
   name=u.rsplit('/',1)[-1]
   if compact(name).find(cg)>=0 and '_NA_MOM0_THINGS.FITS' in name.upper():cands.append(u)
  if len(cands)!=1:
   # Some site names compact differently; retain all target-name substring candidates for audit.
   alt=[u for u in links if cg in compact(u.rsplit('/',1)[-1]) and 'MOM0' in u.upper()]
   if len(alt)==1:cands=alt
  out[g]=cands
 return out

def cards_from_bytes(b):
 cards=[]
 for i in range(0,len(b)-79,80):
  s=b[i:i+80].decode('ascii','replace');cards.append(s)
  if s.startswith('END '):break
 return cards

def value_field(card):
 # FITS comments begin at slash only outside a quoted string.
 s=card[10:]; inq=False
 for i,ch in enumerate(s):
  if ch=="'":inq=not inq
  elif ch=='/' and not inq:return s[:i].strip()
 return s.strip()

def parse(cards):
 d={}; history=[]; comments=[]
 for c in cards:
  k=c[:8].strip()
  if k=='HISTORY':history.append(c[8:].strip());continue
  if k=='COMMENT':comments.append(c[8:].strip());continue
  if not k or k=='END' or c[8:10]!='= ':continue
  v=value_field(c)
  if len(v)>=2 and v[0]=="'" and v[-1]=="'":v=v[1:-1].rstrip()
  elif v in {'T','F'}:v=(v=='T')
  else:
   try:v=float(v.replace('D','E')) if any(ch in v for ch in '.EeDd') else int(v)
   except:pass
  d[k]=v
 return d,history,comments

def fetch_header(url):
 # 28800 bytes spans ten FITS blocks and comfortably covers these headers.
 r,b=get(url,headers={'Range':'bytes=0-28799'},limit=28800)
 cards=cards_from_bytes(b);d,h,c=parse(cards)
 return {'status':getattr(r,'status',200),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type',''),
  'content_length':r.headers.get('Content-Length'),'content_range':r.headers.get('Content-Range'),'bytes_read':len(b),
  'header':d,'history':h,'comments':c,'raw_cards':cards}

def main():
 resolved=resolve_urls(); rows=[]
 for g,cands in resolved.items():
  rec={'galaxy':g,'resolved_candidates':cands}
  if len(cands)==1:
   try:rec.update(fetch_header(cands[0]))
   except Exception as e:rec['error']=repr(e)
  rows.append(rec)
 successes=[r for r in rows if 'header' in r]
 result={'status':'THINGS_MOM0_FITS_HEADERS_V2_AUDITED','page':PAGE,'n_targets':len(rows),'n_success':len(successes),'rows':rows,
  'unit_values':sorted({str(r['header'].get('BUNIT','')) for r in successes}),
  'beam_key_presence':{k:sum(k in r['header'] for r in successes) for k in ['BMAJ','BMIN','BPA']},
  'boundary':'Exact URL/FITS header provenance only; no science-pixel interpretation, profile reconstruction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'n_success':result['n_success'],'urls':{r['galaxy']:r.get('resolved_candidates') for r in rows},'units':result['unit_values'],'beam_key_presence':result['beam_key_presence'],'headers':[{k:v for k,v in r.items() if k in {'galaxy','header','error'}} for r in rows]},indent=2))
 if len(successes)!=len(rows):raise SystemExit(1)
if __name__=='__main__':main()
