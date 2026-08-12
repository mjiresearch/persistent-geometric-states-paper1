#!/usr/bin/env python3
"""Audit Hallenbeck et al. 2014 (Ha14) public source assets for exact radial HI profiles.

Targets: UGC09037 and UGC12506. Ha14 is the resolved VLA observing paper.
Promotion is allowed only for source-native radius-vs-Sigma_HI rows or clearly
recoverable vector radial-profile geometry. No OCR, raster digitization,
map-to-profile reconstruction, normalization, persistence fitting, or blind
outcome inspection.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

OUT=Path('validation/stationary/ha14_hi_profile_source_asset_audit_v1.json')
URLS=['https://arxiv.org/e-print/1407.1744','https://export.arxiv.org/e-print/1407.1744']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
PROFILE_PATS=[r'H\s*I\s+surface\s+density',r'H\\?i\s+surface\s+density',r'surface\s+density.*radius',r'deprojected.*surface\s+density',r'radial.*surface\s+density']

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
    with urllib.request.urlopen(req,timeout=180) as h:return h.read(),h.geturl(),h.headers.get('Content-Type','')

def tok(b,t):return len(re.findall(rb'(?<![A-Za-z])'+re.escape(t)+rb'(?![A-Za-z])',b))

def psinfo(name,b):
    txt=b.decode('latin-1','replace')
    strings=[s for s in re.findall(r'\(([^()]*)\)',txt) if any(k in s.lower() for k in ['ugc','radius','surface','density','hi','h i','m_','pc'])]
    return {'name':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),
            'image_ops':tok(b,b'image'),'colorimage_ops':tok(b,b'colorimage'),'imagemask_ops':tok(b,b'imagemask'),
            'moveto_ops':tok(b,b'moveto'),'lineto_ops':tok(b,b'lineto'),'curveto_ops':tok(b,b'curveto'),'stroke_ops':tok(b,b'stroke'),
            'useful_strings':strings[:100],
            'bounding_box_lines':[ln for ln in txt.splitlines() if 'BoundingBox' in ln][:10]}

def context(lines,i,r=8):return '\n'.join(lines[max(0,i-r):min(len(lines),i+r+1)])[:12000]

def main():
    attempts=[];raw=None
    for u in URLS:
        rec={'url':u}
        try:
            raw,final,ct=fetch(u);rec.update({'status':'fetched','final_url':final,'content_type':ct,'bytes':len(raw)});attempts.append(rec);break
        except Exception as exc:
            rec.update({'status':'error','error':f'{type(exc).__name__}: {exc}'});attempts.append(rec)
    if raw is None: raise SystemExit('Ha14 source fetch failed')
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    members=[];texts=[];graphics=[];data_assets=[];numeric=[]
    for m in tf.getmembers():
        if not m.isfile():continue
        b=tf.extractfile(m).read();suf=Path(m.name).suffix.lower();members.append({'name':m.name,'bytes':m.size,'suffix':suf})
        if suf in {'.tex','.txt','.bbl','.bib','.dat','.tbl','.tab','.csv'}:texts.append((m.name,b.decode('latin-1','replace')))
        if suf in {'.ps','.eps'}:graphics.append(psinfo(m.name,b))
        if suf in {'.dat','.tbl','.tab','.csv','.fits','.fit','.fts'}:data_assets.append({'name':m.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
        if suf in {'.dat','.tbl','.tab','.csv','.txt'}:
            t=b.decode('latin-1','replace')
            if re.search(r'9037|12506',t) and re.search(r'surface|density|H.?I',t,re.I):
                nums=re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?',t)
                numeric.append({'name':m.name,'numeric_tokens':len(nums),'excerpt':t[:12000]})
    target_hits=[];profile_hits=[];figure_refs=[]
    for fn,text in texts:
        lines=text.splitlines()
        for i,line in enumerate(lines):
            if re.search(r'UGC\s*9037|UGC\s*12506|UGC\\?,?\s*9037|UGC\\?,?\s*12506',line,re.I):
                target_hits.append({'file':fn,'line':i+1,'text':line[:2500],'context':context(lines,i)})
            if any(re.search(p,line,re.I) for p in PROFILE_PATS):
                profile_hits.append({'file':fn,'line':i+1,'text':line[:2500],'context':context(lines,i)})
            if re.search(r'includegraphics|epsfig|psfig',line,re.I):
                figure_refs.append({'file':fn,'line':i+1,'text':line[:2500],'context':context(lines,i,5)})
    # identify graphics whose labels make them plausible radial HI profile figures
    profile_graphics=[]
    for g in graphics:
        s=' '.join(g['useful_strings']).lower()
        if ('radius' in s and ('surface' in s or 'density' in s or 'ugc 9037' in s or 'ugc 12506' in s)):
            profile_graphics.append(g)
    out={'status':'HA14_HI_PROFILE_SOURCE_ASSET_AUDIT_COMPLETE','source':'Hallenbeck et al. 2014 AJ 148 69','arxiv':'1407.1744',
         'targets':['UGC09037','UGC12506'],'transport_attempts':attempts,'source_bytes':len(raw),'source_sha256':hashlib.sha256(raw).hexdigest(),
         'members':members,'data_like_assets':data_assets,'numeric_target_profile_candidates':numeric,'target_text_hits':target_hits,
         'profile_language_hits':profile_hits,'figure_refs':figure_refs,'graphics':graphics,'profile_graphics':profile_graphics,
         'promotion_rule':'Only source-native radius-versus-Sigma_HI rows or clearly isolated vector radial-profile geometry may be promoted.',
         'boundary':'Acquisition/provenance only; PostScript parsed but not executed. No OCR, raster digitization, map-to-profile reconstruction, normalization, persistence fitting, or blind-outcome inspection.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'data_assets':data_assets,'numeric_candidates':numeric,
      'profile_hits':[{'file':x['file'],'line':x['line'],'text':x['text']} for x in profile_hits],
      'profile_graphics':[{'name':g['name'],'image':g['image_ops']+g['colorimage_ops']+g['imagemask_ops'],'moveto':g['moveto_ops'],'lineto':g['lineto_ops'],'curveto':g['curveto_ops'],'stroke':g['stroke_ops'],'strings':g['useful_strings']} for g in profile_graphics]},indent=2))
if __name__=='__main__':main()
