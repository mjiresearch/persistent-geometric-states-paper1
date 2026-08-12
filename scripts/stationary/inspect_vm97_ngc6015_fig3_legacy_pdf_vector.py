#!/usr/bin/env python3
"""Inspect VM97 Figure 3 in the legacy A&A PDF with PyMuPDF.

The exact Figure-3 EPS has already been shown to be pure PGPLOT vector. This
companion audit uses the legacy PDF only to recover native text/tick coordinates
and page geometry, while leaving the PGPLOT EPS as the authoritative curve source.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from urllib.request import Request,urlopen
import pymupdf

URLS=['https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.pdf','https://cdsarc.u-strasbg.fr/ftp/vizier/aa/papers/7321003/2300754.pdf']
OUT=Path('validation/stationary/vm97_ngc6015_fig3_legacy_pdf_vector_inventory_v1.json')
TXT=Path('validation/stationary/vm97_ngc6015_fig3_legacy_pdf_vector_context_v1.txt')

def h(b):return hashlib.sha256(b).hexdigest()
def fetch():
 errs=[]
 for u in URLS:
  try:
   with urlopen(Request(u,headers={'User-Agent':'PaperI-VM97-pdf/1.0'}),timeout=90) as r:return r.read(),r.geturl()
  except Exception as e:errs.append([u,repr(e)])
 raise RuntimeError(errs)
def compact(d):
 r=d['rect']
 return {'rect':[round(r.x0,4),round(r.y0,4),round(r.x1,4),round(r.y1,4)],'type':d.get('type'),'color':None if d.get('color') is None else [round(float(x),5) for x in d['color']],'fill':None if d.get('fill') is None else [round(float(x),5) for x in d['fill']],'width':round(float(d.get('width') or 0),5),'nitems':len(d.get('items',[]))}
def main():
 b,url=fetch();doc=pymupdf.open(stream=b,filetype='pdf')
 pages=[];fig_pages=[]
 for pi,p in enumerate(doc):
  text=p.get_text('text')
  words=p.get_text('words')
  imgs=p.get_images(full=True);draw=p.get_drawings()
  rec={'page_index':pi,'page_number_in_article':pi+1,'rect':[round(x,3) for x in p.rect],'n_images':len(imgs),'n_drawings':len(draw),'n_words':len(words),'text':text,'words':[{'rect':[round(w[0],3),round(w[1],3),round(w[2],3),round(w[3],3)],'center':[round((w[0]+w[2])/2,3),round((w[1]+w[3])/2,3)],'text':w[4]} for w in words],'drawing_summary':[compact(x) for x in draw]}
  if 'Fig. 3' in text or 'Fig.3' in text or ('surface density' in text.lower() and '6015' in text):fig_pages.append(pi)
  pages.append(rec)
 result={'status':'VM97_NGC6015_FIG3_LEGACY_PDF_VECTOR_INVENTORY_COMPLETE','source_url':url,'pdf_bytes':len(b),'pdf_sha256':h(b),'page_count':len(doc),'candidate_fig3_pages':fig_pages,'pages':pages,'next_action':'Identify Figure-3 panel d bounds from native labels/ticks; map the corresponding PGPLOT EPS vector marker/polyline coordinates to radius and Sigma_HI.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 lines=[f'URL={url}',f'pages={len(doc)}',f'candidate_fig3_pages={fig_pages}']
 for pi in sorted(set(fig_pages+[2,3,4])):
  if 0<=pi<len(pages):
   p=pages[pi];lines += [f'\n=== PAGE {pi} images={p["n_images"]} drawings={p["n_drawings"]} words={p["n_words"]} ===','TEXT',p['text'],'WORDS']+[f"{w['rect']} {w['text']}" for w in p['words']]+['DRAWINGS']+[json.dumps(x) for x in p['drawing_summary']]
 TXT.write_text('\n'.join(lines)+'\n')
 print(json.dumps({'status':result['status'],'candidate_fig3_pages':fig_pages,'page_summaries':[{'page':p['page_index'],'images':p['n_images'],'drawings':p['n_drawings'],'words':p['n_words']} for p in pages],'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
