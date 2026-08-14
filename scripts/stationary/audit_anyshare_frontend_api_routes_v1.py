#!/usr/bin/env python3
"""Inspect the public AnyShare web-client JS for anonymous-link API routes.

This is a narrow protocol-discovery audit for the official FEASTS public share.
It does not access private data or science outcomes.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.request import Request,urlopen

BASE='https://disk.pku.edu.cn/anyshare/'
ASSETS=['static/js/main.2582f47f.chunk.js','static/js/4.3d9d57ef.chunk.js']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/anyshare_frontend_api_routes_v1.json')
KEYS=('shared-link','anonymous','link_id','download','children','entry','entries','folder','document','api/')

def main():
    rows=[]
    for asset in ASSETS:
        url=BASE+asset
        try:
            with urlopen(Request(url,headers={'User-Agent':UA}),timeout=90) as h: b=h.read(20_000_000)
            t=b.decode('utf-8','replace')
            urls=sorted(set(re.findall(r'["\']([^"\']{0,180}(?:shared-link|anonymous|download|children|entries|folder|document|api/)[^"\']{0,180})["\']',t,re.I)))
            route_like=sorted(set(re.findall(r'[/][A-Za-z0-9_{}:$?.=&%+\-/.]{4,220}',t)))
            route_like=[x for x in route_like if any(k in x.lower() for k in KEYS)][:1000]
            rows.append({'asset':asset,'url':url,'bytes':len(b),'string_hits':urls[:1000],'route_like_hits':route_like})
        except Exception as e:
            rows.append({'asset':asset,'url':url,'error_type':type(e).__name__,'error':str(e)})
    out={'status':'ANYSHARE_FRONTEND_API_ROUTES_AUDITED','assets':rows,'boundary':'Public web-client route inspection only; official FEASTS anonymous share, no private data or science outcomes.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__': main()
