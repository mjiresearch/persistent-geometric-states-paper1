#!/usr/bin/env python3
"""Open the official FEASTS 2025 public release folder in a fresh browser.

Uses only the password-free public AnyShare UI. Enters the single shared root
folder and records visible file/folder names plus redacted public API responses.
No login, credentials, write action, or science analysis.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL='https://disk.pku.edu.cn/link/AA7305FC3F095848F198DD20FDE3E43BF6'
ROOT='size-mass-relation(Wang+25)'
OUT=Path('validation/stationary/feasts2025_public_release_folder_v1.json')
SENSITIVE=('token','authorization','credential','cookie','secret','password','session')

def redact(x):
 if isinstance(x,dict):
  return {k:('***REDACTED***' if any(s in str(k).lower() for s in SENSITIVE) else redact(v)) for k,v in x.items()}
 if isinstance(x,list):return [redact(v) for v in x]
 return x

def main():
 out={'status':'FEASTS2025_PUBLIC_RELEASE_FOLDER_OPEN','share_url':URL,'root_folder':ROOT}
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);context=browser.new_context(ignore_https_errors=True);page=context.new_page();net=[];bodies=[]
  def on_response(resp):
   if 'disk.pku.edu.cn' not in resp.url:return
   if '/api/' in resp.url:
    net.append({'method':resp.request.method,'url':resp.url,'status':resp.status})
    ct=(resp.headers.get('content-type') or '').lower()
    if 'json' in ct and any(k in resp.url for k in ('entry-item','sub_objects','folders','shared-link')):
     try:bodies.append({'url':resp.url,'status':resp.status,'json':redact(resp.json())})
     except Exception:pass
  page.on('response',on_response)
  try:
   page.goto(URL,wait_until='domcontentloaded',timeout=90000);page.wait_for_timeout(10000)
   before=' '.join(page.locator('body').inner_text(timeout=10000).split())[:30000]
   loc=page.get_by_text(ROOT,exact=True)
   count=loc.count();out['root_text_matches']=count
   if count<1:raise RuntimeError('root folder text not found')
   try:loc.first.dblclick(timeout=10000)
   except Exception:loc.first.click(timeout=10000)
   page.wait_for_timeout(10000)
   after=' '.join(page.locator('body').inner_text(timeout=10000).split())[:60000]
   out.update(before_visible_text=before,after_visible_text=after,current_url=page.url)
  except Exception as e:out.update(status='FEASTS2025_PUBLIC_RELEASE_FOLDER_OPEN_FAILED',error_type=type(e).__name__,error=str(e))
  # de-dup public network rows
  seen=set();uniq=[]
  for x in net:
   k=(x['method'],x['url'],x['status'])
   if k not in seen:seen.add(k);uniq.append(x)
  out['public_api_network']=uniq;out['public_json_responses']=bodies
  context.close();browser.close()
 out['boundary']='Fresh unauthenticated password-free public UI navigation only; no credentials, write operations, persistence quantities, or blind outcomes.'
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':out['status'],'root_text_matches':out.get('root_text_matches'),'after_visible_text':out.get('after_visible_text','')[:5000],'current_url':out.get('current_url')},indent=2,ensure_ascii=False))
if __name__=='__main__':main()
