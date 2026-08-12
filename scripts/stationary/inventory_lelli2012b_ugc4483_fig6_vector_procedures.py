#!/usr/bin/env python3
"""Inventory custom PostScript procedures and coordinate invocations in UGC4483 Fig6.eps.

This is a static source-code audit. It does not execute PostScript and does not
render/digitize the figure. The goal is to identify native marker procedures
(dots, up/down triangles) and their source-coordinate sequences.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ARXIV='1207.2696'; URL=f'https://arxiv.org/e-print/{ARXIV}'
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/lelli2012b_ugc4483_fig6_vector_procedure_inventory_v1.json')
CTX=Path('validation/stationary/lelli2012b_ugc4483_fig6_vector_procedure_context_v1.txt')

NUM=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?'
NAME=r'[A-Za-z_][A-Za-z0-9_.-]*'

def fetch_eps():
    req=urllib.request.Request(URL,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    b=tf.extractfile(tf.getmember('Fig6.eps')).read()
    return raw,b

def strip_comment(line):
    # PostScript comments begin with %, except escaped strings are irrelevant to
    # our numeric/procedure invocation inventory.
    return line.split('%',1)[0] if '%' in line else line

def collect_defs(text):
    """Collect /name { ... } def-like definitions with brace balancing."""
    lines=text.splitlines(); defs=[]; i=0
    while i < len(lines):
        line=strip_comment(lines[i])
        m=re.search(r'/('+NAME+r')\s*\{',line)
        if not m:
            i+=1; continue
        name=m.group(1); start=i+1
        chunk=line[m.start():]; depth=chunk.count('{')-chunk.count('}')
        j=i
        while depth>0 and j+1<len(lines):
            j+=1; z=strip_comment(lines[j]); chunk+='\n'+z
            depth += z.count('{')-z.count('}')
        # Include trailing bind/def on same/next line if present.
        if j+1<len(lines) and not re.search(r'\b(?:def|bdef)\b',chunk):
            nxt=strip_comment(lines[j+1])
            if re.search(r'\b(?:def|bdef)\b',nxt):
                j+=1; chunk+='\n'+nxt
        defs.append({'name':name,'start_line':start,'end_line':j+1,'body':chunk[:4000],
                     'has_fill':bool(re.search(r'\bfill\b',chunk)),
                     'has_stroke':bool(re.search(r'\bstroke\b',chunk)),
                     'has_closepath':bool(re.search(r'\bclosepath\b',chunk)),
                     'local_ML_commands':len(re.findall(r'(?<!\S)(?:'+NUM+r')\s+(?:'+NUM+r')\s+[MLR](?!\S)',chunk))})
        i=j+1
    return defs

def in_def_line(li,defs):
    return any(d['start_line']<=li<=d['end_line'] for d in defs)

def main():
    raw,b=fetch_eps(); text=b.decode('latin-1','replace'); lines=text.splitlines(); defs=collect_defs(text)
    defnames={d['name'] for d in defs}

    # Also inventory one-line aliases such as /M {moveto} bind def.
    aliases=[]
    for li,line0 in enumerate(lines,1):
        line=strip_comment(line0)
        m=re.search(r'/('+NAME+r')\s*\{([^{}]{0,300})\}\s*(?:bind\s+)?def',line)
        if m:
            aliases.append({'line':li,'name':m.group(1),'body':m.group(2).strip()})

    inv=defaultdict(list)
    all_names=Counter()
    # Capture literal "x y PROC" and "x y PROC extra" calls outside definitions.
    pat=re.compile(r'('+NUM+r')\s+('+NUM+r')\s+('+NAME+r')\b')
    for li,line0 in enumerate(lines,1):
        if in_def_line(li,defs): continue
        line=strip_comment(line0)
        for m in pat.finditer(line):
            x=float(m.group(1)); y=float(m.group(2)); name=m.group(3)
            all_names[name]+=1
            inv[name].append({'line':li,'x':x,'y':y,'text':line0.strip()[:800]})

    procs=[]
    for name,pts in inv.items():
        if name not in defnames and name not in {a['name'] for a in aliases}: continue
        xs=[p['x'] for p in pts]; ys=[p['y'] for p in pts]
        procs.append({'name':name,'n_invocations':len(pts),'n_unique_xy':len({(p['x'],p['y']) for p in pts}),
                      'bbox':[min(xs),min(ys),max(xs),max(ys)],
                      'x_span':max(xs)-min(xs),'y_span':max(ys)-min(ys),
                      'first_line':min(p['line'] for p in pts),'last_line':max(p['line'] for p in pts),
                      'first_40_invocations':pts[:40]})
    procs.sort(key=lambda z:(z['n_invocations'],z['x_span']+z['y_span']),reverse=True)

    # Strings containing axis-like numerals/units, preserving only small contexts.
    strings=[]
    strpat=re.compile(r'\((?:\\.|[^()])*\)')
    for li,line in enumerate(lines,1):
        ss=strpat.findall(line)
        if ss and any(re.search(r'\d|kpc|pc|Msol|M_',s,re.I) for s in ss):
            strings.append({'line':li,'strings':ss[:20],'text':line.strip()[:1000]})

    # Long native segments are useful for identifying plot borders/ticks.
    long_segments=[]
    for li,line in enumerate(lines,1):
        # absolute x y M followed by x y L, or relative R segment.
        for m in re.finditer(r'('+NUM+r')\s+('+NUM+r')\s+M\s+('+NUM+r')\s+('+NUM+r')\s+L',line):
            x0,y0,x1,y1=map(float,m.groups());
            if abs(x1-x0)>100 or abs(y1-y0)>100:
                long_segments.append({'line':li,'kind':'M-L','a':[x0,y0],'b':[x1,y1],'text':line.strip()[:700]})
        for m in re.finditer(r'('+NUM+r')\s+('+NUM+r')\s+R\b',line):
            dx,dy=map(float,m.groups())
            if abs(dx)>100 or abs(dy)>100:
                long_segments.append({'line':li,'kind':'R','delta':[dx,dy],'text':line.strip()[:700]})

    # Definition bodies matched to invocation summaries.
    bydef={d['name']:d for d in defs}; byalias={a['name']:a for a in aliases}
    candidates=[]
    for p in procs:
        d=bydef.get(p['name']); a=byalias.get(p['name'])
        if 3<=p['n_invocations']<=200 and (p['x_span']>100 or p['y_span']>100):
            candidates.append({**p,'definition':d or a})

    # Small source contexts around candidate invocation starts, for human verification.
    ctx=[]
    for c in candidates[:25]:
        li=c['first_line']; lo=max(1,li-3); hi=min(len(lines),li+8)
        ctx.append(f"===== {c['name']} first invocation line {li} =====\n" + '\n'.join(f'{n:04d}: {lines[n-1]}' for n in range(lo,hi+1)))
    CTX.parent.mkdir(parents=True,exist_ok=True); CTX.write_text('\n\n'.join(ctx)+'\n',encoding='utf-8')

    out={'status':'LELLI2012B_UGC4483_FIG6_VECTOR_PROCEDURE_INVENTORY_COMPLETE',
         'arxiv':ARXIV,'source_package_sha256':hashlib.sha256(raw).hexdigest(),
         'fig6_sha256':hashlib.sha256(b).hexdigest(),'fig6_bytes':len(b),'n_lines':len(lines),
         'definitions':defs,'one_line_aliases':aliases,'procedure_invocation_summaries':procs,
         'candidate_coordinate_procedures':candidates,'axis_numeric_strings':strings,
         'long_native_segments':long_segments[:300],
         'next_gate':'identify_whole_galaxy_dot_procedure_and_axis_mapping_from_native_source',
         'boundary':'Static source geometry only; no PostScript execution, rendering, OCR, raster digitization, map reconstruction, profile fitting, persistence fitting, normalization, or blind-outcome inspection. L_A and C_A remain locked.'}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'fig6_sha256':out['fig6_sha256'],
                      'definitions':[{'name':d['name'],'line':d['start_line'],'fill':d['has_fill'],'stroke':d['has_stroke'],'local':d['local_ML_commands']} for d in defs],
                      'candidate_procs':[{k:c[k] for k in ('name','n_invocations','n_unique_xy','bbox','x_span','y_span','first_line','last_line')} for c in candidates],
                      'axis_strings':strings[:80]},indent=2))
if __name__=='__main__': main()
