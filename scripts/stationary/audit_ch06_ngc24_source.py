#!/usr/bin/env python3
import io,tarfile,urllib.request,re,json,hashlib
from pathlib import Path
u='https://arxiv.org/e-print/astro-ph/0609148'
r=urllib.request.Request(u,headers={'User-Agent':'PaperI-Ch06-audit'})
b=urllib.request.urlopen(r,timeout=60).read()
out={'status':'CH06_NGC24_SOURCE_AUDIT_COMPLETE','source_sha256':hashlib.sha256(b).hexdigest(),'members':[],'fig8_hits':[],'assets':[],'sidecars':[]}
with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as t:
 for m in t.getmembers():
  if not m.isfile(): continue
  x=t.extractfile(m).read(); out['members'].append({'name':m.name,'bytes':len(x)})
  if m.name.lower().endswith(('.dat','.csv','.tab','.tbl','.asc')): out['sidecars'].append(m.name)
  if m.name.lower().endswith(('.eps','.ps')):
   s=x.decode('latin1','ignore').lower();out['assets'].append({'name':m.name,'bytes':len(x),'image':len(re.findall(r'(?<![a-z])image(?![a-z])',s)),'colorimage':s.count('colorimage'),'moveto':s.count('moveto'),'lineto':s.count('lineto'),'stroke':s.count('stroke')})
  if m.name.lower().endswith(('.tex','.ltx')):
   s=x.decode('latin1','ignore')
   for z in re.finditer(r'(?:Fig\.?|Figure)\s*8',s,re.I):out['fig8_hits'].append(re.sub(r'\s+',' ',s[max(0,z.start()-1200):z.end()+1800]))
Path('validation/stationary/ch06_ngc24_source_audit_v1.json').write_text(json.dumps(out,indent=2)+'\n')
Path('validation/stationary/ch06_ngc24_source_audit_v1.txt').write_text('\n'.join(['status='+out['status'],'sidecars='+json.dumps(out['sidecars'])]+['ASSET '+json.dumps(x) for x in out['assets']]+['FIG8 '+x for x in out['fig8_hits']])+'\n')
print(json.dumps({'members':len(out['members']),'sidecars':out['sidecars'],'assets':out['assets'],'fig8_hits':len(out['fig8_hits'])},indent=2))
