#!/usr/bin/env python3
"""Crossmatch the official Bluedisk H I profile archive against frozen SPARC.

Sources:
  Bluedisk overview/profile archive:
    https://wwwmpa.mpa-garching.mpg.de/GASS/Bluedisk/Data/HI/
  SPARC 175-galaxy coordinate catalog:
    VizieR J/AJ/152/157/table1

This script first establishes identity by sky position. It writes an audit
product only; it does not promote any Bluedisk radial profile unless the
coordinate match is unambiguous and the matched SPARC object belongs to the
frozen 149-galaxy Paper I sample.
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://wwwmpa.mpa-garching.mpg.de/GASS/Bluedisk/Data/HI/"
VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
SPARC_CAT = "J/AJ/152/157/table1"
MAX_SEP_ARCSEC = 15.0


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "PersistenceFrameworkPaperI/1.0"})
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="strict")


def compact(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", s or "").upper()


def parse_bluedisk_overview(text: str) -> list[dict[str, str]]:
    toks = text.split()
    # Fixed-width whitespace table: 22 columns, with first row being the header.
    # Header includes tokens like 'D_A/Mpc'; data rows have numeric/string values.
    header = toks[:22]
    body = toks[22:]
    if len(body) % 22:
        raise RuntimeError(f"Bluedisk overview token count not divisible by 22: {len(body)}")
    rows=[]
    for i in range(0,len(body),22):
        vals=body[i:i+22]
        rows.append(dict(zip(header,vals)))
    if len(rows) != 50:
        raise RuntimeError(f"Expected 50 Bluedisk overview rows, got {len(rows)}")
    return rows


def parse_asu(text: str) -> list[dict[str,str]]:
    lines=text.splitlines(); header=None; start=None
    for i,line in enumerate(lines):
        if not line or line.startswith('#'): continue
        cols=line.split('\t')
        if 'Name' in cols and '_RA' in cols and '_DE' in cols:
            header=cols; start=i+1; break
    if header is None: raise RuntimeError('SPARC VizieR header not found')
    out=[]
    for line in lines[start:]:
        if not line or line.startswith('#'): continue
        cols=line.split('\t')
        if len(cols)!=len(header): continue
        if all((not c) or set(c)<={'-'} for c in cols): continue
        r=dict(zip(header,cols))
        try: float(r['_RA']); float(r['_DE'])
        except Exception: continue
        out.append({k:v.strip() for k,v in r.items()})
    if len(out) < 170:
        raise RuntimeError(f"Expected ~175 SPARC coordinate rows, got {len(out)}")
    return out


def sep_arcsec(ra1,dec1,ra2,dec2):
    r1,r2=map(math.radians,(ra1,ra2)); d1,d2=map(math.radians,(dec1,dec2))
    x=math.sin((d2-d1)/2)**2 + math.cos(d1)*math.cos(d2)*math.sin((r2-r1)/2)**2
    return math.degrees(2*math.asin(min(1,math.sqrt(x))))*3600


def load_frozen(path: Path) -> dict[str,str]:
    with path.open(newline='',encoding='utf-8-sig') as fh:
        return {r['galaxy']:r['stationary_role'] for r in csv.DictReader(fh)}


def main():
    frozen=load_frozen(Path('validation/stationary/stationary_split_v1.csv'))
    bd=parse_bluedisk_overview(fetch(BASE+'overview.txt'))
    q=urlencode({'-source':SPARC_CAT,'-out':'Name,_RA,_DE','-out.max':'1000'})
    sp=parse_asu(fetch(VIZIER+'?'+q))

    matches=[]
    for b in bd:
        if b.get('date') == 'notobserved':
            continue
        bra=float(b['ra']); bdec=float(b['dec'])
        ranked=sorted((sep_arcsec(bra,bdec,float(s['_RA']),float(s['_DE'])),s) for s in sp)
        best_sep,best=ranked[0]
        second_sep=ranked[1][0]
        if best_sep <= MAX_SEP_ARCSEC:
            name=best['Name']
            # Use exact SPARC name; CDS table is authoritative for this identity.
            role=frozen.get(name,'not_in_frozen_149')
            matches.append({
                'bluedisk_id':b['ID'],
                'bluedisk_ra_deg':b['ra'],
                'bluedisk_dec_deg':b['dec'],
                'bluedisk_DA_mpc':b['D_A/Mpc'],
                'sparc_name':name,
                'stationary_role':role,
                'separation_arcsec':f'{best_sep:.4f}',
                'second_nearest_separation_arcsec':f'{second_sep:.4f}',
                'unambiguous_15arcsec_match':'1' if second_sep > MAX_SEP_ARCSEC else '0',
            })

    out=Path('data/stationary/source_reconstruction/bluedisk_sparc_overlap_audit_v1.csv')
    out.parent.mkdir(parents=True,exist_ok=True)
    fields=['bluedisk_id','bluedisk_ra_deg','bluedisk_dec_deg','bluedisk_DA_mpc','sparc_name','stationary_role','separation_arcsec','second_nearest_separation_arcsec','unambiguous_15arcsec_match']
    with out.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(matches)

    frozen_matches=[m for m in matches if m['stationary_role'] in {'calibration','blind'}]
    summary={
        'status':'BLUEDISK_SPARC_COORDINATE_CROSSMATCH_COMPLETE',
        'n_bluedisk_overview':len(bd),
        'n_bluedisk_observed':sum(r.get('date')!='notobserved' for r in bd),
        'n_sparc_coordinate_rows':len(sp),
        'match_radius_arcsec':MAX_SEP_ARCSEC,
        'n_sparc_matches_within_radius':len(matches),
        'n_frozen_149_matches':len(frozen_matches),
        'frozen_matches':frozen_matches,
        'boundary':'No H I profile row is promoted unless coordinate identity is unambiguous and frozen membership is confirmed. No persistence quantity evaluated.'
    }
    spath=Path('validation/stationary/bluedisk_sparc_overlap_audit_v1_summary.json')
    spath.parent.mkdir(parents=True,exist_ok=True)
    spath.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
