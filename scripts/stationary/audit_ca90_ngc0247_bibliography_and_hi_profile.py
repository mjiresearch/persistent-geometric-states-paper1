#!/usr/bin/env python3
"""Resolve Ca90 / NGC0247 bibliography and audit the direct public H I profile route.

The repository's CDS-derived mapping currently associates Ca90 with AJ 100,394.
This script opens both Carignan & Puche 1990 AJ articles (100,394 and 100,641)
and the related Puche et al. Sculptor article at 100,1468, using the articles'
own native/text-layer content to identify the galaxy and profile product.

Frozen target is blind. Acquisition/provenance only: no rotation/persistence outcomes,
OCR, raster digitization, or source fitting.
"""
from __future__ import annotations
import csv,hashlib,json,re
from pathlib import Path
from urllib.request import Request,urlopen
import fitz

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
SA=Path('validation/stationary/sa96_original_source_provenance_audit_v1.json')
OUT=Path('validation/stationary/ca90_ngc0247_bibliography_hi_profile_audit_v1.json')
TXT=Path('validation/stationary/ca90_ngc0247_bibliography_hi_profile_audit_v1.txt')
ARTICLES={
 'CP90a_394':'https://articles.adsabs.harvard.edu/pdf/1990AJ....100..394C',
 'CP90b_641':'https://articles.adsabs.harvard.edu/pdf/1990AJ....100..641C',
 'PCB90_1468':'https://articles.adsabs.harvard.edu/pdf/1990AJ....100.1468P',
}
UA='PaperI-Ca90-NGC247-bibliography-audit/1.0'
def sha(b):return hashlib.sha256(b).hexdigest()
def fetch(u):
 with urlopen(Request(u,headers={'User-Agent':UA,'Accept':'application/pdf,*/*'}),timeout=60) as r:
  b=r.read();return b,{'requested_url':u,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':r.headers.get('Content-Type',''),'bytes':len(b),'sha256':sha(b)}
def contexts(text,patterns,window=450):
 low=text.lower();out=[];seen=set()
 for p in patterns:
  for m in re.finditer(re.escape(p.lower()),low):
   s=re.sub(r'\s+',' ',text[max(0,m.start()-window):min(len(text),m.end()+window)]).strip()
   if s not in seen:seen.add(s);out.append({'pattern':p,'context':s})
 return out[:120]
def inspect(label,b,meta):
 d=fitz.open(stream=b,filetype='pdf');pages=[];texts=[]
 for i,p in enumerate(d):
  t=p.get_text('text') or '';texts.append(t);pages.append({'page_index':i,'text_chars':len(t),'n_images':len(p.get_images(full=True)),'n_drawings':len(p.get_drawings())})
 text='\n'.join(texts)
 pats=['NGC 247','NGC 7793','NGC 300','NGC 0300','surface density','surface-density','radial distribution','radial profile','H I distribution','HI distribution','gas distribution','helium','4/3','1.33','1.4','Fig. 4','Fig. 5','Fig. 6','Fig. 7','Fig. 8','Figure 4','Figure 5','Figure 6','Figure 7','Figure 8']
 return {'label':label,'pdf':meta,'page_count':len(d),'pages':pages,'native_text_chars':len(text),'first_text':re.sub(r'\s+',' ',text[:3500]).strip(),'contexts':contexts(text,pats)}
def main():
 with REF.open(newline='',encoding='utf-8-sig') as f:refs=list(csv.DictReader(f))
 tar=[r for r in refs if r.get('galaxy')=='NGC0247' and r.get('sparc_ref_id')=='Ca90']
 if len(tar)!=1 or tar[0].get('stationary_role')!='blind':raise RuntimeError(f'Frozen Ca90 mapping changed: {tar}')
 sa=json.loads(SA.read_text(encoding='utf-8'))
 # Preserve exact Sanders bibliography evidence already archived.
 bib=[]
 for h in sa.get('bibliography_like_hits',[]):
  if h.get('line') in {917,918,919,920,1027,1029}:bib.append(h)
 attempts=[];audits=[]
 for label,u in ARTICLES.items():
  try:
   b,m=fetch(u);attempts.append({'label':label,**m});audits.append(inspect(label,b,m))
  except Exception as e:attempts.append({'label':label,'requested_url':u,'error':repr(e)})
 result={'status':'CA90_NGC0247_BIBLIOGRAPHY_HI_PROFILE_AUDIT_COMPLETE','galaxy':'NGC0247','stationary_role':'blind','sparc_ref_id':'Ca90','frozen_mapping':tar[0],'sandars1996_bibliography_evidence':bib,'fetch_attempts':attempts,'article_audits':audits,'boundary':'Frozen blind target: bibliography and source-profile recoverability only. No blind rotation/persistence outcome inspection, OCR, raster digitization, source fitting, or parameter selection. L_A and C_A remain locked.'}
 OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 lines=[f"status={result['status']}",'FROZEN '+json.dumps(tar[0],sort_keys=True)]
 for h in bib:lines.append('SA96 '+json.dumps(h,ensure_ascii=False))
 for a in attempts:lines.append('ATTEMPT '+json.dumps(a,sort_keys=True))
 for a in audits:
  lines.append('ARTICLE '+json.dumps({'label':a['label'],'url':a['pdf']['final_url'],'pages':a['page_count'],'native_text_chars':a['native_text_chars'],'page_structures':a['pages'],'first_text':a['first_text']},ensure_ascii=False))
  for c in a['contexts']:lines.append(a['label']+'_CONTEXT '+json.dumps(c,ensure_ascii=False))
 TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'attempts':len(attempts),'audits':len(audits),'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
