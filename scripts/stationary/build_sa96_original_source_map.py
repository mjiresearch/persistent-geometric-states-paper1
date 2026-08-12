#!/usr/bin/env python3
"""Build a per-galaxy original-source map for the frozen SPARC Sa96 family.

Sanders (1996) Table 1 contains numeric reference codes for its input data and
immediately follows the table with the numbered reference legend. This script
extracts those two structures directly from the public arXiv TeX source.
"""
from __future__ import annotations

import csv, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URL='https://export.arxiv.org/e-print/astro-ph/9606089'
UA='PersistenceFrameworkPaperI/1.0'
TARGET_PATTERNS={
 'NGC0055':r'NGC\s+55\b','NGC0247':r'NGC\s+247\b','NGC0300':r'NGC\s+300\b',
 'NGC0801':r'NGC\s+801\b','NGC1003':r'NGC\s+1003\b','NGC2683':r'NGC\s+2683\b',
 'NGC2998':r'NGC\s+2998\b','NGC5033':r'NGC\s+5033\b','NGC5371':r'NGC\s+5371\b',
 'NGC5585':r'NGC\s+5585\b','NGC5907':r'NGC\s+5907\b','NGC6674':r'NGC\s+6674\b',
 'UGC02885':r'UGC\s+2885\b',
}


def fetch_tex():
    req=Request(URL,headers={'User-Agent':UA})
    raw=urlopen(req,timeout=90).read()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    return tf.extractfile('rotcur_pp.tex').read().decode('latin-1','replace')


def clean_tex(s):
    s=s.replace('\\&','&').replace('\\etal','et al.').replace('\\ ',' ')
    s=re.sub(r'\\[A-Za-z]+\s*',' ',s)
    s=re.sub(r'[{}$]','',s)
    return re.sub(r'\s+',' ',s).strip(' ;,.')


def main():
    tex=fetch_tex(); lines=tex.splitlines()

    # Extract target table rows and their final numeric reference field.
    target_refs={}
    target_raw={}
    for target,pat in TARGET_PATTERNS.items():
        rx=re.compile(pat,re.I)
        candidates=[]
        for i,line in enumerate(lines):
            if rx.search(line) and '&' in line and re.search(r'&\s*[0-9]+(?:\s*,\s*[0-9]+)*\s*\\\\',line):
                m=re.search(r'&\s*([0-9]+(?:\s*,\s*[0-9]+)*)\s*\\\\',line)
                if m: candidates.append((i+1,line,m.group(1)))
        # Table 1 is the row with the most ampersands / full observational metadata.
        if candidates:
            candidates.sort(key=lambda x:x[1].count('&'),reverse=True)
            ln,line,field=candidates[0]
            codes=[int(x.strip()) for x in field.split(',')]
            target_refs[target]=codes
            target_raw[target]={'line':ln,'text':line}

    # Locate the numbered reference legend immediately following Table 1.
    # Use the block beginning after the table rows and containing refs 1..25.
    legend_lines=[]
    for i,line in enumerate(lines):
        if re.search(r'\b12,\s*Carignan',line):
            lo=max(0,i-4); hi=min(len(lines),i+6)
            legend_lines=lines[lo:hi]
            break
    legend_text=' '.join(legend_lines)
    legend_text=legend_text.replace('\\&','&').replace('\\etal','et al.')
    # Strip TeX linebreaks/commands that interfere with semicolon-separated citations.
    legend_text=re.sub(r'\\\\',' ',legend_text)
    legend_text=re.sub(r'\\[A-Za-z]+',' ',legend_text)
    legend_text=re.sub(r'\s+',' ',legend_text)
    refs={}
    # Entries are separated by semicolon; final entry may terminate without one.
    for m in re.finditer(r'(\d{1,2})\s*,\s*(.*?)(?=;\s*\d{1,2}\s*,|$)',legend_text):
        refs[int(m.group(1))]=clean_tex(m.group(2))

    # If the first/last lines cut an entry, widen to the explicit source lines 1023-1031.
    if len(refs)<20:
        block=' '.join(lines[1021:1032]) if len(lines)>1032 else legend_text
        block=block.replace('\\&','&').replace('\\etal','et al.')
        block=re.sub(r'\\\\',' ',block); block=re.sub(r'\\[A-Za-z]+',' ',block); block=re.sub(r'\s+',' ',block)
        refs={}
        for m in re.finditer(r'(\d{1,2})\s*,\s*(.*?)(?=;\s*\d{1,2}\s*,|$)',block):
            refs[int(m.group(1))]=clean_tex(m.group(2))
        legend_text=block

    rows=[]
    for target in TARGET_PATTERNS:
        codes=target_refs.get(target,[])
        for code in codes:
            rows.append({
              'galaxy':target,
              'sanders1996_ref_number':code,
              'sanders1996_original_source_label':refs.get(code,''),
              'mapping_status':'mapped' if code in refs else 'legend_parse_pending',
            })
        if not codes:
            rows.append({'galaxy':target,'sanders1996_ref_number':'','sanders1996_original_source_label':'','mapping_status':'table_row_not_parsed'})

    out=Path('data/stationary/source_reconstruction/sa96_original_source_map_v1.csv'); out.parent.mkdir(parents=True,exist_ok=True)
    fields=['galaxy','sanders1996_ref_number','sanders1996_original_source_label','mapping_status']
    with out.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    summary={
      'status':'SA96_ORIGINAL_SOURCE_MAP_BUILT',
      'n_target_galaxies':len(TARGET_PATTERNS),
      'n_targets_with_table_refs':len(target_refs),
      'n_numbered_legend_entries_parsed':len(refs),
      'legend_entries':{str(k):v for k,v in sorted(refs.items())},
      'target_table_rows':target_raw,
      'n_galaxy_source_rows':len(rows),
      'unmapped_codes':sorted({int(r['sanders1996_ref_number']) for r in rows if r['sanders1996_ref_number']!='' and r['mapping_status']!='mapped'}),
      'boundary':'Sanders 1996 is downstream. These labels identify the papers Sanders cites for the input observational data; each resulting original paper must still be audited for direct Sigma_HI profile availability.'
    }
    sp=Path('validation/stationary/sa96_original_source_map_v1_summary.json'); sp.parent.mkdir(parents=True,exist_ok=True)
    sp.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
