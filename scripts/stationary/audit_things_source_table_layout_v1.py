#!/usr/bin/env python3
"""Capture Walter+2008 source-table headers and target rows for THINGS QC.

This is metadata layout discovery only. It records source text around the galaxy
properties, image-properties, and global-HI comparison tables so downstream
parsers can use named columns rather than hand-coded positions.
"""
from __future__ import annotations
import io,json,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/0810.2125';UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/things_walter2008_source_table_layout_v1.json')
RANGES={'galaxy_properties':(900,980),'image_properties':(1300,1385),'global_hi':(1430,1515)}
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as tf:
  m=next(x for x in tf.getmembers() if x.name.endswith('THINGS_master_astroph.tex'))
  lines=tf.extractfile(m).read().decode('latin-1','replace').splitlines()
 blocks={}
 for name,(a,b) in RANGES.items():
  blocks[name]={'start_line':a,'end_line':b,'lines':[{'line':i,'text':lines[i-1]} for i in range(a,min(b,len(lines))+1)]}
 result={'status':'WALTER2008_THINGS_SOURCE_TABLE_LAYOUT_AUDITED','arxiv':ARXIV,'source_file':m.name,'blocks':blocks,'boundary':'Source-table metadata layout only; no science pixels, reconstructed profiles, velocities, residuals, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
