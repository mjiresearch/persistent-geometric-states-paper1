#!/usr/bin/env python3
"""Statically parse IDL path/style commands from Ha14 fig-density.eps.

Only a tiny known subset of the IDL prolog is interpreted as geometry metadata:
M=moveto, R=rlineto, P=lineto, D=stroke-preserving-currentpoint, L0..L5=dash
style. PostScript is not executed.
"""
from __future__ import annotations
import hashlib, io, json, math, re, tarfile, urllib.request
from pathlib import Path
URLS=['https://arxiv.org/e-print/1407.1744','https://export.arxiv.org/e-print/1407.1744']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_density_eps_path_inventory_v1.json')

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
    with urllib.request.urlopen(req,timeout=180) as h:return h.read()

def main():
    raw=None
    for u in URLS:
        try: raw=fetch(u);break
        except Exception: pass
    if raw is None: raise SystemExit('fetch failed')
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*'); b=tf.extractfile(tf.getmember('fig-density.eps')).read(); text=b.decode('latin-1','replace')
    lines=text.splitlines()
    # Start after page setup to avoid interpreting procedure definitions.
    page_start=next((i for i,l in enumerate(lines) if l.startswith('%%EndPageSetup')),0)+1
    src='\n'.join(lines[page_start:])
    # Remove comments and parenthesized strings so vector-font labels do not leak arbitrary words.
    clean=[]
    for line in src.splitlines():
        if '%' in line: line=line.split('%',1)[0]
        line=re.sub(r'\((?:\\.|[^()])*\)',' ',line)
        clean.append(line)
    src='\n'.join(clean)
    toks=re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?|[A-Za-z][A-Za-z0-9_]*|\[|\]',src)
    stack=[];cur=None;path=[];paths=[];color=(0.,0.,0.);width=10.;dash='L0';seq=0
    def num(x):
        try:return float(x)
        except:return None
    def popn(n):
        if len(stack)<n:return None
        vals=stack[-n:];del stack[-n:]
        if not all(isinstance(v,(int,float)) for v in vals):return None
        return vals
    def finish():
        nonlocal path,seq
        if len(path)>=2:
            seq+=1;xs=[p[0] for p in path];ys=[p[1] for p in path]
            paths.append({'seq':seq,'n_points':len(path),'color':[round(x,6) for x in color],'width':width,'dash':dash,
                          'bbox':[min(xs),min(ys),max(xs),max(ys)],'start':path[0],'end':path[-1],
                          'points':path[:] if len(path)<=250 else path[:250]})
        path=[]
    for t in toks:
        v=num(t)
        if v is not None: stack.append(v);continue
        if t=='M':
            vals=popn(2)
            if vals:
                x,y=vals;cur=(x,y);path=[cur]
        elif t=='R':
            vals=popn(2)
            if vals and cur is not None:
                dx,dy=vals;cur=(cur[0]+dx,cur[1]+dy);path.append(cur)
        elif t=='P':
            vals=popn(2)
            if vals:
                x,y=vals;cur=(x,y);path.append(cur)
        elif t=='D':
            finish()
            if cur is not None:path=[cur]
        elif t in {'L0','L1','L2','L3','L4','L5'}:
            dash=t
        elif t=='setrgbcolor':
            vals=popn(3)
            if vals: color=tuple(vals)
        elif t=='setgray' or t=='K':
            vals=popn(1)
            if vals:color=(vals[0],)*3
        elif t=='setlinewidth':
            vals=popn(1)
            if vals:width=vals[0]
        elif t in {'stroke'}:
            finish()
        else:
            # Unknown operator: avoid letting its operands pollute later style commands.
            # Keep only a short numeric stack because IDL path commands place operands immediately before aliases.
            if len(stack)>12:stack=stack[-12:]
    finish()
    # Long paths are the scientifically relevant candidates; font glyphs are typically short/local.
    long=[p for p in paths if p['n_points']>=8]
    black=[p for p in long if max(abs(c) for c in p['color'])<1e-8]
    nonblack=[p for p in long if p not in black]
    # Rank candidate black traces by horizontal span and number of points, excluding obvious page-wide axes by requiring finite vertical span.
    candidates=[]
    for p in black:
        x0,y0,x1,y1=p['bbox'];xs=x1-x0;ys=y1-y0
        if xs>1000 and ys>50:
            q=dict(p);q['x_span']=xs;q['y_span']=ys;q['candidate_score']=p['n_points']+xs/500+ys/500;candidates.append(q)
    candidates.sort(key=lambda p:p['candidate_score'],reverse=True)
    out={'status':'HA14_DENSITY_EPS_PATH_INVENTORY_COMPLETE','asset_sha256':hashlib.sha256(b).hexdigest(),
         'n_paths':len(paths),'n_long_paths':len(long),'n_long_black_paths':len(black),'long_paths':long,
         'black_profile_candidates':candidates[:40],
         'boundary':'Static parsing of known IDL geometry/style aliases only; PostScript not executed; no raster digitization, profile normalization, persistence fitting, or blind-outcome inspection.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'n_paths':len(paths),'n_long':len(long),'n_black':len(black),'candidates':candidates[:20],
      'nonblack_long':[p for p in nonblack if p['n_points']>=15][:20]},indent=2))
if __name__=='__main__':main()
