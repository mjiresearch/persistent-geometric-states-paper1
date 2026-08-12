#!/usr/bin/env python3
"""Resolve the exact Tr09 figure/source inventory for D564-8 and D631-7.

Continuation after tr09_d5648_d6317_source_audit_v1.json. This script does not
repeat the broad audit; it resolves target-specific TeX figure blocks and
statically inventories their PostScript for evidence of a published radial H I
surface-density profile or machine-readable radial array.

PostScript is never executed or rendered. No raster digitization, OCR,
map-to-profile reconstruction, normalization, persistence fitting, or blind
outcome inspection is performed.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

ARXIV='0907.5533'
URL=f'https://arxiv.org/e-print/{ARXIV}'
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/tr09_target_figure_inventory_v1.json')
CTX=Path('validation/stationary/tr09_target_figure_inventory_context_v1.txt')
TARGETS=('D564-8','D631-7')


def fetch_source():
    req=urllib.request.Request(URL,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=180) as h:
        raw=h.read()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    return raw,tf


def get_bytes(tf,name):
    return tf.extractfile(tf.getmember(name)).read()


def figure_blocks(tex):
    # Sufficient for this manuscript: figures are not nested.
    return re.findall(r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}',tex,re.S)


def plain_caption(block):
    m=re.search(r'\\caption(?:\[[^\]]*\])?\{(.*?)\}\s*(?:\\label|\\end)',block,re.S)
    if not m:
        return ''
    s=m.group(1)
    s=re.sub(r'\\[A-Za-z@]+(?:\[[^\]]*\])?',' ',s)
    s=re.sub(r'[{}$~]',' ',s)
    return re.sub(r'\s+',' ',s).strip()


def refs(block):
    return re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',block)


def classify_ps(b):
    t=b.decode('latin-1','replace')
    strings=[]
    for li,line in enumerate(t.splitlines(),1):
        for s in re.findall(r'\((?:\\.|[^()])*\)',line):
            q=s[1:-1]
            if re.search(r'(?i)radius|surface|density|column|H.?I|N.?HI|M.?sun|pc|arcsec|kpc|velocity|inclination|position angle',q):
                strings.append({'line':li,'text':q[:300]})
    # Search literal comments/labels too, excluding prolog boilerplate.
    keyword_lines=[]
    for li,line in enumerate(t.splitlines(),1):
        if re.search(r'(?i)surface.?density|column.?density|sigma.?hi|n.?hi|radius.*(?:kpc|arcsec)',line):
            keyword_lines.append({'line':li,'text':line[:500]})
    creators=[]
    for line in t.splitlines()[:80]:
        if line.startswith(('%%Creator','%%Title','%%BoundingBox')):
            creators.append(line)
    return {
        'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),
        'header_lines':creators,
        'image_ops':len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',t)),
        'colorimage_ops':len(re.findall(r'(?<![A-Za-z])colorimage(?![A-Za-z])',t)),
        'moveto_ops':len(re.findall(r'(?<![A-Za-z])moveto(?![A-Za-z])',t)),
        'lineto_ops':len(re.findall(r'(?<![A-Za-z])lineto(?![A-Za-z])',t)),
        'rlineto_ops':len(re.findall(r'(?<![A-Za-z])rlineto(?![A-Za-z])',t)),
        'fill_ops':len(re.findall(r'(?<![A-Za-z])fill(?![A-Za-z])',t)),
        'stroke_ops':len(re.findall(r'(?<![A-Za-z])stroke(?![A-Za-z])',t)),
        'relevant_strings':strings[:200],
        'keyword_lines':keyword_lines[:100],
        'has_radial_hi_density_label':bool(strings or keyword_lines),
    }


def table_blocks(tex):
    return re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}',tex,re.S)


def main():
    raw,tf=fetch_source()
    tex=get_bytes(tf,'11136.tex').decode('latin-1','replace')
    names={m.name for m in tf.getmembers() if m.isfile()}
    figs=[]
    for i,b in enumerate(figure_blocks(tex),1):
        cap=plain_caption(b)
        rr=refs(b)
        target=[g for g in TARGETS if g.lower() in b.lower()]
        if not target:
            continue
        assets=[]
        for r in rr:
            name=r if r in names else next((n for n in names if Path(n).stem==Path(r).stem),None)
            rec={'graphic_ref':r,'resolved_name':name}
            if name:
                data=get_bytes(tf,name)
                if name.lower().endswith(('.ps','.eps')):
                    rec.update(classify_ps(data))
                else:
                    rec.update({'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'type':'non_postscript'})
            assets.append(rec)
        figs.append({'sequence':i,'targets':target,'caption':cap,'graphic_refs':rr,'assets':assets,'tex_block':b})

    # Exact TeX mentions of radial/surface/column profile language.
    tex_lines=tex.splitlines()
    profile_context=[]
    patt=re.compile(r'(?i)surface.?density|column.?density|radial.*profile|profile.*radial|azimuthally.*averag|H.?I.*profile|profile.*H.?I')
    for i,line in enumerate(tex_lines):
        if patt.search(line):
            lo=max(0,i-5);hi=min(len(tex_lines),i+6)
            hood='\n'.join(tex_lines[lo:hi])
            profile_context.append({'line':i+1,'targets_nearby':[g for g in TARGETS if g.lower() in hood.lower()],
                                    'context':'\n'.join(f'{j+1}: {tex_lines[j]}' for j in range(lo,hi))})

    # Check all TeX tables for target-specific radius-by-density style rows.
    target_tables=[]
    for i,b in enumerate(table_blocks(tex),1):
        if any(g.lower() in b.lower() for g in TARGETS):
            radial_header=bool(re.search(r'(?i)radius|surface.?density|column.?density|sigma|N_?\{?\\rm HI',b))
            target_tables.append({'sequence':i,'contains_targets':[g for g in TARGETS if g.lower() in b.lower()],
                                  'radial_or_density_header':radial_header,
                                  'preview':re.sub(r'\s+',' ',b)[:3000]})

    # Appendix summary-panel captions establish product type; collect all target mentions near appendix.
    appendix=[]
    for g in TARGETS:
        for i,line in enumerate(tex_lines):
            if g.lower() in line.lower() and i>900:
                lo=max(0,i-8);hi=min(len(tex_lines),i+9)
                appendix.append({'target':g,'line':i+1,'context':'\n'.join(f'{j+1}: {tex_lines[j]}' for j in range(lo,hi))})

    radial_assets=[]
    for f in figs:
        for a in f['assets']:
            if a.get('has_radial_hi_density_label'):
                radial_assets.append({'targets':f['targets'],'caption':f['caption'],'asset':a['resolved_name'],
                                      'strings':a.get('relevant_strings',[]),'keyword_lines':a.get('keyword_lines',[])})

    exact_table_candidate=any(t['radial_or_density_header'] for t in target_tables)
    status=('TR09_EXACT_RADIAL_HI_SOURCE_CANDIDATE_FOUND' if radial_assets or exact_table_candidate
            else 'TR09_NO_EXACT_RADIAL_HI_PROFILE_IN_PUBLISHED_SOURCE_PRODUCTS')
    out={
        'status':status,'arxiv':ARXIV,'source_package_sha256':hashlib.sha256(raw).hexdigest(),
        'target_figure_blocks':figs,'profile_language_contexts':profile_context,
        'target_tables':target_tables,'appendix_target_contexts':appendix,
        'radial_hi_density_assets':radial_assets,'exact_table_candidate':exact_table_candidate,
        'interpretation':(
            'Target source products are observing/global-parameter tables, tilted-ring kinematic figures, and appendix moment/PV/channel-map summary panels; no published radius-by-Sigma_HI array or vector radial H I surface-density profile was identified.'
            if status.endswith('PUBLISHED_SOURCE_PRODUCTS') else
            'At least one target source asset/table requires a narrower native-data audit before disposition.'),
        'next_gate':('write_Tr09_no_exact_profile_disposition_and_rerank' if status.endswith('PUBLISHED_SOURCE_PRODUCTS')
                     else 'audit_only_the_flagged_exact_candidate'),
        'boundary':'Static source/acquisition audit only; PostScript not executed or rendered; no OCR, raster digitization, map-to-profile reconstruction, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
    ctx=[]
    for f in figs:
        ctx.append('===== TARGET FIGURE =====\nTargets: '+','.join(f['targets'])+'\nCaption: '+f['caption']+'\nRefs: '+','.join(f['graphic_refs'])+'\n'+f['tex_block'])
    for p in profile_context:
        ctx.append(f"===== PROFILE LANGUAGE line {p['line']} =====\n{p['context']}")
    for a in appendix:
        ctx.append(f"===== APPENDIX {a['target']} line {a['line']} =====\n{a['context']}")
    CTX.write_text('\n\n'.join(ctx)+'\n')
    print(json.dumps({'status':status,
                      'figures':[{'targets':f['targets'],'caption':f['caption'],'refs':f['graphic_refs'],
                                  'assets':[{'name':a.get('resolved_name'),'image_ops':a.get('image_ops'),'colorimage_ops':a.get('colorimage_ops'),'path_ops':(a.get('moveto_ops',0)+a.get('lineto_ops',0)+a.get('rlineto_ops',0)),'radial_label':a.get('has_radial_hi_density_label')} for a in f['assets']]} for f in figs],
                      'n_profile_language_contexts':len(profile_context),'radial_assets':radial_assets,
                      'target_tables':[{'targets':t['contains_targets'],'radial_header':t['radial_or_density_header']} for t in target_tables],
                      'next_gate':out['next_gate']},indent=2))

if __name__=='__main__':main()
