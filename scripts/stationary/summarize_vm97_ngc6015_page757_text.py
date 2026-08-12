#!/usr/bin/env python3
"""Compact native-text inventory for VM97 journal page 757 / Figure 3.

Fetches the legacy A&A PDF and records only page index 3 native words, grouped by
position, with numeric/axis-relevant subsets. This is deliberately compact and
replaces the need to consult the earlier oversized whole-PDF diagnostic.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.request import Request,urlopen
import pymupdf

URL='https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.pdf'
PAGE=3
OUT=Path('validation/stationary/vm97_ngc6015_page757_native_text_v1.json')
TXT=Path('validation/stationary/vm97_ngc6015_page757_native_text_v1.txt')

def main():
 with urlopen(Request(URL,headers={'User-Agent':'PaperI-VM97-page757/1.0'}),timeout=90) as r:b=r.read()
 doc=pymupdf.open(stream=b,filetype='pdf');p=doc[PAGE]
 words=[]
 for w in p.get_text('words'):
  rec={'x0':round(w[0],3),'y0':round(w[1],3),'x1':round(w[2],3),'y1':round(w[3],3),'cx':round((w[0]+w[2])/2,3),'cy':round((w[1]+w[3])/2,3),'text':w[4],'block':w[5],'line':w[6],'word':w[7]}
  words.append(rec)
 numeric=[w for w in words if re.fullmatch(r'[+\-−]?(?:\d+(?:\.\d*)?|\.\d+)',w['text'].replace('−','-'))]
 axis=[w for w in words if re.search(r'HI|H.?I|kpc|arcsec|radius|density|surface|B-I|B-V|B-R|ellipt|position|angle|M|pc|D\s*=|13\.9',w['text'],re.I)]
 # Likely figure-region words: left half and upper ~55% of page; retain separately but keep all words too.
 fig=[w for w in words if w['cy']<470]
 result={'status':'VM97_NGC6015_PAGE757_NATIVE_TEXT_COMPLETE','source_url':URL,'page_index':PAGE,'page_rect':[round(x,3) for x in p.rect],'n_words':len(words),'n_numeric_words':len(numeric),'n_axis_relevant_words':len(axis),'words':words,'numeric_words':numeric,'axis_relevant_words':axis,'likely_figure_region_words':fig,'next_action':'Match native numeric labels to the bottom Figure-3d panel frame/tick positions and solve exact radius/Sigma_HI transforms for the 31 M3 markers.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 lines=['AXIS_RELEVANT']+[f"{w['x0']:7.3f} {w['y0']:7.3f} {w['x1']:7.3f} {w['y1']:7.3f} {w['text']}" for w in axis]+['','NUMERIC']+[f"{w['x0']:7.3f} {w['y0']:7.3f} {w['x1']:7.3f} {w['y1']:7.3f} {w['text']}" for w in numeric]+['','ALL_WORDS']+[f"{w['x0']:7.3f} {w['y0']:7.3f} {w['x1']:7.3f} {w['y1']:7.3f} {w['text']}" for w in words]
 TXT.write_text('\n'.join(lines)+'\n')
 print(json.dumps({'status':result['status'],'page_rect':result['page_rect'],'n_words':len(words),'axis_relevant':axis,'numeric_words':numeric,'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
