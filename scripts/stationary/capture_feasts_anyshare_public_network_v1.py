#!/usr/bin/env python3
"""Capture the intended public AnyShare network flow for official FEASTS releases.

A fresh unauthenticated Chromium context opens the two official, password-free
FEASTS public shares. We record only disk.pku.edu.cn request URL/method/status,
redacted JSON response structure, visible public text, and localStorage key names.
Token/cookie/authorization values are never persisted. This is acquisition and
provenance discovery only; no science outcomes or persistence quantities.
"""
from __future__ import annotations
import json,re,time
from pathlib import Path
from playwright.sync_api import sync_playwright

SHARES={
    'wang2024_diffuseHI':'https://disk.pku.edu.cn/link/AAF401EFBFF9A2493CAA7678F24E9BCF28',
    'wang2025_size_mass':'https://disk.pku.edu.cn/link/AA7305FC3F095848F198DD20FDE3E43BF6',
}
OUT=Path('validation/stationary/feasts_anyshare_public_network_v1.json')
SENSITIVE=('token','authorization','credential','cookie','secret','password','session')
INTERESTING=('api/','shared-link','efast','folder','sub_objects','file-download','document','link')

def redact(x):
    if isinstance(x,dict):
        out={}
        for k,v in x.items():
            kl=str(k).lower()
            out[k]='***REDACTED***' if any(s in kl for s in SENSITIVE) else redact(v)
        return out
    if isinstance(x,list): return [redact(v) for v in x]
    return x

def sanitize_text(text):
    # Best-effort removal of JWT/bearer-like opaque values from persisted text.
    text=re.sub(r'Bearer\s+[A-Za-z0-9._~+\-/=]+','Bearer ***REDACTED***',text,flags=re.I)
    text=re.sub(r'(["\']?(?:access_token|link_token|refresh_token|authorization)["\']?\s*[:=]\s*["\'])([^"\']+)',r'\1***REDACTED***',text,flags=re.I)
    return text

def main():
    all_rows=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        for label,url in SHARES.items():
            context=browser.new_context(ignore_https_errors=True)
            page=context.new_page(); events=[]; bodies=[]
            def on_response(resp):
                u=resp.url
                if 'disk.pku.edu.cn' not in u: return
                req=resp.request
                events.append({'method':req.method,'url':u,'status':resp.status,'resource_type':req.resource_type})
                if any(k in u.lower() for k in INTERESTING):
                    ct=(resp.headers.get('content-type') or '').lower()
                    if 'json' in ct:
                        try:
                            obj=resp.json(); bodies.append({'url':u,'status':resp.status,'json':redact(obj)})
                        except Exception:
                            try:bodies.append({'url':u,'status':resp.status,'text':sanitize_text(resp.text())[:12000]})
                            except Exception:pass
            page.on('response',on_response)
            nav_error=None
            try:
                page.goto(url,wait_until='domcontentloaded',timeout=90000)
                # Allow the React application to mint its normal anonymous token
                # and enumerate the public share. No clicks or credentials.
                page.wait_for_timeout(20000)
            except Exception as exc: nav_error=f'{type(exc).__name__}: {exc}'
            try: title=page.title()
            except Exception:title=''
            try: visible=' '.join(page.locator('body').inner_text(timeout=10000).split())[:30000]
            except Exception:visible=''
            try:
                ls=page.evaluate("Object.keys(window.localStorage).map(k => ({key:k,length:(window.localStorage.getItem(k)||'').length}))")
            except Exception:ls=[]
            # deduplicate network events while preserving order
            seen=set(); de=[]
            for e in events:
                key=(e['method'],e['url'],e['status'])
                if key not in seen:seen.add(key);de.append(e)
            all_rows.append({'label':label,'share_url':url,'nav_error':nav_error,'page_title':title,'visible_text':sanitize_text(visible),'local_storage_keys':ls,'network':de,'public_json_responses':bodies})
            context.close()
        browser.close()
    out={'status':'FEASTS_ANYSHARE_PUBLIC_NETWORK_CAPTURED','shares':all_rows,'boundary':'Fresh unauthenticated public-share browser flow only. Token/cookie/authorization values redacted and not persisted. No private data, writes, persistence parameters, or blind outcomes.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':out['status'],'shares':[{'label':r['label'],'nav_error':r['nav_error'],'n_network':len(r['network']),'n_json':len(r['public_json_responses']),'title':r['page_title']} for r in all_rows]},indent=2))

if __name__=='__main__':main()
