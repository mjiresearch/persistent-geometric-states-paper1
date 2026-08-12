#!/usr/bin/env python3
"""Targeted continuation of the committed Ge04 source audit.

The broad audit established from paper.tex that Figure 2 is exactly fig2.eps,
but its generic graphics-reference regex missed the legacy psfig syntax. This
script does NOT repeat the broad audit. It directly opens that already-known
member and inventories its source-native PostScript structure, marker-like
coordinate sequences, text labels, and panel geometry.

No PostScript execution/rendering, OCR, raster digitization, map reconstruction,
normalization, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

URL='https://arxiv.org/e-print/astro-ph/0403154'
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ge04_fig2_native_vector_inventory_v1.json')
CTX=Path('validation/stationary/ge04_fig2_native_vector_context_v1.txt')
NUM=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?'
NAME=r'[A-Za-z_][A-Za-z0-9_.-]*'

req=urllib.request.Request(URL,headers={'User-Agent':UA})
with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
b=tf.extractfile(tf.getmember('fig2.eps')).read()
text=b.decode('latin-1','replace'); lines=text.splitlines()

# Basic structure.
image_ops=len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',text))
colorimage_ops=len(re.findall(r'(?<![A-Za-z])colorimage(?![A-Za-z])',text))
header=[z for z in lines[:100] if z.startswith(('%%Creator','%%Title','%%BoundingBox','%%Orientation','%%Pages'))]

# Collect custom procedure definitions with simple brace balancing.
defs=[]; i=0
while i<len(lines):
    line=lines[i].split('%',1)[0]
    m=re.search(r'/('+NAME+r')\s*\{',line)
    if not m:
        i+=1; continue
    name=m.group(1); start=i+1; chunk=line[m.start():]
    depth=chunk.count('{')-chunk.count('}'); j=i
    while depth>0 and j+1<len(lines):
        j+=1; z=lines[j].split('%',1)[0]; chunk+='\n'+z
        depth += z.count('{')-z.count('}')
    defs.append({'name':name,'start_line':start,'end_line':j+1,'body':chunk[:3500],
                 'has_fill':bool(re.search(r'\bfill\b',chunk)),'has_stroke':bool(re.search(r'\bstroke\b',chunk)),
                 'local_path_ops':len(re.findall(r'(?<!\S)(?:'+NUM+r')\s+(?:'+NUM+r')\s+(?:M|L|R|V|moveto|lineto|rlineto)(?!\S)',chunk))})
    i=j+1

def_ranges=[(d['start_line'],d['end_line']) for d in defs]
def inside_def(li): return any(a<=li<=b for a,b in def_ranges)
defnames={d['name'] for d in defs}

# Inventory numeric x y <procedure> calls outside definitions.
inv=defaultdict(list); pat=re.compile(r'('+NUM+r')\s+('+NUM+r')\s+('+NAME+r')\b')
for li,line in enumerate(lines,1):
    if inside_def(li): continue
    clean=line.split('%',1)[0]
    for m in pat.finditer(clean):
        name=m.group(3)
        if name in defnames:
            inv[name].append({'line':li,'x':float(m.group(1)),'y':float(m.group(2)),'text':line.strip()[:900]})

proc=[]
for name,pts in inv.items():
    xs=[p['x'] for p in pts]; ys=[p['y'] for p in pts]
    proc.append({'name':name,'n_invocations':len(pts),'n_unique_xy':len({(p['x'],p['y']) for p in pts}),
                 'bbox':[min(xs),min(ys),max(xs),max(ys)],'x_span':max(xs)-min(xs),'y_span':max(ys)-min(ys),
                 'first_line':min(p['line'] for p in pts),'last_line':max(p['line'] for p in pts),
                 'first_80_invocations':pts[:80]})
proc.sort(key=lambda z:(z['n_invocations'],z['x_span']+z['y_span']),reverse=True)

# Literal strings and nearby source anchors, useful for panel labels / axes.
strings=[]
for li,line in enumerate(lines,1):
    ss=re.findall(r'\((?:\\.|[^()])*\)',line)
    if ss:
        strings.append({'line':li,'strings':ss[:30],'text':line.strip()[:1200]})

# Explicit numeric labels and last absolute source coordinate anchor in preceding lines.
numlabels=[]
for z in strings:
    vals=[]
    for s in z['strings']:
        q=s[1:-1].strip()
        if re.fullmatch(r'[-+]?\d+(?:\.\d+)?',q): vals.append(q)
    if not vals: continue
    anchor=None
    for j in range(z['line']-2,max(-1,z['line']-18),-1):
        ms=list(re.finditer(r'('+NUM+r')\s+('+NUM+r')\s+(?:M|moveto)\b',lines[j]))
        if ms:
            m=ms[-1]; anchor={'line':j+1,'x':float(m.group(1)),'y':float(m.group(2))}; break
    numlabels.append({'line':z['line'],'values':vals,'anchor':anchor,'text':z['text']})

# Source lines containing target/panel labels or axis-quantity words.
keyword=[]
for li,line in enumerate(lines,1):
    if re.search(r'(?i)ESO|116|79|radius|surface|density|M.?sun|pc|arcsec|kpc|approach|reced|average|Sigma|H.?I',line):
        keyword.append({'line':li,'text':line[:1200]})

# Long line/relative-vector commands can reveal panel frames/ticks.
longgeom=[]
for li,line in enumerate(lines,1):
    for m in re.finditer(r'('+NUM+r')\s+('+NUM+r')\s+(?:R|V|rlineto)\b',line):
        dx,dy=map(float,m.groups())
        if abs(dx)>=100 or abs(dy)>=100:
            longgeom.append({'line':li,'delta':[dx,dy],'text':line.strip()[:900]})

# Heuristic candidates: custom procedures invoked repeatedly across nontrivial spans.
candidates=[]; bydef={d['name']:d for d in defs}
for p in proc:
    if p['n_invocations']>=3 and (p['x_span']>=100 or p['y_span']>=100):
        candidates.append({**p,'definition':bydef.get(p['name'])})

# Persist bounded human-readable contexts around candidate procedure definitions and invocations.
ctx=[]
for c in candidates[:40]:
    d=c.get('definition')
    if d:
        lo=max(1,d['start_line']-2); hi=min(len(lines),d['end_line']+2)
        ctx.append(f"===== DEF {c['name']} lines {d['start_line']}-{d['end_line']} =====\n"+'\n'.join(f'{n:05d}: {lines[n-1]}' for n in range(lo,hi+1)))
    li=c['first_line']; lo=max(1,li-4); hi=min(len(lines),li+12)
    ctx.append(f"===== FIRST CALL {c['name']} line {li} =====\n"+'\n'.join(f'{n:05d}: {lines[n-1]}' for n in range(lo,hi+1)))
# Axis/label sections.
for z in keyword[:80]:
    li=z['line']; lo=max(1,li-2); hi=min(len(lines),li+2)
    ctx.append(f"===== KEYWORD line {li} =====\n"+'\n'.join(f'{n:05d}: {lines[n-1]}' for n in range(lo,hi+1)))
CTX.parent.mkdir(parents=True,exist_ok=True);CTX.write_text('\n\n'.join(ctx)+'\n',encoding='utf-8')

out={'status':'GE04_FIG2_NATIVE_VECTOR_INVENTORY_COMPLETE',
     'source_package_sha256':hashlib.sha256(raw).hexdigest(),'fig2_sha256':hashlib.sha256(b).hexdigest(),
     'fig2_bytes':len(b),'n_lines':len(lines),'header':header,
     'image_ops':image_ops,'colorimage_ops':colorimage_ops,
     'native_vector_candidate':image_ops==0 and colorimage_ops==0,
     'procedure_definitions':defs,'procedure_invocation_summaries':proc,
     'candidate_coordinate_procedures':candidates,'numeric_label_anchors':numlabels,
     'keyword_lines':keyword[:400],'long_geometry':longgeom[:500],
     'next_gate':('identify_panel_order_filled_circle_average_series_and_axes' if image_ops==0 and colorimage_ops==0 else 'no_exact_vector_route_check_other_numeric_asset'),
     'boundary':'Targeted continuation from committed Ge04 audit; no PostScript execution/rendering, OCR, raster digitization, map reconstruction, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'fig2_sha256':out['fig2_sha256'],'header':header,
                  'image_ops':image_ops,'colorimage_ops':colorimage_ops,'native_vector_candidate':out['native_vector_candidate'],
                  'candidate_procs':[{k:c[k] for k in ('name','n_invocations','n_unique_xy','bbox','x_span','y_span','first_line','last_line')} for c in candidates],
                  'numeric_labels':numlabels[:120],'keyword_lines':keyword[:120],'next_gate':out['next_gate']},indent=2))
