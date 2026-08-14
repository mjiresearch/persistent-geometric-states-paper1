#!/usr/bin/env python3
"""Extract narrow public AnyShare link-token flow from the public main JS bundle."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request,urlopen
URL='https://disk.pku.edu.cn/anyshare/static/js/main.2582f47f.chunk.js'
NEEDLES=['link_token:','useLinkOpenApi','password_required','oauth2Token','shared-link/v1/links/{link_id}','shared-link/v1/document/anonymous/{link_id}']
OUT=Path('validation/stationary/anyshare_link_token_flow_v1.json')
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
def main():
 with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=90) as h:b=h.read(20_000_000)
 t=b.decode('utf-8','replace'); hits=[]
 for needle in NEEDLES:
  start=0
  while True:
   i=t.find(needle,start)
   if i<0:break
   hits.append({'needle':needle,'index':i,'context':t[max(0,i-3200):min(len(t),i+5200)]})
   start=i+1
 out={'status':'ANYSHARE_LINK_TOKEN_FLOW_EXTRACTED','source_url':URL,'hits':hits,'boundary':'Public anonymous-share client-flow inspection only; no private data, credentials, writes, or science outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
