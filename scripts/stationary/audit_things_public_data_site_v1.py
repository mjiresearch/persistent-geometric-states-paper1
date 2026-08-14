#!/usr/bin/env python3
"""Inventory the public THINGS data website and exact FITS product links.

Network/provenance audit only. It does not download science FITS payloads beyond
small HTTP header/range probes, reconstruct profiles, or evaluate persistence.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen

URLS=['http://www.mpia.de/THINGS/Data.html','https://things.www3.mpia.de/Data.html','http://things.www3.mpia.de/Data.html']
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/things_public_data_site_audit_v1.json')
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']

def fetch(u,maxb=5_000_000):
 try:
  with urlopen(Request(u,headers={'User-Agent':UA}),timeout=45) as h:
   b=h.read(maxb);return {'url':u,'final_url':h.geturl(),'status':getattr(h,'status',200),'content_type':h.headers.get('Content-Type',''),'bytes':len(b),'body':b}
 except Exception as e:return {'url':u,'error':repr(e)}

def main():
 requests=[]; chosen=None
 for u in URLS:
  x=fetch(u); requests.append({k:v for k,v in x.items() if k!='body'})
  if x.get('status')==200 and b'<html' in x.get('body',b'').lower():chosen=x;break
 result={'status':'THINGS_PUBLIC_DATA_SITE_AUDITED','requests':requests,'targets':TARGETS,'links':[],'candidate_science_links':[]}
 if chosen:
  t=chosen['body'].decode('latin-1','replace'); base=chosen['final_url']
  hrefs=re.findall(r'href\s*=\s*["\']([^"\']+)["\']',t,re.I)
  links=[]
  for h in hrefs:
   u=urljoin(base,h)
   if u not in links:links.append(u)
  result['links']=links
  for u in links:
   lo=u.lower(); compact=re.sub(r'[^a-z0-9]','',lo)
   matched=[g for g in TARGETS if re.sub(r'[^a-z0-9]','',g.lower()) in compact]
   if matched or any(k in lo for k in ['fits','fit.gz','mom0','moment','cube','natural','robust','data']):
    result['candidate_science_links'].append({'url':u,'target_matches':matched})
  result['html_target_mentions']={g:len(re.findall(re.escape(g),t,re.I)) for g in TARGETS}
  result['html_head']=re.sub(r'\s+',' ',t[:5000]).strip()
 result['n_links']=len(result['links']);result['n_candidate_science_links']=len(result['candidate_science_links'])
 result['boundary']='Public archive link inventory only; no science FITS reconstruction, profile fitting, persistence parameters, or blind outcomes.'
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
