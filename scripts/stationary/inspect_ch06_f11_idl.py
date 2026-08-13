#!/usr/bin/env python3
import urllib.request,io,tarfile,re,json
from pathlib import Path
UA={'User-Agent':'PaperI-WLM-route'}
def get(u):
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30);b=r.read();return {'url':u,'final_url':r.geturl(),'type':r.headers.get('Content-Type',''),'bytes':len(b),'text':b.decode('utf8','replace')[:250000]}
 except Exception as e:return {'url':u,'error':repr(e),'text':''}
urls=['https://doi.org/10.11570/26.0020','https://www.canfar.net/storage/list/AstroDataCitationDOI/CISTI.CANFAR/26.0020','https://www.canfar.net/storage/list/AstroDataCitationDOI/CISTI.CANFAR/26.0020/data']
a=[get(u) for u in urls];links=[]
for x in a:
 links += re.findall(r'https?://[^\s"<>]+',x['text'])
hits=[]
try:
 b=urllib.request.urlopen(urllib.request.Request('https://arxiv.org/e-print/2607.21841',headers=UA),timeout=60).read()
 with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as t:
  for m in t.getmembers():
   if m.isfile() and m.name.lower().endswith(('.tex','.txt')):
    s=t.extractfile(m).read().decode('utf8','replace')
    for z in re.finditer(r'(10\.11570/26\.0020|canfar|public release|data availability)',s,re.I):hits.append({'file':m.name,'context':re.sub(r'\s+',' ',s[max(0,z.start()-500):z.end()+1000])})
except Exception as e:hits=[{'error':repr(e)}]
out={'status':'LGLBS2026_WLM_DATA_ROUTE_AUDITED','attempts':[{k:v for k,v in x.items() if k!='text'} for x in a],'candidate_links':[u for u in links if any(k in u.lower() for k in ['canfar','cadc','26.0020','wlm','profile'])],'source_hits':hits}
Path('validation/stationary/lglbs2026_wlm_data_route_v1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
