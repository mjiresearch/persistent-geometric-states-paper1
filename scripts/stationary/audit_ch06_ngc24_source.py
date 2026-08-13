#!/usr/bin/env python3
import io,tarfile,urllib.request,re,json,hashlib
from pathlib import Path
u='https://arxiv.org/e-print/astro-ph/0609148';r=urllib.request.Request(u,headers={'User-Agent':'PaperI-Ch06-audit'})
b=urllib.request.urlopen(r,timeout=60).read();out={'status':'CH06_NGC24_SOURCE_AUDIT_COMPLETE','source_sha256':hashlib.sha256(b).hexdigest(),'members':[],'hi_profile_contexts':[],'assets':[],'sidecars':[]}
with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as t:
 for m in t.getmembers():
  if not m.isfile():continue
  x=t.extractfile(m).read();out['members'].append({'name':m.name,'bytes':len(x)})
  if m.name.lower().endswith(('.dat','.csv','.tab','.tbl','.asc')):out['sidecars'].append(m.name)
  if m.name.lower().endswith(('.eps','.ps')):
   q=x.decode('latin1','ignore').lower();out['assets'].append({'name':m.name,'bytes':len(x),'image':len(re.findall(r'(?<![a-z])image(?![a-z])',q)),'colorimage':q.count('colorimage'),'moveto':q.count('moveto'),'lineto':q.count('lineto'),'stroke':q.count('stroke')})
  if m.name.lower().endswith(('.tex','.ltx')):
   s=x.decode('latin1','ignore')
   for pat in [r'\\label\{HIprof\}',r'\\ref\{HIprof\}',r'concentric elliptical averaging']:
    for z in re.finditer(pat,s,re.I):
     c=re.sub(r'\s+',' ',s[max(0,z.start()-1800):z.end()+2200]);files=re.findall(r'\{([^{}]+\.(?:eps|ps|pdf|png|jpg))\}',c,re.I);out['hi_profile_contexts'].append({'pattern':pat,'files':files,'context':c})
Path('validation/stationary/ch06_ngc24_source_audit_v1.json').write_text(json.dumps(out,indent=2)+'\n')
Path('validation/stationary/ch06_ngc24_source_audit_v1.txt').write_text('\n'.join(['status='+out['status'],'sidecars='+json.dumps(out['sidecars'])]+['ASSET '+json.dumps(x) for x in out['assets']]+['HIPROF '+json.dumps(x) for x in out['hi_profile_contexts']])+'\n')
print(json.dumps({'members':len(out['members']),'sidecars':out['sidecars'],'hi_profile_contexts':out['hi_profile_contexts'],'assets':out['assets']},indent=2))
