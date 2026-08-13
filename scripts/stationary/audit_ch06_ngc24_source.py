#!/usr/bin/env python3
import io,tarfile,urllib.request,re,json,hashlib,collections
from pathlib import Path
u='https://arxiv.org/e-print/astro-ph/0609148';b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'PaperI-Ch06-audit'}),timeout=60).read()
out={'status':'CH06_NGC24_SOURCE_AUDIT_COMPLETE','source_sha256':hashlib.sha256(b).hexdigest(),'members':[],'hi_profile_contexts':[],'assets':[],'sidecars':[],'f11_geometry':{}}
with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as t:
 for m in t.getmembers():
  if not m.isfile():continue
  x=t.extractfile(m).read();out['members'].append({'name':m.name,'bytes':len(x)})
  if m.name.lower().endswith(('.dat','.csv','.tab','.tbl','.asc')):out['sidecars'].append(m.name)
  if m.name.lower().endswith(('.eps','.ps')):
   q=x.decode('latin1','ignore');lo=q.lower();out['assets'].append({'name':m.name,'bytes':len(x),'image':len(re.findall(r'(?<![a-z])image(?![a-z])',lo)),'colorimage':lo.count('colorimage'),'moveto':lo.count('moveto'),'lineto':lo.count('lineto'),'stroke':lo.count('stroke')})
   if m.name=='f11.eps':
    calls=[]
    for z in re.finditer(r'(?m)^\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+([A-Za-z][A-Za-z0-9]*)\s*$',q):calls.append((float(z.group(1)),float(z.group(2)),z.group(3)))
    by=collections.Counter(c[2] for c in calls)
    out['f11_geometry']={'headers':[line for line in q.splitlines() if line.startswith(('%%Title','%%Creator','%%BoundingBox'))][:20],'procedures':[line.strip() for line in q.splitlines() if re.match(r'^/[A-Za-z][A-Za-z0-9]*\s',line)][:80],'call_counts':dict(by),'calls_by_token':{k:[[a,b] for a,b,tok in calls if tok==k][:200] for k in by}}
  if m.name.lower().endswith(('.tex','.ltx')):
   s=x.decode('latin1','ignore')
   for pat in [r'\\label\{HIprof\}',r'concentric elliptical averaging']:
    for z in re.finditer(pat,s,re.I):
     c=re.sub(r'\s+',' ',s[max(0,z.start()-1800):z.end()+2200]);files=re.findall(r'\{([^{}]+\.(?:eps|ps|pdf|png|jpg))\}',c,re.I);out['hi_profile_contexts'].append({'pattern':pat,'files':files,'context':c})
Path('validation/stationary/ch06_ngc24_source_audit_v1.json').write_text(json.dumps(out,indent=2)+'\n')
Path('validation/stationary/ch06_ngc24_source_audit_v1.txt').write_text('\n'.join(['status='+out['status'],'sidecars='+json.dumps(out['sidecars'])]+['ASSET '+json.dumps(x) for x in out['assets']]+['F11 '+json.dumps(out['f11_geometry'])]+['HIPROF '+json.dumps(x) for x in out['hi_profile_contexts']])+'\n')
print(json.dumps({'sidecars':out['sidecars'],'f11_geometry':out['f11_geometry']},indent=2))
