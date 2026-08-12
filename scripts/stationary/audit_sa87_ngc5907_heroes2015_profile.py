#!/usr/bin/env python3
"""Audit SA87 / NGC5907 via the later direct HEROES-II H I profile route.

SPARC/Lelli SA87 is Sancisi & van Albada (1987), a review. NGC5907's original
H I lineage goes back to Sancisi (1976). Rather than extracting an old scan,
this audit inspects Allaert et al. (2015; arXiv:1507.03095), which re-reduces
archival H I data and derives the radial H I surface-density profile with a
3-D tilted-ring model. Figure 29 explicitly plots Sigma_HI versus radius.

Acquisition/provenance only. No raster digitization, map/cube reconstruction,
profile fitting, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import hashlib, io, json, re, subprocess, tarfile, tempfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV='1507.03095'
URLS=[f'https://arxiv.org/e-print/{ARXIV}',f'https://export.arxiv.org/e-print/{ARXIV}']
OUT=Path('validation/stationary/sa87_ngc5907_heroes2015_profile_asset_audit_v1.json')
CTX=Path('validation/stationary/sa87_ngc5907_heroes2015_fig29_context_v1.txt')

def h(b):return hashlib.sha256(b).hexdigest()
def dec(b):return b.decode('latin-1',errors='replace')
def fetch():
    errs=[]
    for u in URLS:
        try:
            with urlopen(Request(u,headers={'User-Agent':'PaperI-SA87-HEROES-audit/1.0'}),timeout=90) as r:
                return r.read(),r.geturl(),r.headers.get_content_type()
        except Exception as e:errs.append([u,repr(e)])
    raise RuntimeError(errs)
def unpack(b):
    out={}
    with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as tf:
        for m in tf.getmembers():
            if m.isfile():
                f=tf.extractfile(m)
                if f:out[m.name]=f.read()
    return out

def ps_info(name,b):
    t=dec(b)
    def n(op):return len(re.findall(r'(?<![A-Za-z])'+re.escape(op)+r'(?![A-Za-z])',t))
    ops={x:n(x) for x in ['image','colorimage','imagemask','moveto','lineto','rlineto','curveto','arc','stroke','fill','show']}
    strings=re.findall(r'\(([^()]{1,180})\)',t)
    keep=[s for s in strings if re.search(r'NGC|5907|Sigma|H.?I|Radius|kpc|pc|M.?sun|approach|reced',s,re.I)]
    return {'name':name,'bytes':len(b),'sha256':h(b),'ops':ops,
            'native_vector_candidate':ops['image']==0 and ops['colorimage']==0 and ops['imagemask']==0 and sum(ops[x] for x in ['lineto','rlineto','curveto','arc','stroke','fill'])>20,
            'interesting_strings':keep[:180],'begin_document':re.findall(r'%%BeginDocument:\s*([^\r\n]+)',t)[:60],'header':t[:600]}
def pdf_info(name,b):
    info={'name':name,'bytes':len(b),'sha256':h(b),'extension':'.pdf','native_vector_candidate':None}
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'x.pdf';p.write_bytes(b)
        for cmd,key in [(['pdfimages','-list',str(p)],'pdfimages_list'),(['pdffonts',str(p)],'pdffonts'),(['pdftotext','-layout',str(p),'-'],'pdftotext')]:
            try:
                r=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
                info[key]=(r.stdout+r.stderr)[:12000]
            except Exception as e:info[key+'_error']=repr(e)
    img=info.get('pdfimages_list','')
    # If pdfimages lists no actual image rows beyond header, vector is plausible.
    rows=[ln for ln in img.splitlines() if re.match(r'\s*\d+\s+\d+\s+',ln)]
    info['embedded_image_rows']=rows[:100]
    info['embedded_image_count']=len(rows)
    info['native_vector_candidate']=(len(rows)==0 and bool(info.get('pdftotext','').strip()))
    return info

def main():
    payload,url,ctype=fetch();files=unpack(payload)
    tex={n:dec(b) for n,b in files.items() if n.lower().endswith(('.tex','.ltx'))}
    contexts=[];refs=[]
    pats=[r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',r'\\epsfig\{[^}]*file\s*=\s*([^,}\s]+)',r'\\plotone\{([^}]+)\}',r'\\plottwo\{([^}]+)\}\{([^}]+)\}']
    for n,t in tex.items():
        lines=t.splitlines()
        for i,line in enumerate(lines):
            w='\n'.join(lines[max(0,i-14):min(len(lines),i+18)])
            low=w.lower()
            if not (('fig' in low and ('29' in low or 'radially dependent' in low)) or ('ngc 5907' in low and 'surface density' in low)):
                continue
            ctx='\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-14),min(len(lines),i+18)))
            if (n,ctx) not in {(x['tex_file'],x['context']) for x in contexts}:contexts.append({'tex_file':n,'line':i+1,'context':ctx})
            for pat in pats:
                for m in re.finditer(pat,w):refs.extend([g.strip() for g in m.groups() if g])
    refs=list(dict.fromkeys(refs))
    cand=[]
    for r in refs:
        rb=Path(r).name
        for n in files:
            nb=Path(n).name
            if n==r or nb==rb or Path(nb).stem==Path(rb).stem:cand.append(n)
    for n in files:
        if re.search(r'fig.?29|rad.*param|parameter|sigma|surf.*dens',n,re.I):cand.append(n)
    cand=list(dict.fromkeys(cand))
    inspected=[]
    for n in cand:
        b=files[n];lo=n.lower()
        if lo.endswith(('.eps','.ps')):inspected.append(ps_info(n,b))
        elif lo.endswith('.pdf'):inspected.append(pdf_info(n,b))
        else:inspected.append({'name':n,'bytes':len(b),'sha256':h(b),'extension':Path(n).suffix.lower(),'native_vector_candidate':False})
    side=[]
    for n,b in files.items():
        if n.lower().endswith(('.dat','.txt','.tab','.csv','.tbl','.table')):
            side.append({'name':n,'bytes':len(b),'sha256':h(b),'preview':dec(b)[:3000]})
    result={
      'status':'SA87_NGC5907_HEROES2015_PROFILE_ASSET_AUDIT_COMPLETE','sparc_ref_id':'SA87','galaxy':'NGC5907','stationary_role':'calibration',
      'lelli_source':'Sancisi & van Albada 1987 IAUS 117, 67-81 (review paper)',
      'original_hi_lineage':'Sancisi 1976 A&A 53,159, Warped HI Disks in Galaxies; WSRT NGC5907 observations',
      'later_direct_public_source':'Allaert et al. 2015 A&A 582 A18, HEROES II; arXiv:1507.03095',
      'later_source_method':'re-reduced archival H I data; detailed 3-D tilted-ring modelling; Figure 29 plots radially dependent H I surface density, rotation velocity, inclination, PA and vertical scale height; approaching/receding sides separately',
      'public_source_url':url,'content_type':ctype,'source_bytes':len(payload),'source_sha256':h(payload),'n_source_files':len(files),
      'figure29_contexts':contexts[:120],'graphics_references':refs,'candidate_assets':inspected,'numeric_sidecar_candidates':side,
      'file_inventory':[{'name':n,'bytes':len(b),'sha256':h(b)} for n,b in sorted(files.items())],
      'next_action':'If the Figure 29 source asset is native vector, isolate the NGC5907 Sigma_HI panel/series and calibrate source-native axes. If numerical sidecar exists, use it preferentially. Otherwise record the direct-profile route but defer under current no-raster/no-map-reconstruction protocol.',
      'boundary':'No raster digitization, OCR, PostScript execution, calibrated-cube reconstruction, profile refitting, common normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
    lines=[]
    for c in contexts[:120]:lines += [f"--- {c['tex_file']} line {c['line']} ---",c['context'],'']
    lines += ['Candidate assets:']+[json.dumps(x,ensure_ascii=False) for x in inspected]+['','Numeric sidecars:']+[json.dumps(x,ensure_ascii=False) for x in side]
    CTX.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':result['status'],'n_files':len(files),'candidates':[x['name'] for x in inspected],'native_vector_candidates':[x['name'] for x in inspected if x.get('native_vector_candidate') is True],'numeric_sidecars':[x['name'] for x in side],'outputs':[str(OUT),str(CTX)]},indent=2))
if __name__=='__main__':main()
