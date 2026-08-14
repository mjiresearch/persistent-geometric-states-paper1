#!/usr/bin/env python3
"""Inventory the official FEASTS 2024 public `profiles` folder."""
from __future__ import annotations
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
URL='https://disk.pku.edu.cn/link/AAF401EFBFF9A2493CAA7678F24E9BCF28'
ROOT='total_and_diffuseHI(Wang+24a,b)'; SUB='profiles'
OUT=Path('validation/stationary/feasts2024_profiles_folder_v1.json')
SENSITIVE=('token','authorization','credential','cookie','secret','password','session')
def redact(x):
 if isinstance(x,dict):return {k:('***REDACTED***' if any(s in str(k).lower() for s in SENSITIVE) else redact(v)) for k,v in x.items()}
 if isinstance(x,list):return [redact(v) for v in x]
 return x
def click_last(page,text):
 loc=page.get_by_text(text,exact=True);n=loc.count()
 if n<1:raise RuntimeError(f'{text!r} not found')
 try:loc.nth(n-1).dblclick(timeout=10000)
 except Exception:loc.nth(n-1).click(timeout=10000)
 page.wait_for_timeout(8000)
def main():
 out={'status':'FEASTS2024_PROFILES_FOLDER_OPEN','share_url':URL,'root_folder':ROOT,'subfolder':SUB}
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);c=b.new_context(ignore_https_errors=True);page=c.new_page();net=[];bodies=[]
  def on_response(r):
   if 'disk.pku.edu.cn' not in r.url or '/api/' not in r.url:return
   net.append({'method':r.request.method,'url':r.url,'status':r.status})
   if 'json' in (r.headers.get('content-type') or '').lower() and any(k in r.url for k in ('entry-item','sub_objects','shared-link')):
    try:bodies.append({'url':r.url,'status':r.status,'json':redact(r.json())})
    except Exception:pass
  page.on('response',on_response)
  try:
   page.goto(URL,wait_until='domcontentloaded',timeout=90000);page.wait_for_timeout(10000);click_last(page,ROOT)
   root_text=' '.join(page.locator('body').inner_text(timeout=10000).split())[:60000]
   click_last(page,SUB)
   sub_text=' '.join(page.locator('body').inner_text(timeout=10000).split())[:100000]
   out.update(root_visible_text=root_text,profiles_visible_text=sub_text,current_url=page.url)
  except Exception as e:out.update(status='FEASTS2024_PROFILES_FOLDER_OPEN_FAILED',error_type=type(e).__name__,error=str(e))
  seen=set();uniq=[]
  for x in net:
   k=(x['method'],x['url'],x['status'])
   if k not in seen:seen.add(k);uniq.append(x)
  out['public_api_network']=uniq;out['public_json_responses']=bodies;c.close();b.close()
 out['boundary']='Fresh password-free public UI inventory only; no credentials, writes, raster digitization, persistence quantities, or blind outcomes.'
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':out['status'],'profiles_visible_text':out.get('profiles_visible_text','')[:12000]},indent=2,ensure_ascii=False))
if __name__=='__main__':main()
