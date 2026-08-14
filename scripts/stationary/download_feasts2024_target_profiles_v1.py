#!/usr/bin/env python3
"""Download official FEASTS 2024 native text profiles for NGC2841/NGC3198.

Uses only the password-free public AnyShare UI. Files are preserved unchanged
with SHA-256 provenance; this script records text heads but does not interpret
columns, fit profiles, or inspect persistence/blind outcomes.
"""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

URL='https://disk.pku.edu.cn/link/AAF401EFBFF9A2493CAA7678F24E9BCF28'
ROOT='total_and_diffuseHI(Wang+24a,b)';SUB='profiles'
FILES={
 'NGC2841':'ngc2841.msc.corrected.reg2fu.dprof.txt',
 'NGC3198':'ngc3198.msc.corrected.reg2fu.dprof.txt',
}
OUTDIR=Path('data/stationary/source_reconstruction/feasts2024_profiles')
AUDIT=Path('validation/stationary/feasts2024_target_profiles_download_v1.json')

def click_last(page,text):
 loc=page.get_by_text(text,exact=True);n=loc.count()
 if n<1:raise RuntimeError(f'{text!r} not found')
 try:loc.nth(n-1).dblclick(timeout=10000)
 except Exception:loc.nth(n-1).click(timeout=10000)
 page.wait_for_timeout(6000)

def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def download_one(browser,galaxy,name,tmpdir):
 c=browser.new_context(ignore_https_errors=True,accept_downloads=True);page=c.new_page();attempts=[]
 page.goto(URL,wait_until='domcontentloaded',timeout=90000);page.wait_for_timeout(9000);click_last(page,ROOT);click_last(page,SUB)
 loc=page.get_by_text(name,exact=True);n=loc.count()
 if n<1:raise RuntimeError(f'{name} not found in profiles folder')
 row=loc.nth(n-1)
 dest=tmpdir/name
 try:
  with page.expect_download(timeout=10000) as info:row.dblclick(timeout=10000)
  info.value.save_as(dest);attempts.append('file_dblclick_download')
 except Exception as e:
  attempts.append('file_dblclick_no_download:'+type(e).__name__);page.wait_for_timeout(2000)
  dl=page.get_by_text('Download',exact=True)
  if dl.count()<1:raise RuntimeError(f'no Download control after selecting {name}; attempts={attempts}; visible='+(' '.join(page.locator('body').inner_text().split())[:20000]))
  with page.expect_download(timeout=20000) as info:dl.last.click(timeout=10000)
  info.value.save_as(dest);attempts.append('Download_control_download')
 c.close();return dest,attempts

def main():
 OUTDIR.mkdir(parents=True,exist_ok=True);AUDIT.parent.mkdir(parents=True,exist_ok=True);tmp=Path('/tmp/feasts2024_profiles');tmp.mkdir(parents=True,exist_ok=True)
 result={'status':'FEASTS2024_TARGET_PROFILES_DOWNLOAD','share_url':URL,'root_folder':ROOT,'subfolder':SUB,'files':[]}
 try:
  with sync_playwright() as p:
   b=p.chromium.launch(headless=True,args=['--no-sandbox'])
   for g,n in FILES.items():
    src,attempts=download_one(b,g,n,tmp);dst=OUTDIR/n;shutil.copyfile(src,dst);text=dst.read_text(encoding='utf-8',errors='replace')
    result['files'].append({'galaxy':g,'filename':n,'bytes':dst.stat().st_size,'sha256':sha(dst),'output':str(dst),'download_attempts':attempts,'text_head':text[:12000]})
   b.close()
  result['status']='FEASTS2024_TARGET_PROFILES_DOWNLOADED'
 except Exception as e:result.update(status='FEASTS2024_TARGET_PROFILES_DOWNLOAD_FAILED',error_type=type(e).__name__,error=str(e))
 result['boundary']='Official password-free public native text profiles only; no column interpretation, raster digitization, persistence parameters, or blind outcomes in this download step.'
 AUDIT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':result['status'],'files':[{k:x[k] for k in ('galaxy','filename','bytes','sha256')} for x in result['files']], 'error':result.get('error')},indent=2))
 if result['status']!='FEASTS2024_TARGET_PROFILES_DOWNLOADED':raise SystemExit(2)
if __name__=='__main__':main()
