#!/usr/bin/env python3
"""Audit Lelli et al. 2012b UGC4483 Figure 6 for exact native profile data.

Fetches the arXiv source package, identifies the Figure 6 graphics asset from
TeX/caption context, inventories its native structure, and records data-like
numeric/vector evidence. It never executes PostScript and never digitizes a
raster image.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

ARXIV='1207.2696'
URL=f'https://arxiv.org/e-print/{ARXIV}'
OUT=Path('validation/stationary/lelli2012b_ugc4483_fig6_source_audit_v1.json')
RAW=Path('validation/stationary/lelli2012b_ugc4483_fig6_source_context_v1.txt')
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'

def fetch():
    req=urllib.request.Request(URL,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=180) as h:
        return h.read(), h.geturl(), h.headers.get('Content-Type','')

def decode(b): return b.decode('latin-1','replace')

def main():
    raw,final_url,ctype=fetch()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    members=[m for m in tf.getmembers() if m.isfile()]
    names=[m.name for m in members]
    text_files=[]; graphics=[]; contexts=[]
    for m in members:
        lower=m.name.lower()
        b=tf.extractfile(m).read()
        if lower.endswith(('.tex','.txt','.bbl','.bib')):
            t=decode(b); text_files.append((m.name,t))
            lines=t.splitlines()
            for i,line in enumerate(lines):
                if ('surface density' in line.lower() or 'surface-density' in line.lower() or
                    'fig:dens' in line.lower() or 'fig6' in line.lower() or 'density profile' in line.lower()):
                    lo=max(0,i-12); hi=min(len(lines),i+13)
                    contexts.append({'file':m.name,'line':i+1,'context':'\n'.join(f'{j+1}: {lines[j]}' for j in range(lo,hi))})
        if lower.endswith(('.eps','.ps','.pdf','.png','.jpg','.jpeg','.gif','.tif','.tiff')):
            graphics.append({'name':m.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    # Extract graphics references in relevant TeX neighborhoods and caption blocks.
    refs=[]
    refpat=re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
    for fn,t in text_files:
        lines=t.splitlines()
        for i,line in enumerate(lines):
            neighborhood='\n'.join(lines[max(0,i-20):min(len(lines),i+21)])
            if ('H I surface density profiles' in neighborhood or 'HI surface density profiles' in neighborhood or
                'H\\,{\\sc i} surface density profiles' in neighborhood or 'surface density profiles' in neighborhood):
                for r in refpat.findall(neighborhood):
                    refs.append({'tex_file':fn,'near_line':i+1,'graphic_ref':r})
    # De-duplicate while preserving order.
    seen=set(); refs2=[]
    for r in refs:
        k=(r['tex_file'],r['graphic_ref'])
        if k not in seen: seen.add(k); refs2.append(r)
    refs=refs2

    assets=[]
    def resolve(ref):
        candidates=[ref,ref+'.eps',ref+'.ps',ref+'.pdf',ref+'.png']
        base=Path(ref).name
        for n in names:
            if n in candidates or Path(n).name in candidates or Path(n).stem==Path(base).stem:
                return n
        return None
    for r in refs:
        n=resolve(r['graphic_ref'])
        if not n: continue
        b=tf.extractfile(tf.getmember(n)).read(); low=n.lower(); rec={'ref':r,'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
        if low.endswith(('.eps','.ps')):
            t=decode(b)
            rec.update({
                'type':'postscript',
                'image_ops':len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',t)),
                'colorimage_ops':len(re.findall(r'(?<![A-Za-z])colorimage(?![A-Za-z])',t)),
                'moveto_tokens':len(re.findall(r'\b(?:moveto|M)\b',t)),
                'lineto_tokens':len(re.findall(r'\b(?:lineto|P)\b',t)),
                'rlineto_tokens':len(re.findall(r'\b(?:rlineto|R)\b',t)),
                'fill_tokens':len(re.findall(r'\b(?:fill|F)\b',t)),
                'stroke_tokens':len(re.findall(r'\b(?:stroke|D)\b',t)),
                'setrgbcolor_tokens':len(re.findall(r'\bsetrgbcolor\b',t)),
                'setdash_tokens':len(re.findall(r'\bsetdash\b',t)),
                'n_lines':len(t.splitlines()),
                'sample_numeric_lines':[]
            })
            for li,line in enumerate(t.splitlines(),1):
                nums=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
                if len(nums)>=8 and any(op in line for op in (' M',' R',' P',' D',' F','moveto','lineto','rlineto')):
                    rec['sample_numeric_lines'].append({'line':li,'text':line[:500]})
                    if len(rec['sample_numeric_lines'])>=60: break
            rec['native_vector_candidate']=(rec['image_ops']==0 and rec['colorimage_ops']==0 and (rec['rlineto_tokens']+rec['lineto_tokens']+rec['fill_tokens'])>20)
        elif low.endswith('.pdf'):
            # Structural byte-level PDF inventory only; no rendering/OCR.
            t=decode(b)
            rec.update({'type':'pdf','image_xobjects':len(re.findall(r'/Subtype\s*/Image',t)),
                        'path_operator_hits':len(re.findall(r'(?m)(?:^|\s)(?:m|l|c|v|y|h|S|s|f|f\*|B|b)(?:\s|$)',t)),
                        'native_vector_candidate':len(re.findall(r'/Subtype\s*/Image',t))==0})
        else:
            rec.update({'type':'raster','native_vector_candidate':False})
        assets.append(rec)

    out={
        'status':'LELLI2012B_UGC4483_FIG6_SOURCE_AUDIT_COMPLETE',
        'arxiv':ARXIV,'source_url':URL,'final_url':final_url,'content_type':ctype,
        'source_package_bytes':len(raw),'source_package_sha256':hashlib.sha256(raw).hexdigest(),
        'n_members':len(members),'members':names,
        'relevant_tex_contexts':contexts,
        'relevant_graphics_refs':refs,
        'resolved_assets':assets,
        'all_graphics':graphics,
        'next_gate':('parse_source_native_profile_geometry' if any(a.get('native_vector_candidate') for a in assets)
                     else 'no_exact_vector_asset_found_check_numeric_arrays_or_disposition'),
        'boundary':'Source/acquisition audit only; no PostScript execution, raster digitization, map-to-profile reconstruction, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2)+'\n')
    RAW.write_text('\n\n'.join(f"===== {c['file']}:{c['line']} =====\n{c['context']}" for c in contexts),encoding='utf-8')
    print(json.dumps({'status':out['status'],'refs':refs,'assets':[{k:a.get(k) for k in ('name','type','bytes','image_ops','colorimage_ops','moveto_tokens','rlineto_tokens','fill_tokens','stroke_tokens','image_xobjects','path_operator_hits','native_vector_candidate')} for a in assets],'next_gate':out['next_gate']},indent=2))

if __name__=='__main__': main()
