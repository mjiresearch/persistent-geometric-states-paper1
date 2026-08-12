#!/usr/bin/env python3
"""Reduce HIX2018 NGC289 Figure A3 panel (b) to compact native geometry.

Panel (b) is the upper-right radial H I profile. This reducer keeps only nearby
native text and black vector objects, groups likely markers by dimensions, and
extracts the TeX appendix/method context needed to determine whether the plotted
series is measured or a TiRiFiC model parameter profile.
"""
from __future__ import annotations
import collections, hashlib, io, json, math, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen
import fitz

URL='https://arxiv.org/e-print/1802.04043'
PDF_MEMBER='Images/app-fig3.pdf'
TEX_MEMBER='hix2_main.tex'
OUT=Path('validation/stationary/hix2018_ngc289_hi_panel_geometry_v1.json')
TXT=Path('validation/stationary/hix2018_ngc289_hi_panel_geometry_v1.txt')
UA='PaperI-HIX-NGC289-hi-panel/1.0'
# Native plot frame inferred from shared appendix panel layout and tick positions.
ROI=(228.0, 24.0, 362.0, 151.5)

def sha(b):return hashlib.sha256(b).hexdigest()
def intersects(r,roi):
    x0,y0,x1,y1=roi
    return not (r.x1<x0 or r.x0>x1 or r.y1<y0 or r.y0>y1)
def ckey(v):
    if v is None:return 'None'
    return ','.join(f'{q:.4f}' for q in v)
def compact_item(z):
    out=[]
    for v in z:
        if isinstance(v,str): out.append(v)
        elif hasattr(v,'ul') and hasattr(v,'ur') and hasattr(v,'ll') and hasattr(v,'lr'):
            out.append({'quad':[[round(v.ul.x,4),round(v.ul.y,4)],[round(v.ur.x,4),round(v.ur.y,4)],[round(v.lr.x,4),round(v.lr.y,4)],[round(v.ll.x,4),round(v.ll.y,4)]]})
        elif hasattr(v,'x0') and hasattr(v,'y0') and hasattr(v,'x1') and hasattr(v,'y1'):
            out.append([round(v.x0,4),round(v.y0,4),round(v.x1,4),round(v.y1,4)])
        elif hasattr(v,'x') and hasattr(v,'y'):
            out.append([round(v.x,4),round(v.y,4)])
        else: out.append(str(v))
    return out

def contexts(tex,needle,window=1000):
    out=[]
    for m in re.finditer(needle,tex,re.I|re.S):
        lo=max(0,m.start()-window);hi=min(len(tex),m.end()+window)
        out.append(re.sub(r'\s+',' ',tex[lo:hi]).strip())
    return out

def main():
    with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=60) as r:
        payload=r.read();final=r.geturl()
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        pdf=tf.extractfile(tf.getmember(PDF_MEMBER)).read()
        tex=tf.extractfile(tf.getmember(TEX_MEMBER)).read().decode('latin-1',errors='replace')
    d=fitz.open(stream=pdf,filetype='pdf');p=d[0]
    words=[]
    for w in p.get_text('words'):
        x0,y0,x1,y1,t,*_=w
        if x1>=195 and x0<=390 and y1>=-2 and y0<=157:
            words.append({'x0':round(x0,4),'y0':round(y0,4),'x1':round(x1,4),'y1':round(y1,4),
                          'cx':round((x0+x1)/2,4),'cy':round((y0+y1)/2,4),'text':t})
    keep=[]
    for i,x in enumerate(p.get_drawings()):
        r=x.get('rect')
        if not r or not intersects(r,ROI):continue
        color=ckey(x.get('color'));fill=ckey(x.get('fill'))
        # Keep black/near-black only for axes/profile; colored contours belong other layers.
        def nearblack(v):return v is not None and max(v)<=0.06
        if not (nearblack(x.get('color')) or nearblack(x.get('fill'))):continue
        ent={'i':i,'type':x.get('type'),'color':color,'fill':fill,'width':x.get('width'),
             'rect':[round(r.x0,4),round(r.y0,4),round(r.x1,4),round(r.y1,4)],
             'cx':round((r.x0+r.x1)/2,4),'cy':round((r.y0+r.y1)/2,4),
             'rw':round(r.width,4),'rh':round(r.height,4),'n_items':len(x.get('items',[]))}
        if len(x.get('items',[]))<=20:
            ent['items']=[compact_item(z) for z in x.get('items',[])]
        keep.append(ent)
    # Dimension/type groups reveal repeated marker glyphs without assuming their identity.
    groups=collections.Counter((e['type'],round(e['rw'],2),round(e['rh'],2),e['color'],e['fill'],e['n_items']) for e in keep)
    group_rows=[{'type':k[0],'rw':k[1],'rh':k[2],'color':k[3],'fill':k[4],'n_items':k[5],'count':v} for k,v in groups.most_common()]
    repeated=[g for g in group_rows if g['count']>=3 and g['rw']<=10 and g['rh']<=10]
    # Explicit likely-marker candidates: compact, repeated black filled/stroked glyphs fully within plotting frame.
    reps={(g['type'],g['rw'],g['rh'],g['color'],g['fill'],g['n_items']) for g in repeated}
    markers=[]
    for e in keep:
        key=(e['type'],round(e['rw'],2),round(e['rh'],2),e['color'],e['fill'],e['n_items'])
        if key in reps and 232.5<=e['cx']<=358 and 28<=e['cy']<=148:
            markers.append(e)
    # TeX context: radial profile methods, appendix panel description, NGC289 figure mapping, helium/conversion terms.
    tex_context={
      'radial_profiles':contexts(tex,r'\\subsection\{Radial profiles\}',1800)[:3],
      'appendix_panel_description':contexts(tex,r'Panel\s*\(b\)',1800)[:5],
      'ngc289_figure':contexts(tex,r'\\caption\{NGC289\}',1000)[:3],
      'helium_terms':contexts(tex,r'helium|1\.36|1\.4|1\.33',600)[:20],
      'column_density_terms':contexts(tex,r'column density',500)[:20]
    }
    result={'status':'HIX2018_NGC289_HI_PANEL_GEOMETRY_REDUCED',
            'source_package':{'url':final,'bytes':len(payload),'sha256':sha(payload)},
            'pdf_member':PDF_MEMBER,'pdf_sha256':sha(pdf),'roi':ROI,
            'words':words,'n_black_objects':len(keep),'black_objects':keep,
            'geometry_groups':group_rows,'repeated_small_groups':repeated,
            'likely_marker_candidates':markers,'n_likely_marker_candidates':len(markers),
            'tex_context':tex_context,
            'boundary':'Native PDF/TeX structure only; no OCR, raster digitization, source execution, persistence fitting, or blind-outcome inspection.'}
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=[f"status={result['status']}",f"pdf_sha256={sha(pdf)}",f"roi={ROI}",f"words={len(words)} black_objects={len(keep)} marker_candidates={len(markers)}",
           'GROUPS '+json.dumps(group_rows[:40]),'REPEATED '+json.dumps(repeated)]
    for w in words:lines.append('WORD '+json.dumps(w,ensure_ascii=False))
    for e in markers:lines.append('MARKER '+json.dumps({k:e[k] for k in ['i','type','cx','cy','rw','rh','color','fill','n_items']}))
    for k,v in tex_context.items():
        for c in v: lines.append('TEX_'+k.upper()+' '+json.dumps(c,ensure_ascii=False))
    TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'black_objects':len(keep),'marker_candidates':len(markers),'repeated_small_groups':repeated,'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
