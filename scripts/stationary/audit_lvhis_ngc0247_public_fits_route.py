#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

OUT = Path('validation/stationary/lvhis_ngc0247_public_fits_route_v1.json')
TXT = Path('validation/stationary/lvhis_ngc0247_public_fits_route_v1.txt')
UA = 'PaperI-NGC247-LVHIS-route-audit/1.0'
BASE = 'www.atnf.csiro.au/research/LVHIS/'

def fetch(url, timeout=45):
    try:
        req=Request(url,headers={'User-Agent':UA})
        with urlopen(req,timeout=timeout) as r:
            b=r.read()
            return {'url':url,'final_url':r.geturl(),'status':getattr(r,'status',None),
                    'content_type':r.headers.get('Content-Type',''),'bytes':len(b),
                    'sha256':hashlib.sha256(b).hexdigest(),'body':b}
    except Exception as e:
        return {'url':url,'error':repr(e)}

def cdx(pattern):
    q=('https://web.archive.org/cdx/search/cdx?url='+quote(pattern,safe='*/:')+
       '&output=json&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype,statuscode,length&limit=5000')
    x=fetch(q,60)
    rows=[]
    if 'body' in x:
        try:
            raw=json.loads(x['body'].decode('utf-8','replace'))
            if raw and isinstance(raw,list):
                for r in raw[1:]:
                    if len(r)>=5: rows.append(dict(zip(raw[0],r)))
        except Exception as e: x['parse_error']=repr(e)
    x.pop('body',None)
    return x,rows

def main():
    result={'status':'LVHIS_NGC0247_PUBLIC_FITS_ROUTE_AUDITED','live':[],'cdx_queries':[],'matches':[],'snapshot_tests':[]}
    for u in ['https://www.atnf.csiro.au/research/LVHIS/','http://www.atnf.csiro.au/research/LVHIS/']:
        x=fetch(u); x.pop('body',None); result['live'].append(x)
    patterns=[BASE+'*NGC247*',BASE+'*ngc247*',BASE+'*J0047*',BASE+'*j0047*',BASE+'*0047*']
    seen=set()
    for p in patterns:
        meta,rows=cdx(p); result['cdx_queries'].append({'pattern':p,'meta':meta,'n_rows':len(rows)})
        for r in rows:
            orig=r.get('original','')
            key=(r.get('timestamp',''),orig)
            if key in seen: continue
            seen.add(key)
            lo=orig.lower()
            score=sum(k in lo for k in ['ngc247','ngc0247','j0047','0047-20','0047_20','004720'])
            fitsish=any(k in lo for k in ['.fits','.fit','.fits.gz','.fit.gz','mom0','moment','column','nhi','hi_'])
            result['matches'].append({**r,'name_score':score,'fitsish':fitsish})
    result['matches'].sort(key=lambda r:(not r['fitsish'],-r['name_score'],r.get('original','')))
    for r in [x for x in result['matches'] if x['fitsish']][:30]:
        ts=r['timestamp']; orig=r['original']
        u=f'https://web.archive.org/web/{ts}id_/{orig}'
        x=fetch(u,60)
        body=x.pop('body',b'')
        x['magic_hex']=body[:16].hex() if body else ''
        x['looks_fits']=body.startswith(b'SIMPLE  =') or body[:2]==b'\x1f\x8b'
        x['timestamp']=ts; x['original']=orig
        result['snapshot_tests'].append(x)
    result['candidate_recoverable_snapshots']=[x for x in result['snapshot_tests'] if x.get('looks_fits') and x.get('bytes',0)>10000]
    result['boundary']='Route audit only. No radial values are extracted here.'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=[f"status={result['status']}",f"matches={len(result['matches'])}",f"recoverable={len(result['candidate_recoverable_snapshots'])}"]
    for x in result['live']: lines.append('LIVE '+json.dumps(x,sort_keys=True))
    for x in result['cdx_queries']: lines.append('CDX '+json.dumps(x,sort_keys=True))
    for x in result['matches'][:100]: lines.append('MATCH '+json.dumps(x,sort_keys=True))
    for x in result['snapshot_tests']: lines.append('TEST '+json.dumps(x,sort_keys=True))
    TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'matches':len(result['matches']),'recoverable':len(result['candidate_recoverable_snapshots']),'outputs':[str(OUT),str(TXT)]},indent=2))

if __name__=='__main__': main()
