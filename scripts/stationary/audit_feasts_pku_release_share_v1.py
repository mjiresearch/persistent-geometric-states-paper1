#!/usr/bin/env python3
"""Audit the official FEASTS I/II PKU data-release share linked from FEASTS/LVgal.

Inventory only: resolve the share page, record HTML/script/link structure, and
identify downloadable/data-like endpoints. No science fitting or blind outcomes.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen

URL='https://disk.pku.edu.cn/link/AAF401EFBFF9A2493CAA7678F24E9BCF28'
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/feasts_pku_release_share_audit_v1.json')

def main():
    out={'status':'FEASTS_PKU_RELEASE_SHARE_AUDIT','source_url':URL}
    try:
        req=Request(URL,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8'})
        with urlopen(req,timeout=90) as h:
            b=h.read(8_000_000); final=h.geturl(); headers=dict(h.headers.items())
        text=b.decode('utf-8','replace')
        hrefs=re.findall(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']',text,re.I)
        urls=[]
        for x in hrefs:
            u=urljoin(final,x)
            if u not in urls: urls.append(u)
        raw_urls=re.findall(r'https?://[^\s"\'<>]+',text)
        for u in raw_urls:
            u=u.rstrip('),;]')
            if u not in urls: urls.append(u)
        keys=('download','api','share','file','list','dir','folder','zip','fits','csv','txt','dat','profile','ngc','feasts','things')
        out.update(final_url=final,http_status=200,headers=headers,bytes=len(b),n_urls=len(urls),urls=urls,
                   priority_urls=[u for u in urls if any(k in u.lower() for k in keys)],
                   html_head=re.sub(r'\s+',' ',text[:30000]).strip())
        out['n_priority_urls']=len(out['priority_urls'])
    except Exception as e:
        out.update(status='FEASTS_PKU_RELEASE_SHARE_FETCH_FAILED',error_type=type(e).__name__,error=str(e))
    out['boundary']='Official release-page inventory only; no science profile fitting, persistence parameters, or blind outcomes.'
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
