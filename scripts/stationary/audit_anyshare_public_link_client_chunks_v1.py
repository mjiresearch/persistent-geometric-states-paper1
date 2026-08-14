#!/usr/bin/env python3
"""Trace public anonymous-link access flow in AnyShare lazy-loaded frontend chunks.

Downloads only the public JS assets referenced by the official FEASTS AnyShare
page and records narrow contexts for public-link/token/API strings.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request,urlopen

BASE='https://disk.pku.edu.cn/anyshare/static/js/'
ASSETS={
 '0':'0.0ca06775.chunk.js','1':'1.5bcd84a3.chunk.js','5':'5.661d900d.chunk.js','6':'6.6c16f0aa.chunk.js',
 '7':'7.fca45225.chunk.js','8':'8.45e90497.chunk.js','9':'9.866bba2a.chunk.js','10':'10.6942bb96.chunk.js'}
NEEDLES=['shared-link/v1/links','shared-link/v1/document/anonymous','password_required','link_id','Authorization','authorization','token expired','access_token','anonymous_token','X-AS-Authorization']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/anyshare_public_link_client_chunks_v1.json')

def main():
 rows=[]
 for key,name in ASSETS.items():
  url=BASE+name
  try:
   with urlopen(Request(url,headers={'User-Agent':UA}),timeout=90) as h:b=h.read(20_000_000)
   t=b.decode('utf-8','replace'); hits=[]
   for needle in NEEDLES:
    start=0
    while True:
     i=t.find(needle,start)
     if i<0:break
     hits.append({'needle':needle,'index':i,'context':t[max(0,i-1400):min(len(t),i+2200)]})
     start=i+1
   rows.append({'chunk':key,'asset':name,'bytes':len(b),'n_hits':len(hits),'hits':hits})
  except Exception as e: rows.append({'chunk':key,'asset':name,'error_type':type(e).__name__,'error':str(e)})
 out={'status':'ANYSHARE_PUBLIC_LINK_CLIENT_CHUNKS_AUDITED','assets':rows,'boundary':'Public frontend protocol tracing only; no private data, credential guessing, write operations, or science outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
