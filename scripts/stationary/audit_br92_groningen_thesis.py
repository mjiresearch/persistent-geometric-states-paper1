#!/usr/bin/env python3
"""One-pass audit of the current University of Groningen Broeils 1992 thesis deposit.

Live SPARC/Lelli source family: Br92, six frozen galaxies.
This uses the current institutional repository, not historical WHISP/atlas URLs.
Acquisition/provenance only; no profile values or persistence parameters are fit.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

LANDING='https://research.rug.nl/en/publications/dark-and-visible-matter-in-spiral-galaxies/'
KNOWN_PDF='https://research.rug.nl/files/3332246/broeils.PDF'
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
TARGETS=['NGC 801','NGC 1003','NGC 2683','NGC 2998','NGC 5985','NGC 6674']


def get(url, referer=None):
    headers={'User-Agent':UA,'Accept':'text/html,application/pdf,*/*'}
    if referer: headers['Referer']=referer
    req=Request(url,headers=headers)
    with urlopen(req,timeout=90) as r:
        return r.read(),r.headers.get('Content-Type',''),r.geturl()


def sha(b): return hashlib.sha256(b).hexdigest()


def contexts(lines, phrase, radius=6):
    out=[]; rx=re.compile(re.escape(phrase).replace(r'\ ',r'\s*'),re.I)
    for i,l in enumerate(lines):
        if rx.search(l):
            lo=max(0,i-radius); hi=min(len(lines),i+radius+1)
            out.append({'line':i+1,'start':lo+1,'end':hi,'context':[{'line':j+1,'text':lines[j][:1200]} for j in range(lo,hi)]})
    return out[:100]


def main():
    result={
      'status':'BR92_GRONINGEN_THESIS_AUDIT',
      'source':'Broeils 1992 PhD thesis, Dark and visible matter in spiral galaxies, University of Groningen',
      'landing_url':LANDING,'known_pdf_url':KNOWN_PDF,
      'frozen_targets':TARGETS,
      'boundary':'Institutional-source audit only. No numerical profile is promoted unless a direct table/curve and its physical units/conventions are unambiguous.'
    }
    try:
        html,ct,final=get(LANDING)
        result['landing']={'ok':True,'bytes':len(html),'content_type':ct,'final_url':final,'sha256':sha(html)}
        text=html.decode('utf-8','replace')
        hrefs=re.findall(r'href=["\']([^"\']+)["\']',text,re.I)
        result['landing_pdf_hrefs']=[h for h in hrefs if 'broeils' in h.lower() or '.pdf' in h.lower()]
    except Exception as e:
        result['landing']={'ok':False,'error':f'{type(e).__name__}: {e}'}
        result['landing_pdf_hrefs']=[]

    urls=[]
    for h in result['landing_pdf_hrefs']+[KNOWN_PDF]:
        if h.startswith('/'):
            h='https://research.rug.nl'+h
        if h not in urls: urls.append(h)
    result['pdf_attempts']=[]
    pdf=None; pdf_url=None
    for u in urls:
        try:
            b,ct,final=get(u,LANDING)
            rec={'url':u,'ok':True,'bytes':len(b),'content_type':ct,'final_url':final,'sha256':sha(b),'magic':b[:8].decode('latin-1','replace')}
            result['pdf_attempts'].append(rec)
            if b.startswith(b'%PDF') and pdf is None:
                pdf=b; pdf_url=final
        except Exception as e:
            result['pdf_attempts'].append({'url':u,'ok':False,'error':f'{type(e).__name__}: {e}'})

    if pdf is None:
        result['pdf_recovered']=False
    else:
        result['pdf_recovered']=True; result['pdf_url_used']=pdf_url; result['pdf_sha256']=sha(pdf); result['pdf_bytes']=len(pdf)
        p=Path('/tmp/broeils1992.pdf'); p.write_bytes(pdf)
        # Text extraction is used only to locate target/table/method pages. Figure values are not digitized here.
        cp=subprocess.run(['pdftotext','-layout',str(p),'/tmp/broeils1992.txt'],capture_output=True,text=True)
        result['pdftotext_returncode']=cp.returncode; result['pdftotext_stderr']=cp.stderr[:3000]
        if Path('/tmp/broeils1992.txt').exists():
            txt=Path('/tmp/broeils1992.txt').read_text(errors='replace'); lines=txt.splitlines()
            result['text_chars']=len(txt); result['text_lines']=len(lines)
            result['target_contexts']={t:contexts(lines,t) for t in TARGETS}
            patterns={
              'surface_density':r'surface\s+density|surface-density|Sigma.?HI|H\s*I\s+surface',
              'radial_profile':r'radial.*profile|profile.*radial|radial.*surface',
              'table':r'\btable\b',
              'electronic':r'electronic|machine.readable|tabulat',
              'helium':r'helium|1\.33|1\.4',
              'strip_integral':r'strip\s+integral|deproject',
            }
            result['method_hits']={}
            for key,pat in patterns.items():
                rx=re.compile(pat,re.I); hits=[]
                for i,l in enumerate(lines):
                    if rx.search(l):
                        lo=max(0,i-3); hi=min(len(lines),i+4)
                        hits.append({'line':i+1,'context':[{'line':j+1,'text':lines[j][:1000]} for j in range(lo,hi)]})
                        if len(hits)>=150: break
                result['method_hits'][key]=hits

    out=Path('validation/stationary/br92_groningen_thesis_audit_v1.json'); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({
      'status':result['status'],'landing':result.get('landing'),'pdf_recovered':result.get('pdf_recovered'),
      'pdf_attempts':result.get('pdf_attempts'),
      'target_hit_counts':{k:len(v) for k,v in result.get('target_contexts',{}).items()},
      'method_hit_counts':{k:len(v) for k,v in result.get('method_hits',{}).items()},
    },indent=2))

if __name__=='__main__': main()
