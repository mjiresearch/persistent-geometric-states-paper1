#!/usr/bin/env python3
"""Audit a later exact public H I profile route for RA85 / UGC02885 (UGC 2885).

RA85 is Roelfsema & Allen (1985).  Before accepting an old scanned-figure
boundary, inspect the later direct WSRT H I observations in Hunter et al. (2013),
arXiv:1307.7116, which explicitly derive H I surface densities from the integrated
H I map using the same ellipse geometry/14.8-arcsec radial step as the optical
surface photometry.

Acquisition/provenance only: no raster digitization, image reconstruction,
helium guessing, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV='1307.7116'
URLS=[f'https://arxiv.org/e-print/{ARXIV}',f'https://export.arxiv.org/e-print/{ARXIV}']
OUT=Path('validation/stationary/ra85_ugc2885_hunter2013_public_profile_audit_v1.json')
CTX=Path('validation/stationary/ra85_ugc2885_hunter2013_source_context_v1.txt')

def h(b): return hashlib.sha256(b).hexdigest()
def dec(b): return b.decode('latin-1',errors='replace')

def fetch():
    errs=[]
    for u in URLS:
        try:
            with urlopen(Request(u,headers={'User-Agent':'PaperI-RA85-audit/1.0'}),timeout=60) as r:
                return r.read(),r.geturl(),r.headers.get_content_type()
        except Exception as e: errs.append([u,repr(e)])
    raise RuntimeError(errs)

def unpack(b):
    out={}
    with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as tf:
        for m in tf.getmembers():
            if m.isfile():
                f=tf.extractfile(m)
                if f: out[m.name]=f.read()
    return out

def ps_info(name,b):
    t=dec(b)
    def n(op): return len(re.findall(r'(?<![A-Za-z])'+re.escape(op)+r'(?![A-Za-z])',t))
    ops={x:n(x) for x in ['image','colorimage','imagemask','moveto','lineto','rlineto','curveto','arc','stroke','fill','show']}
    strings=re.findall(r'\(([^()]{1,160})\)',t)
    keep=[s for s in strings if re.search(r'HI|H I|H\\,?I|gas|surface|density|kpc|arcsec|M.?sun|Sigma|radius|UGC|2885|R/R',s,re.I)]
    return {
        'name':name,'bytes':len(b),'sha256':h(b),'ops':ops,
        'native_vector_candidate': ops['image']==0 and ops['colorimage']==0 and ops['imagemask']==0 and sum(ops[x] for x in ['lineto','rlineto','curveto','arc','stroke','fill'])>10,
        'interesting_strings':keep[:160],
        'begin_document':re.findall(r'%%BeginDocument:\s*([^\r\n]+)',t)[:40],
        'header':t[:500],
    }

def main():
    payload,url,ctype=fetch(); files=unpack(payload)
    tex={n:dec(b) for n,b in files.items() if n.lower().endswith(('.tex','.ltx'))}
    contexts=[]; graphics=[]
    context_terms=['H\\,{\\sc i} surface','H\\,i surface','H i surface','H I surface','surface dens','gas and stellar','gas surface','UGC 2885','UGC~2885','UGC~2885']
    fig_patterns=[
        r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',
        r'\\epsfig\{[^}]*file\s*=\s*([^,}\s]+)',
        r'\\plotone\{([^}]+)\}',
        r'\\plottwo\{([^}]+)\}\{([^}]+)\}',
    ]
    for n,t in tex.items():
        lines=t.splitlines()
        for i,line in enumerate(lines):
            w='\n'.join(lines[max(0,i-12):min(len(lines),i+14)])
            low=w.lower()
            interesting=(('ugc' in low and '2885' in low and ('surface' in low or 'sigma' in low or 'gas' in low or 'h i' in low or 'h\\' in low)) or
                         ('h' in low and 'surface dens' in low) or
                         ('figure' in low and ('14' in low or '15' in low) and ('gas' in low or 'ugc' in low)))
            if not interesting: continue
            ctx='\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-12),min(len(lines),i+14)))
            key=(n,ctx)
            if key not in {(x['tex_file'],x['context']) for x in contexts}:
                contexts.append({'tex_file':n,'line':i+1,'context':ctx})
            for pat in fig_patterns:
                for m in re.finditer(pat,w):
                    graphics.extend([g.strip() for g in m.groups() if g])
    graphics=list(dict.fromkeys(graphics))

    # Match referenced names plus filename heuristics.
    candidates=[]
    for r in graphics:
        rb=Path(r).name
        for n in files:
            nb=Path(n).name
            if n==r or nb==rb or Path(nb).stem==Path(rb).stem: candidates.append(n)
    for n in files:
        if re.search(r'2885|ugc|gas|hi|surf|dens|sigma|prof|fig.?1[345]',n,re.I): candidates.append(n)
    candidates=list(dict.fromkeys(candidates))

    inspected=[]
    for n in candidates:
        b=files[n]; low=n.lower()
        if low.endswith(('.eps','.ps')) and len(b)<25_000_000: inspected.append(ps_info(n,b))
        else: inspected.append({'name':n,'bytes':len(b),'sha256':h(b),'extension':Path(n).suffix.lower(),'native_vector_candidate':False})

    side=[]
    for n,b in files.items():
        if n.lower().endswith(('.dat','.txt','.tab','.csv','.tbl','.table')):
            side.append({'name':n,'bytes':len(b),'sha256':h(b),'preview':dec(b)[:2500]})

    # Record snippets that may specify gas/He convention without interpreting it here.
    convention=[]
    for n,t in tex.items():
        lines=t.splitlines()
        for i,line in enumerate(lines):
            if re.search(r'helium|He\b|1\.3[0-9]|1\.4|H.?I.*mass|gas mass|Sigma.*gas|surface densit',line,re.I):
                convention.append({'tex_file':n,'line':i+1,'text':line[:1000]})

    result={
        'status':'RA85_UGC2885_HUNTER2013_PUBLIC_PROFILE_AUDIT_COMPLETE',
        'sparc_ref_id':'RA85','galaxy':'UGC02885','source_alias':'UGC 2885','stationary_role':'calibration',
        'lelli_source':'Roelfsema & Allen 1985 A&A 146 213',
        'later_direct_public_source':'Hunter et al. 2013 AJ 146 92; arXiv:1307.7116',
        'public_source_url':url,'content_type':ctype,'source_bytes':len(payload),'source_sha256':h(payload),'n_source_files':len(files),
        'published_method_facts':{
            'instrument':'WSRT','observation_year':2004,'on_source_hours':24,
            'beam_arcsec':'22.3 x 13.6','channel_width_km_s':2.06,'pixel_arcsec':4.0,
            'total_hi_flux_jy_km_s':28.3,'total_hi_mass_msun':4.2e10,
            'profile_method':'H I surface densities from integrated H I map using GIPSY; ellipse parameters and 14.8-arcsec radial step same as optical/near-IR surface photometry'
        },
        'tex_contexts':contexts[:120],'graphics_references':graphics,'candidate_assets':inspected,'numeric_sidecar_candidates':side,
        'gas_helium_convention_snippets':convention[:160],
        'file_inventory':[{'name':n,'bytes':len(b),'sha256':h(b)} for n,b in sorted(files.items())],
        'next_action':'Identify the exact UGC2885 radial H I/gas profile graphic or numerical sidecar. If native-vector, extract source series and calibrate axes from source-native labels/ticks. Preserve any stated helium convention separately. If no exact numeric/vector route exists, disposition this later public route and then assess the original RA85 scan only as provenance, without raster digitization.',
        'boundary':'No raster digitization, OCR, PostScript execution, H I map reconstruction, helium guessing, common normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2)+'\n')
    lines=[]
    for c in contexts[:120]: lines += [f"--- {c['tex_file']} line {c['line']} ---",c['context'],'']
    lines += ['Candidate assets:']+[json.dumps(x,ensure_ascii=False) for x in inspected]+['','Numeric sidecars:']+[json.dumps(x,ensure_ascii=False) for x in side]+['','Gas/helium convention snippets:']+[json.dumps(x,ensure_ascii=False) for x in convention[:160]]
    CTX.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':result['status'],'n_files':len(files),'candidates':[x['name'] for x in inspected],'native_vector_candidates':[x['name'] for x in inspected if x.get('native_vector_candidate')],'numeric_sidecars':[x['name'] for x in side],'outputs':[str(OUT),str(CTX)]},indent=2))

if __name__=='__main__': main()
