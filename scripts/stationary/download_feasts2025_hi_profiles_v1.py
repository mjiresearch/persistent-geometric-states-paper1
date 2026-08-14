#!/usr/bin/env python3
"""Download the official FEASTS 2025 machine-readable H I profile release.

Uses only the password-free public AnyShare UI linked by FEASTS/LVgal. The
original ECSV is preserved byte-for-byte with SHA-256 provenance. The script
also records its ECSV metadata/schema and NGC3198 row count/range without
looking at rotation residuals or any persistence-model quantity.
"""
from __future__ import annotations
import hashlib,json,re,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL='https://disk.pku.edu.cn/link/AA7305FC3F095848F198DD20FDE3E43BF6'
ROOT='size-mass-relation(Wang+25)'
NAME='HIprof_wang25.ecsv'
OUT=Path('data/stationary/source_reconstruction/feasts2025_HIprof_wang25.ecsv')
AUDIT=Path('validation/stationary/feasts2025_hi_profiles_download_v1.json')

def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def parse_ecsv(p):
 text=p.read_text(encoding='utf-8-sig',errors='replace')
 lines=text.splitlines(); header=[x for x in lines if x.startswith('#')]
 data=[x for x in lines if x.strip() and not x.startswith('#')]
 # ECSV normally has one un-commented column-name row followed by data rows.
 columns=re.split(r'\s+',data[0].strip()) if data else []
 rows=[]
 for line in data[1:]:
  vals=re.split(r'\s+',line.strip())
  if len(vals)==len(columns): rows.append(dict(zip(columns,vals)))
 name_keys=[k for k in columns if k.lower() in ('name','galaxy','gal','obj','object','source') or 'name' in k.lower()]
 target=[]
 for r in rows:
  hay=' '.join(r.get(k,'') for k in name_keys) if name_keys else ' '.join(r.values())
  if re.sub(r'[^a-z0-9]','',hay.lower()).find('ngc3198')>=0:target.append(r)
 numeric_summary={}
 for c in columns:
  vals=[]
  for r in target:
   try:vals.append(float(r[c]))
   except Exception:pass
  if vals:numeric_summary[c]={'n_numeric':len(vals),'min':min(vals),'max':max(vals)}
 return {'n_header_lines':len(header),'header_lines':header[:500],'columns':columns,'n_rows_parsed':len(rows),'name_keys':name_keys,'n_ngc3198_rows':len(target),'ngc3198_numeric_ranges':numeric_summary,'ngc3198_preview':target[:5]}

def enter_folder(page):
 page.goto(URL,wait_until='domcontentloaded',timeout=90000);page.wait_for_timeout(10000)
 loc=page.get_by_text(ROOT,exact=True);n=loc.count()
 if n<1:raise RuntimeError('shared root folder not found')
 try:loc.nth(n-1).dblclick(timeout=10000)
 except Exception:loc.nth(n-1).click(timeout=10000)
 page.wait_for_timeout(8000)

def try_download(page,tmpdir):
 fileloc=page.get_by_text(NAME,exact=True);n=fileloc.count()
 if n<1:raise RuntimeError('ECSV file row not found')
 row=fileloc.nth(n-1)
 attempts=[]
 # AnyShare may download on double click or select/open a preview first.
 try:
  with page.expect_download(timeout=12000) as info: row.dblclick(timeout=10000)
  d=info.value;dest=tmpdir/NAME;d.save_as(dest);return dest,attempts+['file_dblclick_download']
 except Exception as e:attempts.append('file_dblclick_no_download:'+type(e).__name__)
 page.wait_for_timeout(3000)
 # If a preview/action surface appeared, use its public Download control.
 for label in ('Download','download'):
  loc=page.get_by_text(label,exact=True)
  if loc.count():
   try:
    with page.expect_download(timeout=20000) as info:loc.last.click(timeout=10000)
    d=info.value;dest=tmpdir/NAME;d.save_as(dest);return dest,attempts+[f'{label}_control_download']
   except Exception as e:attempts.append(f'{label}_control_no_download:'+type(e).__name__)
 # Return visible state for fail-closed diagnosis.
 visible=' '.join(page.locator('body').inner_text(timeout=10000).split())[:30000]
 raise RuntimeError('public UI did not yield a download; attempts='+repr(attempts)+' visible='+visible)

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True);AUDIT.parent.mkdir(parents=True,exist_ok=True)
 tmpdir=Path('/tmp/feasts2025_public');tmpdir.mkdir(parents=True,exist_ok=True)
 result={'status':'FEASTS2025_HI_PROFILES_DOWNLOAD','share_url':URL,'root_folder':ROOT,'filename':NAME}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,args=['--no-sandbox']);context=browser.new_context(ignore_https_errors=True,accept_downloads=True);page=context.new_page()
   enter_folder(page);src,attempts=try_download(page,tmpdir);context.close();browser.close()
  shutil.copyfile(src,OUT)
  result.update(status='FEASTS2025_HI_PROFILES_DOWNLOADED',download_attempts=attempts,bytes=OUT.stat().st_size,sha256=sha256(OUT),output=str(OUT),ecsv=parse_ecsv(OUT))
 except Exception as e:
  result.update(status='FEASTS2025_HI_PROFILES_DOWNLOAD_FAILED',error_type=type(e).__name__,error=str(e))
 result['boundary']='Official password-free public machine-readable H I release only; no raster digitization, rotation residuals, persistence parameters, or blind outcomes.'
 AUDIT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({k:result.get(k) for k in ('status','bytes','sha256','output','error') if k in result},indent=2))
 if result['status']!='FEASTS2025_HI_PROFILES_DOWNLOADED':raise SystemExit(2)

if __name__=='__main__':main()
