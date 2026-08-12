#!/usr/bin/env python3
"""Audit Gentile et al. 2004 Figure 2 for native radial H I profiles.

Ge04 is already established as the original ATCA observing source for
ESO116-G12 and ESO79-G14. The paper explicitly states that Figure 2 contains
the radial neutral-hydrogen surface-density distributions, with filled circles
representing the average profile. This script identifies that Figure-2 source
asset and inventories its exact source-native structure.

No PostScript execution/rendering, OCR, raster digitization, map-to-profile
reconstruction, normalization, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

ARXIV='astro-ph/0403154'
URL='https://arxiv.org/e-print/astro-ph/0403154'
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ge04_fig2_hi_profile_source_audit_v1.json')
CTX=Path('validation/stationary/ge04_fig2_hi_profile_source_context_v1.txt')
TARGETS=('ESO 116-G12','ESO 79-G14','ESO116-G12','ESO79-G14')

def fetch():
    req=urllib.request.Request(URL,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    return raw,tf

def read_member(tf,name):return tf.extractfile(tf.getmember(name)).read()

def classify(name,b):
    low=name.lower(); rec={'name':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    if low.endswith(('.ps','.eps')):
        t=b.decode('latin-1','replace')
        rec.update({'type':'postscript',
                    'image_ops':len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',t)),
                    'colorimage_ops':len(re.findall(r'(?<![A-Za-z])colorimage(?![A-Za-z])',t)),
                    'moveto_ops':len(re.findall(r'(?<![A-Za-z])moveto(?![A-Za-z])',t)),
                    'lineto_ops':len(re.findall(r'(?<![A-Za-z])lineto(?![A-Za-z])',t)),
                    'rlineto_ops':len(re.findall(r'(?<![A-Za-z])rlineto(?![A-Za-z])',t)),
                    'fill_ops':len(re.findall(r'(?<![A-Za-z])fill(?![A-Za-z])',t)),
                    'stroke_ops':len(re.findall(r'(?<![A-Za-z])stroke(?![A-Za-z])',t)),
                    'circle_tokens':len(re.findall(r'(?i)circle|circ|dot|point',t)),
                    'triangle_tokens':len(re.findall(r'(?i)triang|triangle|TriU|TriD',t)),
                    'creator_lines':[z for z in t.splitlines()[:100] if z.startswith(('%%Creator','%%Title','%%BoundingBox'))],
                    'n_lines':len(t.splitlines())})
        # Procedure definitions and common plot marker invocations.
        defs=[]
        for li,line in enumerate(t.splitlines(),1):
            if re.search(r'/[A-Za-z][A-Za-z0-9_.-]*\s*\{',line):
                defs.append({'line':li,'text':line[:700]})
        rec['procedure_definition_samples']=defs[:150]
        marker_lines=[]
        for li,line in enumerate(t.splitlines(),1):
            if re.search(r'(?i)CircleF|Circle|TriU|TriD|Pt\b|Pnt\b|symbol|marker',line):
                marker_lines.append({'line':li,'text':line[:1000]})
        rec['marker_lines']=marker_lines[:300]
        rec['native_vector_candidate']=(rec['image_ops']==0 and rec['colorimage_ops']==0 and (rec['moveto_ops']+rec['lineto_ops']+rec['rlineto_ops']+rec['fill_ops'])>10)
    elif low.endswith('.pdf'):
        t=b.decode('latin-1','replace'); imgs=len(re.findall(r'/Subtype\s*/Image',t))
        rec.update({'type':'pdf','image_xobjects':imgs,'native_vector_candidate':imgs==0})
    else:
        rec.update({'type':'raster','native_vector_candidate':False})
    return rec

def main():
    raw,tf=fetch(); members=[m for m in tf.getmembers() if m.isfile()]; names=[m.name for m in members]
    texs=[]
    for m in members:
        if m.name.lower().endswith('.tex'):
            texs.append((m.name,read_member(tf,m.name).decode('latin-1','replace')))
    contexts=[]; fig2=[]
    for fn,t in texs:
        lines=t.splitlines()
        for i,line in enumerate(lines):
            hood='\n'.join(lines[max(0,i-20):min(len(lines),i+21)])
            if ('radial distribution of the neutral hydrogen' in hood.lower() or
                ('surface density' in hood.lower() and 'filled circles' in hood.lower())):
                contexts.append({'file':fn,'line':i+1,'context':'\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-20),min(len(lines),i+21)))})
                for r in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',hood): fig2.append({'tex_file':fn,'near_line':i+1,'graphic_ref':r})
                for r in re.findall(r'\\epsfig\{[^}]*file\s*=\s*([^,} ]+)',hood): fig2.append({'tex_file':fn,'near_line':i+1,'graphic_ref':r})
    # If context matching catches adjacent figures, identify the block whose caption contains radial density.
    for fn,t in texs:
        for b in re.findall(r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}',t,re.S):
            if 'radial distribution' in b.lower() and ('hydrogen' in b.lower() or 'h i' in b.lower() or 'h\\' in b.lower()):
                for r in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',b): fig2.append({'tex_file':fn,'near_line':None,'graphic_ref':r,'source':'figure_block'})
                for r in re.findall(r'\\epsfig\{[^}]*file\s*=\s*([^,} ]+)',b): fig2.append({'tex_file':fn,'near_line':None,'graphic_ref':r,'source':'figure_block'})
    # dedupe refs
    seen=set(); refs=[]
    for r in fig2:
        k=r['graphic_ref']
        if k not in seen:seen.add(k);refs.append(r)
    def resolve(r):
        cand=[r,r+'.eps',r+'.ps',r+'.pdf']
        for n in names:
            if n in cand or Path(n).stem==Path(r).stem:return n
        return None
    assets=[]
    for r in refs:
        n=resolve(r['graphic_ref'])
        if n:assets.append({'ref':r,**classify(n,read_member(tf,n))})
    # inventory potential machine-readable data members
    data_members=[]
    for m in members:
        low=m.name.lower()
        if low.endswith(('.dat','.data','.txt','.tab','.tbl','.csv','.lis','.out')):
            b=read_member(tf,m.name); txt=b.decode('latin-1','replace')
            score=sum(1 for line in txt.splitlines() if len(re.findall(r'[-+]?\d+(?:\.\d+)?',line))>=3)
            data_members.append({'name':m.name,'bytes':len(b),'numeric_lines_3plus':score,'sha256':hashlib.sha256(b).hexdigest()})
    out={'status':'GE04_FIG2_HI_PROFILE_SOURCE_AUDIT_COMPLETE','arxiv':ARXIV,
         'source_package_sha256':hashlib.sha256(raw).hexdigest(),'n_members':len(members),'members':names,
         'paper_fact':'Ge04 Section 5 says radial neutral-hydrogen surface density is computed and shown in Fig. 2; filled circles are the average.',
         'figure2_contexts':contexts,'figure2_graphics_refs':refs,'figure2_assets':assets,
         'potential_numeric_data_members':data_members,
         'next_gate':('parse_source_native_average_profile_markers_and_axes' if any(a.get('native_vector_candidate') for a in assets)
                      else 'check_numeric_member_then_disposition_if_no_exact_route'),
         'boundary':'Acquisition/provenance only; PostScript not executed/rendered; no OCR, raster digitization, map reconstruction, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
    CTX.write_text('\n\n'.join(f"===== {c['file']}:{c['line']} =====\n{c['context']}" for c in contexts)+'\n')
    print(json.dumps({'status':out['status'],'refs':refs,
                      'assets':[{k:a.get(k) for k in ('name','type','bytes','image_ops','colorimage_ops','moveto_ops','lineto_ops','rlineto_ops','fill_ops','circle_tokens','triangle_tokens','native_vector_candidate','creator_lines')} for a in assets],
                      'data_members':data_members,'next_gate':out['next_gate']},indent=2))
if __name__=='__main__':main()
