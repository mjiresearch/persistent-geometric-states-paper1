#!/usr/bin/env python3
"""Read-only probe of the official FEASTS AnyShare anonymous-link endpoint."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

HOST='https://disk.pku.edu.cn'
LINK='AAF401EFBFF9A2493CAA7678F24E9BCF28'
SHARE=f'{HOST}/link/{LINK}'
URL=f'{HOST}/api/shared-link/v1/document/anonymous/{LINK}'
OUT=Path('validation/stationary/feasts_anyshare_anonymous_get_probe_v1.json')
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'

def one(method):
    req=Request(URL,method=method,headers={'User-Agent':UA,'Accept':'application/json, text/plain, */*','Referer':SHARE})
    try:
        with urlopen(req,timeout=60) as h:
            b=h.read(2_000_000)
            r={'method':method,'status':getattr(h,'status',200),'final_url':h.geturl(),'headers':dict(h.headers.items()),'body_text':b.decode('utf-8','replace')}
    except HTTPError as e:
        b=e.read(2_000_000);r={'method':method,'status':e.code,'headers':dict(e.headers.items()),'body_text':b.decode('utf-8','replace')}
    except Exception as e:r={'method':method,'error_type':type(e).__name__,'error':str(e)}
    try:r['json']=json.loads(r.get('body_text',''))
    except Exception:pass
    return r

def main():
    out={'status':'FEASTS_ANYSHARE_ANONYMOUS_READONLY_PROBE','link_id':LINK,'endpoint':URL,'requests':[one('OPTIONS'),one('GET')],'boundary':'Read-only public anonymous-share protocol probe only; no PUT, DELETE, authentication bypass, private data, or science outcomes.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
