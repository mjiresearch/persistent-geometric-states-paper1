#!/usr/bin/env python3
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/astro-ph/0403154'
OUT=Path('validation/stationary/ge04_fig2_embedded_blocks_v1.json')
req=urllib.request.Request(URL,headers={'User-Agent':'PaperI-Ge04-block-probe/1.0'})
with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as tf:fig=tf.extractfile(tf.getmember('fig2.eps')).read()
s=fig.decode('latin-1','replace');lines=s.splitlines();blocks=[];start=None;name=None
for i,line in enumerate(lines):
    if line.startswith('%%BeginDocument:'):
        start=i;name=line.split(':',1)[1].strip()
    elif line.startswith('%%EndDocument') and start is not None:
        txt='\n'.join(lines[start:i+1]);low=txt.lower()
        blocks.append({'name':name,'bytes_text':len(txt.encode('latin-1','replace')),'sha256':hashlib.sha256(txt.encode('latin-1','replace')).hexdigest(),'filled_circle_signature_hits':len(re.findall(r'(?:35|36|37|38|39|40|41|42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|59|60)',txt)),'ngc1090_name_signal':'1090' in name.lower()})
        start=None;name=None
out={'status':'GE04_FIG2_EMBEDDED_BLOCKS_ENUMERATED','source_url':URL,'source_package_sha256':hashlib.sha256(raw).hexdigest(),'fig2_sha256':hashlib.sha256(fig).hexdigest(),'n_blocks':len(blocks),'blocks':blocks,'ngc1090_candidates':[b for b in blocks if b['ngc1090_name_signal']],'boundary':'Block-name/structure enumeration only; no data-value extraction or rendering.'}
OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
