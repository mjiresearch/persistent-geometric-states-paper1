#!/usr/bin/env python3
"""Targeted static audit of Ha14 fig-density.eps vector geometry.

The figure is parsed as text only; PostScript is never executed. The purpose is
to determine whether the two thick black H I surface-density traces can be
isolated from source-native vector commands and mapped to axes without raster
 digitization.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

URLS=['https://arxiv.org/e-print/1407.1744','https://export.arxiv.org/e-print/1407.1744']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_density_eps_vector_geometry_v1.json')
TARGET='fig-density.eps'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
    with urllib.request.urlopen(req,timeout=180) as h:return h.read(),h.geturl(),h.headers.get('Content-Type','')

def bounded(lines,i,r=6):
    return '\n'.join(lines[max(0,i-r):min(len(lines),i+r+1)])[:8000]

def main():
    attempts=[];raw=None
    for u in URLS:
        rec={'url':u}
        try:
            raw,final,ct=fetch(u);rec.update({'status':'fetched','final_url':final,'content_type':ct,'bytes':len(raw)});attempts.append(rec);break
        except Exception as exc:
            rec.update({'status':'error','error':f'{type(exc).__name__}: {exc}'});attempts.append(rec)
    if raw is None: raise SystemExit('source fetch failed')
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    m=tf.getmember(TARGET);b=tf.extractfile(m).read();text=b.decode('latin-1','replace');lines=text.splitlines()

    header=[ln for ln in lines[:120] if ln.startswith('%')]
    creator=[ln for ln in lines if any(k in ln.lower() for k in ['creator','title:','for:','creationdate','boundingbox','orientation'])][:80]

    # Procedure/alias definitions, especially plotting shorthands.
    defs=[]
    for i,ln in enumerate(lines):
        if re.search(r'^\s*/[A-Za-z][A-Za-z0-9_]*\s*\{',ln) or re.search(r'^\s*/[A-Za-z][A-Za-z0-9_]*\s+/',ln):
            if any(k in ln.lower() for k in ['moveto','lineto','rlineto','curveto','stroke','setrgbcolor','setgray','setlinewidth','setdash','show','translate','scale','clip','newpath','closepath']) or len(defs)<120:
                defs.append({'line':i+1,'text':ln[:2000]})

    # Explicit and one-letter candidate token counts.
    explicit_ops=['moveto','lineto','rlineto','curveto','rcurveto','stroke','newpath','closepath','clip','eoclip','setrgbcolor','setgray','setlinewidth','setdash','show','showpage','gsave','grestore']
    token_counts={op:len(re.findall(r'(?<![A-Za-z])'+re.escape(op)+r'(?![A-Za-z])',text)) for op in explicit_ops}
    one_letter={ch:len(re.findall(r'(?<![A-Za-z0-9_])'+re.escape(ch)+r'(?![A-Za-z0-9_])',text)) for ch in list('mMlLrRcCsSnNpPhHvV')}

    # Plot-state transitions and likely command-rich lines.
    state_hits=[]
    state_re=re.compile(r'(setrgbcolor|setgray|setlinewidth|setdash|clip|eoclip|newpath|moveto|lineto|rlineto|stroke|\b(?:m|M|l|L|r|R|c|C|s|S)\b)')
    for i,ln in enumerate(lines):
        if state_re.search(ln) and not ln.lstrip().startswith('%'):
            state_hits.append({'line':i+1,'text':ln[:2500]})

    # Literal strings and show-related labels for axis inference.
    labels=[]
    for i,ln in enumerate(lines):
        if '(' in ln and ')' in ln:
            ss=re.findall(r'\(([^()]*)\)',ln)
            useful=[s for s in ss if s.strip() and (re.search(r'\d',s) or any(k in s.lower() for k in ['radius','ugc','surface','density','pc','kpc','hi','h i']))]
            if useful: labels.append({'line':i+1,'strings':useful[:20],'text':ln[:2500]})

    # Numeric command lines: retain compact lines that plausibly encode paths.
    numeric_command_lines=[]
    numline=re.compile(r'^\s*[-+]?\d+(?:\.\d+)?(?:\s+[-+]?\d+(?:\.\d+)?){1,8}\s+[A-Za-z][A-Za-z0-9_]*\s*$')
    for i,ln in enumerate(lines):
        if numline.match(ln): numeric_command_lines.append({'line':i+1,'text':ln[:1000]})

    # Detect definitions mapping aliases to canonical operators.
    alias_map={}
    alias_pat=re.compile(r'^\s*/([A-Za-z][A-Za-z0-9_]*)\s*\{([^}]*)\}\s*(?:bind\s+)?def')
    for ln in lines:
        mm=alias_pat.search(ln)
        if mm:
            name,body=mm.group(1),mm.group(2).strip()
            if any(op in body for op in explicit_ops):alias_map[name]=body

    # Recount known aliases from discovered map.
    alias_counts={a:len(re.findall(r'(?<![A-Za-z0-9_])'+re.escape(a)+r'(?![A-Za-z0-9_])',text)) for a in alias_map}

    out={'status':'HA14_DENSITY_EPS_VECTOR_GEOMETRY_AUDIT_COMPLETE','source':'Hallenbeck et al. 2014 / fig-density.eps','arxiv':'1407.1744',
         'transport_attempts':attempts,'asset':{'name':TARGET,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},
         'header':header,'creator_lines':creator,'procedure_definitions':defs,'alias_map':alias_map,'explicit_token_counts':token_counts,
         'alias_token_counts':alias_counts,'one_letter_token_counts':one_letter,'state_hits':state_hits[:1500],
         'labels':labels[:500],'numeric_command_lines':numeric_command_lines[:3000],
         'static_interpretation_rule':'Zero image/colorimage/imagemask plus substantial path-command aliases supports native vector geometry, but promotion requires isolating the H I traces and a defensible axis coordinate mapping.',
         'boundary':'Static PostScript text parsing only. No PostScript execution, OCR, raster digitization, map reconstruction, normalization, persistence fitting, or blind-outcome inspection.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'asset':out['asset'],'creator':creator[:20],'alias_map':alias_map,'explicit':token_counts,
      'alias_counts':alias_counts,'one_letter':one_letter,'n_state_hits':len(state_hits),'n_labels':len(labels),'n_numeric_command_lines':len(numeric_command_lines),
      'state_sample':state_hits[:80],'label_sample':labels[:80],'numeric_sample':numeric_command_lines[:120]},indent=2))
if __name__=='__main__':main()
