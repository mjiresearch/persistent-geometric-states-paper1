#!/usr/bin/env python3
import io,tarfile,urllib.request,json
from pathlib import Path
u='https://arxiv.org/e-print/astro-ph/0609148'
b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'PaperI'}),timeout=60).read()
with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as t:
 s=t.extractfile('f11.eps').read().decode('latin1','ignore')
lines=s.splitlines();defs=[x.strip() for x in lines if x.lstrip().startswith('/') or ' def' in x]
prog=[x.strip() for x in lines if x.strip() and not x.lstrip().startswith(('%','/'))]
out={'status':'CH06_F11_IDL_STRUCTURE_INSPECTED','defs':defs[:120],'program_lines':prog,'program_tail':prog[-140:]}
Path('validation/stationary/ch06_f11_idl_structure_v1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'program_tail':prog[-100:]},indent=2))
