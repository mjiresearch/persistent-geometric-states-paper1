#!/usr/bin/env python3
from pathlib import Path
import io, tarfile, urllib.request, re, json, hashlib

URL='https://arxiv.org/e-print/1207.2696'
req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 PersistenceFrameworkPaperI/1.0'})
with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
b=tf.extractfile(tf.getmember('Fig6.eps')).read()
lines=b.decode('latin-1','replace').splitlines()

# Preserve only the native axis/data section, not the figure binary/source asset itself.
selected=[]
for n in range(460, 736):
    if n <= len(lines): selected.append(f'{n:04d}: {lines[n-1]}')
Path('validation/stationary/ugc4483_fig6_axis_context_v1.txt').write_text('\n'.join(selected)+'\n')

# Record every numeric label and the closest preceding absolute moveto anchor.
labels=[]
for i,line in enumerate(lines):
    strings=re.findall(r'\((?:\\.|[^()])*\)',line)
    vals=[]
    for s in strings:
        t=s[1:-1].replace('\\(','(').replace('\\)',')').strip()
        if re.fullmatch(r'[-+]?\d+(?:\.\d+)?',t): vals.append(t)
    if not vals: continue
    anchor=None
    for j in range(i-1,max(-1,i-12),-1):
        m=re.search(r'(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+M\b',lines[j])
        if m:
            anchor={'line':j+1,'x':float(m.group(1)),'y':float(m.group(2))}
            break
    labels.append({'line':i+1,'values':vals,'anchor':anchor})

out={'status':'UGC4483_FIG6_AXIS_CONTEXT_EXTRACTED','fig6_sha256':hashlib.sha256(b).hexdigest(),
     'numeric_labels':labels,
     'known_frame':{'x0':882,'x1':6102,'y0':576,'y1':4500},
     'boundary':'Native EPS text/geometry only; no rendering or raster digitization.'}
Path('validation/stationary/ugc4483_fig6_axis_labels_v1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
