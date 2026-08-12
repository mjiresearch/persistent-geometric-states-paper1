#!/usr/bin/env python3
"""Audit original Co91 / NGC5585 public H I profile route.

Reads only public article structure/text and source metadata. No OCR/raster
 digitization, no blind outcome inspection, no persistence fitting.
"""
from __future__ import annotations
import csv,hashlib,json,re
from pathlib import Path
from urllib.request import Request,urlopen
import fitz

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OUT=Path('validation/stationary/co91_ngc5585_public_hi_profile_route_v1.json')
TXT=Path('validation/stationary/co91_ngc5585_public_hi_profile_route_v1.txt')
URLS=['https://articles.adsabs.harvard.edu/pdf/1991AJ....102..904C','https://articles.adsabs.harvard.edu/full/1991AJ....102..904C','https://iopscience.iop.org/article/10.1086/115922/pdf','https://journals.uchicago.edu/doi/pdf/10.1086/115922']
UA='PaperI-Co91-NGC5585-audit/1.0'
def sha(b):return hashlib.sha256(b).hexdigest()
def fetch(u):
 with urlopen(Request(u,headers={'User-Agent':UA,'Accept':'application/pdf,text/html,*/*'}),timeout=45) as r:
  b=r.read();return b,{'requested_url':u,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':r.headers.get('Content-Type',''),'bytes':len(b),'sha256':sha(b)}
def contexts(text):
 pats=['surface density','surface-density','radial distribution','radial profile','H I distribution','HI distribution','gas distribution','helium','1.33','1.4','Figure 4','Figure 5','Figure 6','Figure 7','Figure 8','Figure 9','Fig. 4','Fig. 5','Fig. 6','Fig. 7','Fig. 8','Fig. 9']
 out=[];seen=set();low=text.lower()
 for p in pats:
  for m in re.finditer(re.escape(p.lower()),low):
   s=re.sub(r'\s+',' ',text[max(0,m.start()-350):min(len(text),m.end()+550)]).strip()
   if s not in seen:seen.add(s);out.append({'pattern':p,'context':s})
 return out[:100]
def inspect_pdf(b,meta):
 d=fitz.open(stream=b,filetype='pdf');pages=[];texts=[]
 for i,p in enumerate(d):
  t=p.get_text('text') or '';texts.append(t);pages.append({'page_index':i,'text_chars':len(t),'n_images':len(p.get_images(full=True)),'n_drawings':len(p.get_drawings())})
 text='\n'.join(texts)
 return {'pdf':meta,'page_count':len(d),'pages':pages,'native_text_chars':len(text),'contexts':contexts(text)}
def main():
 with REF.open(newline='',encoding='utf-8-sig') as f:refs=list(csv.DictReader(f))
 target=[r for r in refs if r.get('galaxy')=='NGC5585' and r.get('sparc_ref_id')=='Co91']
 if len(target)!=1 or target[0].get('stationary_role')!='blind':raise RuntimeError(f'Co91 frozen mapping changed: {target}')
 attempts=[];pdfs=[]
 for u in URLS:
  try:
   b,m=fetch(u);attempts.append(m)
   if b.startswith(b'%PDF') or 'application/pdf' in m['content_type'].lower():
    try:pdfs.append(inspect_pdf(b,m))
    except Exception as e:pdfs.append({'pdf':m,'parse_error':repr(e)})
  except Exception as e:attempts.append({'requested_url':u,'error':repr(e)})
 result={'status':'CO91_NGC5585_PUBLIC_ROUTE_AUDIT_COMPLETE','galaxy':'NGC5585','stationary_role':'blind','sparc_ref_id':'Co91','reference':{'authors':'Cote, Carignan & Sancisi','year':1991,'title':'A Dark-Halo-Dominated Galaxy: NGC 5585','journal':'AJ','volume':102,'pages':'904-913','doi':'10.1086/115922','bibcode':'1991AJ....102..904C'},'frozen_mapping':target[0],'fetch_attempts':attempts,'pdf_structural_audits':pdfs,'boundary':'Public source/provenance only for frozen blind target. No OCR, raster digitization, rotation-fit outcome inspection, persistence fitting, or source selection from blind results. L_A and C_A remain locked.'}
 OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 lines=[f"status={result['status']}"]
 for a in attempts:lines.append('ATTEMPT '+json.dumps(a,sort_keys=True))
 for p in pdfs:
  if 'parse_error' in p:lines.append('PDF_ERROR '+json.dumps(p));continue
  lines.append('PDF '+json.dumps({'url':p['pdf']['final_url'],'pages':p['page_count'],'native_text_chars':p['native_text_chars'],'structures':p['pages']},sort_keys=True))
  for c in p['contexts']:lines.append('CONTEXT '+json.dumps(c,ensure_ascii=False))
 TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'attempts':len(attempts),'pdfs':len(pdfs),'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
