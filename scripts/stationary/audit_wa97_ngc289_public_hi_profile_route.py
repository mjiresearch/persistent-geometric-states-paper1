#!/usr/bin/env python3
"""Audit public exact radial H I profile routes for Wa97 / NGC0289.

Acquisition/provenance only. The script makes bounded public fetch attempts for
the original Walsh, Staveley-Smith & Oosterloo (1997) AJ article, then inspects
any recovered PDF structurally with PyMuPDF. It never OCRs, raster-digitizes, or
executes embedded content.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import fitz

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OUT=Path('validation/stationary/wa97_ngc289_public_hi_profile_route_v1.json')
TXT=Path('validation/stationary/wa97_ngc289_public_hi_profile_route_v1.txt')

CANDIDATES=[
 'https://articles.adsabs.harvard.edu/pdf/1997AJ....113.1591W',
 'https://articles.adsabs.harvard.edu/full/1997AJ....113.1591W',
 'https://iopscience.iop.org/article/10.1086/118377/pdf',
 'https://journals.uchicago.edu/doi/pdf/10.1086/118377',
]
UA='PaperI-Wa97-public-profile-audit/1.0'

def sha(b): return hashlib.sha256(b).hexdigest()

def fetch(url,timeout=45):
    req=Request(url,headers={'User-Agent':UA,'Accept':'application/pdf,text/html,*/*'})
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return {'requested_url':url,'final_url':r.geturl(),'status':getattr(r,'status',200),
                'content_type':r.headers.get('Content-Type',''),'bytes':len(b),'sha256':sha(b)},b

def text_context(text,patterns,window=280):
    low=text.lower(); out=[]; seen=set()
    for p in patterns:
        for m in re.finditer(re.escape(p.lower()),low):
            lo=max(0,m.start()-window); hi=min(len(text),m.end()+window)
            s=re.sub(r'\s+',' ',text[lo:hi]).strip()
            if s not in seen: seen.add(s); out.append({'pattern':p,'context':s})
    return out[:80]

def inspect_pdf(meta,b):
    d=fitz.open(stream=b,filetype='pdf')
    pages=[]; alltext=[]
    for i,p in enumerate(d):
        t=p.get_text('text') or ''
        alltext.append(t)
        pages.append({'page_index':i,'text_chars':len(t),'n_images':len(p.get_images(full=True)),
                      'n_drawings':len(p.get_drawings())})
    text='\n'.join(alltext)
    pats=['surface density','surface-density','column density','radial distribution','radial profile',
          'H I surface','HI surface','gas surface','Figure 2','Figure 3','Figure 4','Figure 5',
          'Fig. 2','Fig. 3','Fig. 4','Fig. 5','helium','1.33','1.4']
    contexts=text_context(text,pats)
    # Page-level candidates from H I + density/profile language, no semantic guessing from images.
    candidates=[]
    for i,t in enumerate(alltext):
        l=t.lower()
        score=sum(x in l for x in ['surface density','surface-density','column density','radial profile','radial distribution'])
        if score or ('h i' in l and ('density' in l or 'radial' in l)):
            candidates.append({'page_index':i,'score':score,'text_excerpt':re.sub(r'\s+',' ',t)[:1800]})
    return {'pdf':meta,'page_count':len(d),'pages':pages,'native_text_chars':len(text),
            'contexts':contexts,'candidate_pages':candidates[:20]}

def main():
    with REF.open(newline='',encoding='utf-8-sig') as f: refs=list(csv.DictReader(f))
    rows=[r for r in refs if r.get('galaxy')=='NGC0289' and r.get('sparc_ref_id')=='Wa97']
    if len(rows)!=1 or rows[0].get('stationary_role')!='calibration':
        raise RuntimeError(f'Wa97 frozen mapping changed: {rows}')

    attempts=[]; pdfs=[]; html_links=[]
    for u in CANDIDATES:
        try:
            meta,b=fetch(u); attempts.append(meta)
            ct=meta['content_type'].lower(); head=b[:16]
            if b.startswith(b'%PDF') or 'application/pdf' in ct:
                try: pdfs.append(inspect_pdf(meta,b))
                except Exception as e: pdfs.append({'pdf':meta,'parse_error':repr(e)})
            elif 'html' in ct or b'html' in head.lower():
                txt=b.decode('utf-8',errors='replace')
                for href in re.findall(r'href=[\"\']([^\"\']+)',txt,re.I):
                    hu=urljoin(meta['final_url'],href)
                    if any(k in hu.lower() for k in ['pdf','1997aj','1591w']): html_links.append(hu)
        except Exception as e:
            attempts.append({'requested_url':u,'error':repr(e)})

    # Follow at most eight discovered article/PDF links, bounded and deduplicated.
    seen=set(CANDIDATES)
    for u in html_links[:20]:
        if u in seen: continue
        seen.add(u)
        if len(seen)>len(CANDIDATES)+8: break
        try:
            meta,b=fetch(u); attempts.append(meta)
            if b.startswith(b'%PDF') or 'application/pdf' in meta['content_type'].lower():
                try: pdfs.append(inspect_pdf(meta,b))
                except Exception as e: pdfs.append({'pdf':meta,'parse_error':repr(e)})
        except Exception as e:
            attempts.append({'requested_url':u,'error':repr(e)})

    result={
      'status':'WA97_NGC0289_PUBLIC_ROUTE_AUDIT_COMPLETE',
      'galaxy':'NGC0289','stationary_role':'calibration','sparc_ref_id':'Wa97',
      'reference':{'authors':'Walsh, Staveley-Smith & Oosterloo','year':1997,
                   'title':'The Giant, Gas-Rich, Low-Surface-Brightness Galaxy NGC 289',
                   'journal':'Astronomical Journal','volume':113,'pages':'1591-1606',
                   'doi':'10.1086/118377','bibcode':'1997AJ....113.1591W'},
      'frozen_mapping':rows[0],
      'fetch_attempts':attempts,
      'discovered_links':sorted(set(html_links))[:40],
      'pdf_structural_audits':pdfs,
      'boundary':'Public acquisition/provenance only. No OCR, raster digitization, profile fitting, persistence fitting, blind-outcome inspection, or PostScript execution. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=[f"status={result['status']}",f"target=NGC0289 role=calibration ref=Wa97",f"attempts={len(attempts)} pdfs={len(pdfs)}"]
    for a in attempts: lines.append('ATTEMPT '+json.dumps(a,sort_keys=True))
    for p in pdfs:
        if 'parse_error' in p: lines.append('PDF_ERROR '+json.dumps(p,sort_keys=True)); continue
        lines.append('PDF '+json.dumps({'url':p['pdf']['final_url'],'pages':p['page_count'],'native_text_chars':p['native_text_chars'],'page_structures':p['pages']},sort_keys=True))
        for c in p['contexts'][:25]: lines.append('CONTEXT '+json.dumps(c,ensure_ascii=False))
    TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'attempts':len(attempts),'pdfs':len(pdfs),'outputs':[str(OUT),str(TXT)]},indent=2))

if __name__=='__main__': main()
