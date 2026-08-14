#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

OUT=Path('validation/stationary/rh96_ngc0100_public_profile_route_v1.json')
TXT=Path('validation/stationary/rh96_ngc0100_public_profile_route_v1.txt')
UA='PaperI-Rh96-NGC100-route-audit/1.0'
URLS=[
 'https://cdsarc.cds.unistra.fr/ftp/J/A+AS/115/407/',
 'https://cdsarc.cds.unistra.fr/ftp/J/A+AS/115/407/ReadMe',
 'https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J%2FA%2BAS%2F115%2F407',
 'https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/A+AS/115/407/table1&Name=NGC%20100',
 'https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/A+AS/115/407/table4&Name=NGC%20100',
]

def fetch(url,timeout=45,max_bytes=12_000_000):
 try:
  req=Request(url,headers={'User-Agent':UA,'Accept':'*/*'})
  with urlopen(req,timeout=timeout) as r:
   b=r.read(max_bytes+1)
   if len(b)>max_bytes:b=b[:max_bytes]
   return {'url':url,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':r.headers.get('Content-Type',''),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'body':b}
 except Exception as e:return {'url':url,'error':repr(e)}

def text_of(b):
 return b.decode('utf-8','replace')

def main():
 result={'status':'RH96_NGC0100_PUBLIC_PROFILE_ROUTE_AUDITED','galaxy':'NGC0100','stationary_role':'blind','sparc_ref_id':'Rh96','requests':[],'directory_links':[],'candidate_assets':[],'asset_tests':[],'findings':{}}
 responses=[]
 for u in URLS:
  x=fetch(u);responses.append(x)
  rec={k:v for k,v in x.items() if k!='body'}
  if 'body' in x:
   t=text_of(x['body'])
   rec['text_head']=re.sub(r'\s+',' ',t[:2500]).strip()
   rec['ngc100_mentions']=len(re.findall(r'NGC\s*0*100|NGC100',t,re.I))
   rec['profile_terms']=len(re.findall(r'radial|surface density|surface-density|profile',t,re.I))
  result['requests'].append(rec)
 # Parse the CDS directory listing for all published auxiliary assets.
 if responses and 'body' in responses[0]:
  html=text_of(responses[0]['body'])
  hrefs=re.findall(r'href=["\']([^"\']+)["\']',html,re.I)
  links=[]
  for h in hrefs:
   if h.startswith('?') or h in ('../','./'):continue
   u=urljoin(responses[0].get('final_url',URLS[0]),h)
   if u not in links:links.append(u)
  result['directory_links']=links
  for u in links:
   lo=u.lower()
   if any(k in lo for k in ['ngc','gal','img','image','fig','plot','profile','surf','hi']) or lo.endswith(('.ps','.eps','.pdf','.dat','.txt','.gz','.tar','.fits','.fit')):
    result['candidate_assets'].append(u)
 # Fetch bounded candidate assets, looking only for exact/vector/numeric paths.
 for u in result['candidate_assets'][:120]:
  x=fetch(u,45,8_000_000);body=x.pop('body',b'')
  rec=x
  rec['name']=u.rsplit('/',1)[-1]
  rec['magic_hex']=body[:16].hex()
  sample=body[:2_000_000]
  low=sample.lower()
  rec['ngc100_mentions']=len(re.findall(rb'ngc\s*0*100|ngc100',low,re.I))
  rec['postscript_vector_ops']=sum(low.count(tok) for tok in [b' moveto',b' lineto',b' rlineto',b' stroke',b' fill'])
  rec['postscript_raster_ops']=low.count(b' image')+low.count(b'colorimage')
  rec['looks_fits']=body.startswith(b'SIMPLE  =')
  rec['looks_numeric_text']=bool(re.search(rb'(?m)^\s*[-+]?\d+(?:\.\d+)?\s+[-+]?\d+(?:\.\d+)?',sample))
  rec['profile_terms']=sum(low.count(k) for k in [b'radial',b'surface density',b'surface-density',b'profile'])
  result['asset_tests'].append(rec)
 # ReadMe semantics and inventory summary.
 readme=responses[1].get('body',b'') if len(responses)>1 else b''
 rt=text_of(readme)
 result['findings']={
  'readme_mentions_image_collection':bool(re.search(r'image|img\(',rt,re.I)),
  'readme_ngc100_mentions':len(re.findall(r'NGC\s*0*100|NGC100',rt,re.I)),
  'n_directory_links':len(result['directory_links']),
  'n_candidate_assets':len(result['candidate_assets']),
  'n_assets_with_ngc100':sum(x.get('ngc100_mentions',0)>0 for x in result['asset_tests']),
  'n_vector_candidates':sum(x.get('postscript_vector_ops',0)>20 and x.get('postscript_raster_ops',0)==0 for x in result['asset_tests']),
  'n_numeric_text_candidates':sum(bool(x.get('looks_numeric_text')) for x in result['asset_tests']),
  'n_fits_candidates':sum(bool(x.get('looks_fits')) for x in result['asset_tests']),
 }
 result['boundary']='Exact public-route audit only. No OCR, raster digitization, profile fitting, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 lines=[f"status={result['status']}",json.dumps(result['findings'],sort_keys=True)]
 for x in result['requests']:lines.append('REQUEST '+json.dumps(x,sort_keys=True))
 for u in result['directory_links']:lines.append('LINK '+u)
 for x in result['asset_tests']:lines.append('ASSET '+json.dumps(x,sort_keys=True))
 TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],**result['findings'],'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
