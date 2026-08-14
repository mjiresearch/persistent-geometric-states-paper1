#!/usr/bin/env python3
"""Resolve the official FEASTS 2025 radial-profile data share through AnyShare API."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
HOST='https://disk.pku.edu.cn'; LINK='AA7305FC3F095848F198DD20FDE3E43BF6'
URL=f'{HOST}/api/shared-link/v1/links/{LINK}'
OUT=Path('validation/stationary/feasts_2025_radial_anyshare_link_resolution_v1.json')
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
def main():
 out={'status':'FEASTS_2025_RADIAL_ANYSHARE_LINK_RESOLUTION','link_id':LINK,'api_url':URL}
 try:
  with urlopen(Request(URL,headers={'User-Agent':UA,'Accept':'application/json'}),timeout=60) as h:
   b=h.read(2_000_000);out.update(http_status=getattr(h,'status',200),final_url=h.geturl(),content_type=h.headers.get('Content-Type',''),body_text=b.decode('utf-8','replace'))
   try:out['json']=json.loads(out['body_text'])
   except Exception:pass
 except HTTPError as e:
  b=e.read(2_000_000);out.update(status='FEASTS_2025_RADIAL_LINK_HTTP_ERROR',http_status=e.code,body_text=b.decode('utf-8','replace'))
 except Exception as e:out.update(status='FEASTS_2025_RADIAL_LINK_FETCH_FAILED',error_type=type(e).__name__,error=str(e))
 out['boundary']='Official public FEASTS radial-profile shared-link resolution only; no science fitting or blind outcomes.'
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
