#!/usr/bin/env python3
"""Record the exact 18-file Barbieri+2005 arXiv source inventory.

Continuation after the Ba05 route audit found no PS/EPS/numeric candidates.
This does not repeat profile searching; it records file names, extensions,
sizes, hashes, magic bytes, and TeX graphics references so the source-asset
format is unambiguous and durably checkpointed.
"""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/astro-ph/0504534';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/ba05_source_inventory_v1.json')
def main():
 req=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');rows=[];refs=[]
 for m in tf.getmembers():
  if not m.isfile():continue
  b=tf.extractfile(m).read();ext=''.join(Path(m.name).suffixes).lower();rec={'name':m.name,'suffixes':Path(m.name).suffixes,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'magic_hex':b[:24].hex(),'magic_text':b[:80].decode('latin-1','replace')}
  if m.name.lower().endswith('.tex'):
   t=b.decode('latin-1','replace');gre=[]
   for i,line in enumerate(t.splitlines(),1):
    if re.search(r'(includegraphics|epsfig|psfig|plotone|plottwo)',line,re.I):gre.append({'line':i,'text':line[:1000]})
   rec['graphics_reference_lines']=gre;refs.extend([{'tex':m.name,**x} for x in gre])
  rows.append(rec)
 out={'status':'BA05_SOURCE_INVENTORY_COMPLETE','source':'Barbieri et al. 2005 / astro-ph/0504534','source_package_sha256':hashlib.sha256(raw).hexdigest(),'n_files':len(rows),'files':rows,'all_tex_graphics_references':refs,'boundary':'Archive inventory only; no OCR, rendering, raster digitization, map reconstruction, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
