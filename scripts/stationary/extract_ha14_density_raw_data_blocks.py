#!/usr/bin/env python3
"""Persist the black-vector blocks between axes and legend/colored curves in Ha14 fig-density.eps.
Static source extraction only; no PostScript execution.
"""
from __future__ import annotations
import io,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/1407.1744';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_density_raw_data_blocks_v1.txt')

def main():
 req=urllib.request.Request(URL,headers={'User-Agent':UA})
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');lines=tf.extractfile(tf.getmember('fig-density.eps')).read().decode('latin-1','replace').splitlines()
 # 1-based source ranges localized from prior audits: after top/bottom axes and before legends/colored thresholds.
 ranges=[('TOP_POST_AXES_PRE_LEGEND',218,379),('BOTTOM_POST_AXES_PRE_LEGEND',661,865),('BOTTOM_LATE_BLACK_PRE_COLOR',866,955)]
 out=[]
 for name,a,b in ranges:
  out.append(f'===== {name} lines {a}-{b} =====')
  for n in range(a,b+1):
   if 1<=n<=len(lines):out.append(f'{n:04d}: {lines[n-1]}')
  out.append('')
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text('\n'.join(out)+'\n',encoding='utf-8')
 print(f'wrote {OUT} with {len(out)} records')
if __name__=='__main__':main()
