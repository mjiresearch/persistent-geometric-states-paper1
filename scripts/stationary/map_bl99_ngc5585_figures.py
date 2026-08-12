#!/usr/bin/env python3
"""Map Bl99 source figure captions to PostScript assets and static vector strings."""
from __future__ import annotations
import hashlib,io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen

URL='https://arxiv.org/e-print/astro-ph/9911223';UA='PaperI-Bl99-figure-map/1.0'
OUT=Path('validation/stationary/bl99_ngc5585_figure_map_v1.json');TXT=Path('validation/stationary/bl99_ngc5585_figure_map_v1.txt')
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=60) as r:payload=r.read();final=r.geturl()
 blobs={}
 with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
  for m in tf.getmembers():
   if m.isfile():
    f=tf.extractfile(m);blobs[m.name]=f.read() if f else b''
 tex='\n'.join(b.decode('latin-1',errors='replace') for n,b in blobs.items() if n.lower().endswith(('.tex','.ltx')))
 # Capture AASTeX plot commands and captions in order.
 plots=[]
 for m in re.finditer(r'\\plotone\{([^}]+)\}|\\plottwo\{([^}]+)\}\{([^}]+)\}|\\epsfbox\{([^}]+)\}|\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',tex,re.I):
  refs=[x for x in m.groups() if x];
  after=tex[m.end():m.end()+3000]
  cm=re.search(r'\\caption\{(.*?)\}(?:\s*\\label|\s*\\end\{figure)',after,re.I|re.S)
  cap=re.sub(r'\s+',' ',cm.group(1)).strip() if cm else ''
  plots.append({'refs':refs,'caption':cap,'char':m.start()})
 # Fallback: source uses \plotfiddle or other constructs; capture all figure env captions and local filenames.
 envs=[]
 for m in re.finditer(r'\\begin\{figure\}(.*?)\\end\{figure\}',tex,re.I|re.S):
  block=m.group(1);cm=re.search(r'\\caption\{(.*?)\}',block,re.I|re.S)
  cap=re.sub(r'\s+',' ',cm.group(1)).strip() if cm else ''
  refs=re.findall(r'(Blais-Ouellette\.fig\d+\.ps)',block,re.I)
  envs.append({'refs':refs,'caption':cap,'block':re.sub(r'\s+',' ',block).strip()[:1800]})
 assets=[]
 for n,b in sorted(blobs.items()):
  if re.search(r'fig\d+\.ps$',n,re.I):
   s=b.decode('latin-1',errors='replace');low=s.lower()
   strings=re.findall(r'\(([^()]*)\)\s*(?:show|[A-Za-z]{1,4})',s)
   interesting=[x for x in strings if any(k in x.lower() for k in ['gas','h i','hi','radius','surface','density','kpc','km','disk','halo'])]
   assets.append({'name':n,'bytes':len(b),'sha256':sha(b),'image_ops':len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',low)),'interesting_strings':interesting[:100]})
 result={'status':'BL99_NGC5585_FIGURE_MAP_COMPLETE','source':{'url':final,'bytes':len(payload),'sha256':sha(payload)},'plot_commands':plots,'figure_environments':envs,'assets':assets,'boundary':'Static source map only; no source execution, OCR, raster digitization, blind outcome inspection, or persistence fitting.'}
 OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 lines=[f"status={result['status']}"]
 for x in plots:lines.append('PLOT '+json.dumps(x,ensure_ascii=False))
 for x in envs:lines.append('ENV '+json.dumps(x,ensure_ascii=False))
 for x in assets:lines.append('ASSET '+json.dumps(x,ensure_ascii=False))
 TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'plots':len(plots),'envs':len(envs),'assets':len(assets),'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
