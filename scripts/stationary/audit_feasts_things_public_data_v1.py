#!/usr/bin/env python3
"""Inventory the public FEASTS+THINGS data page linked by Wang et al. 2024.

Acquisition/provenance audit only. No persistence quantities or blind outcomes.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen

URL='https://kavli.pku.edu.cn/~jwang/FEASTS_data.html'
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/feasts_things_public_data_audit_v1.json')
TOKENS=('profile','radial','sigma','surface','hi','things','w08','w24','ngc2841','ngc3198','2841','3198','fits','csv','txt','dat','zip','tar')

def main():
    result={'status':'FEASTS_THINGS_PUBLIC_DATA_AUDIT','source_url':URL,'links':[],'priority_links':[]}
    try:
        with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=60) as h:
            body=h.read(5_000_000)
            result.update(final_url=h.geturl(),http_status=getattr(h,'status',200),content_type=h.headers.get('Content-Type',''),bytes=len(body))
        text=body.decode('utf-8','replace')
        hrefs=re.findall(r'href\s*=\s*["\']([^"\']+)["\']',text,re.I)
        links=[]
        for href in hrefs:
            u=urljoin(result['final_url'],href)
            if u not in links: links.append(u)
        result['links']=links
        result['priority_links']=[u for u in links if any(t in u.lower().replace('_','') for t in TOKENS)]
        result['n_links']=len(links); result['n_priority_links']=len(result['priority_links'])
        result['html_head']=re.sub(r'\s+',' ',text[:12000]).strip()
    except Exception as exc:
        result['status']='FEASTS_THINGS_PUBLIC_DATA_AUDIT_FETCH_FAILED'
        result['error_type']=type(exc).__name__; result['error']=str(exc)
    result['boundary']='Public source inventory only; no profile fitting, persistence parameters, or blind outcomes.'
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
