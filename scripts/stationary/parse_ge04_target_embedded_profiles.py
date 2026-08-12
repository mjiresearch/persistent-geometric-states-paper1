#!/usr/bin/env python3
"""Parse the two target SuperMongo EPS subdocuments embedded in Ge04 fig2.eps.

The committed Ge04 native-vector inventory established that fig2.eps is an
Xfig wrapper containing imported SuperMongo radial-profile EPS panels, including
`116readradialgraph.mr.eps` and `79readradialgraph.mr.eps`. This continuation
statically interprets only the simple drawing aliases in those two embedded EPS
streams (M/m/L/l, B, CS, CF), inventories filled marker polygons, and derives
plot-frame/tick geometry. It does not render or execute PostScript.
"""
from __future__ import annotations
import hashlib, io, json, math, re, tarfile, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

URL='https://arxiv.org/e-print/astro-ph/0403154'
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ge04_target_embedded_profile_vectors_v1.json')
CTX=Path('validation/stationary/ge04_target_embedded_profile_vectors_context_v1.txt')
TARGETS={'ESO116-G12':'116readradialgraph.mr.eps','ESO79-G14':'79readradialgraph.mr.eps'}
NUM_RE=re.compile(r'^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?$')
TOKEN_RE=re.compile(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?|[A-Za-z][A-Za-z0-9_]*')

req=urllib.request.Request(URL,headers={'User-Agent':UA})
with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
fig=tf.extractfile(tf.getmember('fig2.eps')).read()
text=fig.decode('latin-1','replace'); lines=text.splitlines()


def extract_embedded(name):
    begin=None; end=None
    for i,line in enumerate(lines):
        if line.strip()==f'%%BeginDocument: {name}': begin=i+1
        if begin is not None and i>begin and line.strip().startswith('%%EndDocument'):
            end=i; break
    if begin is None or end is None:
        raise RuntimeError(f'Embedded document not found: {name}')
    return begin+1,end,[z for z in lines[begin:end]]  # 1-based source line of first embedded line


def parse_panel(src_lines, global_first_line):
    # Locate the simple SuperMongo graphics aliases to document semantics.
    defs=[]
    for j,line in enumerate(src_lines,global_first_line):
        if re.search(r'/[A-Za-z][A-Za-z0-9_]*\s*\{',line):
            if any('/'+n in line for n in ['B ','CS ','CF ','L ','l ','M ','m ','P ','T ']):
                defs.append({'line':j,'text':line[:1000]})

    # Drop comments and literal strings before tokenization; font-vector paths remain
    # but are distinguishable by geometry/location.
    toks=[]
    for li,line in enumerate(src_lines,global_first_line):
        clean=line.split('%',1)[0]
        clean=re.sub(r'\((?:\\.|[^()])*\)',' ',clean)
        for t in TOKEN_RE.findall(clean): toks.append((li,t))

    stack=[]; cur=None; path=[]; fills=[]; strokes=[]; moves=[]
    def pop2():
        if len(stack)<2:return None
        y=stack.pop(); x=stack.pop()
        return (x,y) if isinstance(x,float) and isinstance(y,float) else None
    def flush(kind,li):
        nonlocal path
        if len(path)>=2:
            rec={'line':li,'points':[list(p) for p in path]}
            xs=[p[0] for p in path];ys=[p[1] for p in path]
            rec['bbox']=[min(xs),min(ys),max(xs),max(ys)]
            rec['width']=max(xs)-min(xs);rec['height']=max(ys)-min(ys)
            rec['n_points']=len(path);rec['n_unique_points']=len(set(path))
            (fills if kind=='fill' else strokes).append(rec)
        path=[]
    for li,t in toks:
        if NUM_RE.fullmatch(t):
            stack.append(float(t)); continue
        if t=='M':
            p=pop2()
            if p is not None: cur=p; path=[cur]; moves.append({'line':li,'op':'M','to':list(cur)})
        elif t=='m':
            p=pop2()
            if p is not None and cur is not None: cur=(cur[0]+p[0],cur[1]+p[1]);path=[cur];moves.append({'line':li,'op':'m','to':list(cur)})
        elif t=='L':
            p=pop2()
            if p is not None:
                cur=p
                if not path:path=[cur]
                else:path.append(cur)
        elif t=='l':
            p=pop2()
            if p is not None and cur is not None:
                cur=(cur[0]+p[0],cur[1]+p[1])
                if not path:path=[cur]
                else:path.append(cur)
        elif t=='B':
            # In this SM prolog B is currentpoint/newpath/moveto: preserve current
            # point as the start of a fresh marker/path.
            if cur is not None:path=[cur]
        elif t=='CF':
            flush('fill',li)
        elif t=='CS':
            flush('stroke',li)
        elif t in {'stroke','S'}:
            flush('stroke',li)
        elif t in {'eofill','fill','F'}:
            flush('fill',li)
        else:
            # Keep only a bounded operand stack so unrelated font/scaling operands
            # cannot leak into later graphics aliases.
            if len(stack)>16: stack=stack[-16:]

    # Shape clusters for fills. Quantize dimensions to 2 source units; source marker
    # polygons are strongly repeated while text glyph fills are not.
    clusters=defaultdict(list)
    for f in fills:
        key=(f['n_unique_points'],round(f['width']/2)*2,round(f['height']/2)*2)
        clusters[key].append(f)
    shape_clusters=[]
    for key,arr in clusters.items():
        centers=[]
        for f in arr:
            x0,y0,x1,y1=f['bbox']; centers.append([(x0+x1)/2,(y0+y1)/2,f['line']])
        shape_clusters.append({'signature':{'n_unique_points':key[0],'width':key[1],'height':key[2]},
                               'n_paths':len(arr),'bbox':[min(c[0] for c in centers),min(c[1] for c in centers),max(c[0] for c in centers),max(c[1] for c in centers)],
                               'centers':centers[:300],'sample_paths':arr[:8]})
    shape_clusters.sort(key=lambda z:z['n_paths'],reverse=True)

    # Candidate plot frame from stroked rectangular/long paths.
    long_strokes=[s for s in strokes if s['width']>800 or s['height']>600]
    frame=None
    # Known SM frame often appears as connected path spanning max x/y. Pick largest
    # axis-aligned stroke bounding box in plausible plot coordinates.
    plausible=[s for s in long_strokes if 200<=s['bbox'][0]<=600 and 1000<=s['bbox'][2]<=2200 and 200<=s['bbox'][1]<=600 and 1000<=s['bbox'][3]<=1600]
    if plausible:
        q=max(plausible,key=lambda s:s['width']*s['height']);frame=q['bbox']

    # All short axis-aligned stroke segments touching a frame edge become tick candidates.
    ticks=[]
    if frame:
        x0,y0,x1,y1=frame; tol=3
        for s in strokes:
            pts=s['points']
            for a,b in zip(pts,pts[1:]):
                ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay
                if abs(dx)<1e-9 and abs(dy)<=150 and (abs(ay-y0)<=tol or abs(ay-y1)<=tol or abs(by-y0)<=tol or abs(by-y1)<=tol):
                    ticks.append({'axis':'x','pos':ax,'length':abs(dy),'a':a,'b':b,'line':s['line']})
                if abs(dy)<1e-9 and abs(dx)<=150 and (abs(ax-x0)<=tol or abs(ax-x1)<=tol or abs(bx-x0)<=tol or abs(bx-x1)<=tol):
                    ticks.append({'axis':'y','pos':ay,'length':abs(dx),'a':a,'b':b,'line':s['line']})
    # Dedupe tick positions and retain maximum stroke length at each coordinate.
    tick_summary={}
    for axis in ('x','y'):
        d=defaultdict(float)
        for z in ticks:
            if z['axis']==axis:d[round(z['pos'],3)]=max(d[round(z['pos'],3)],z['length'])
        tick_summary[axis]=[{'pos':k,'max_length':v} for k,v in sorted(d.items())]

    return {'definitions':defs,'n_filled_paths':len(fills),'n_stroked_paths':len(strokes),
            'shape_clusters':shape_clusters,'long_strokes':long_strokes[:80],
            'frame':frame,'tick_summary':tick_summary}

panels={};ctx=[]
for galaxy,name in TARGETS.items():
    first,last,src=extract_embedded(name)
    p=parse_panel(src,first);p['embedded_name']=name;p['global_line_range']=[first,last];panels[galaxy]=p
    ctx.append(f'===== {galaxy} {name} global lines {first}-{last} =====')
    for z in p['definitions']:ctx.append(f"DEF {z['line']}: {z['text']}")
    ctx.append('FRAME '+repr(p['frame']))
    ctx.append('TICKS '+json.dumps(p['tick_summary']))
    for c in p['shape_clusters'][:12]:
        ctx.append('SHAPE '+json.dumps({'signature':c['signature'],'n_paths':c['n_paths'],'bbox':c['bbox'],'centers':c['centers'][:80]}))

out={'status':'GE04_TARGET_EMBEDDED_PROFILE_VECTOR_PARSE_COMPLETE',
     'source_package_sha256':hashlib.sha256(raw).hexdigest(),'fig2_sha256':hashlib.sha256(fig).hexdigest(),
     'targets':panels,
     'next_gate':'identify_filled_circle_cluster_then_apply_native_axis_calibration',
     'boundary':'Static interpretation of known SuperMongo geometry aliases only; no PostScript execution/rendering, OCR, raster digitization, map reconstruction, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
CTX.write_text('\n'.join(ctx)+'\n')
print(json.dumps({'status':out['status'],'targets':{g:{'frame':p['frame'],'ticks':p['tick_summary'],'shapes':[{'signature':c['signature'],'n_paths':c['n_paths'],'bbox':c['bbox'],'centers':c['centers'][:60]} for c in p['shape_clusters'][:15]]} for g,p in panels.items()}},indent=2))
