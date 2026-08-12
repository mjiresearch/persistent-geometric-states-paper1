#!/usr/bin/env python3
"""Resolve VB99 / UGC00128 and redirect it to the already-audited VH93 H I source.

SPARC/Lelli assigns UGC00128 both VB99 and VH93. VB99 is Verheijen & de Blok
(1999), a short rotation-curve decomposition/comparison of NGC2403 and UGC128,
not a new 21-cm observing paper. A closely related de Blok & McGaugh (1996)
source explicitly states that the UGC128 data are from van der Hulst et al.
(1993). The repository has already audited that VH93 direct radial H I profile
route and found the current public profile to be figure-scan only with no exact
numeric/native-vector recovery.

This script preserves that provenance chain and prevents VB99 from reopening the
same exhausted VH93 mechanism merely because SPARC lists both references.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
VH93=Path('validation/stationary/VH93_PUBLIC_PROFILE_ROUTE_AUDIT_V1.md')
OUT=Path('validation/stationary/vb99_ugc128_provenance_redirect_v1.json')
CHECK=Path('validation/stationary/CHECKPOINT_VB99_REDIRECT_TO_VH93.md')
ARXIV_URLS=['https://arxiv.org/e-print/astro-ph/9607042','https://export.arxiv.org/e-print/astro-ph/9607042']


def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def sha(b):return hashlib.sha256(b).hexdigest()

def fetch_precursor():
    errs=[]
    for u in ARXIV_URLS:
        try:
            with urlopen(Request(u,headers={'User-Agent':'PaperI-VB99-provenance/1.0'}),timeout=60) as r:
                return r.read(),r.geturl()
        except Exception as e:errs.append([u,repr(e)])
    raise RuntimeError(f'Could not fetch public precursor source: {errs}')

def unpack_text(payload):
    texts=[]
    try:
        with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
            for m in tf.getmembers():
                if m.isfile() and m.name.lower().endswith(('.tex','.ltx','.txt')):
                    f=tf.extractfile(m)
                    if f:texts.append((m.name,f.read().decode('latin-1',errors='replace')))
    except tarfile.ReadError:
        texts=[('submission_source',payload.decode('latin-1',errors='replace'))]
    return texts

def main():
    refs=read_csv(REF)
    vb=[r for r in refs if r.get('galaxy')=='UGC00128' and r.get('sparc_ref_id')=='VB99']
    vh=[r for r in refs if r.get('galaxy')=='UGC00128' and r.get('sparc_ref_id')=='VH93']
    if len(vb)!=1 or len(vh)!=1 or vb[0].get('stationary_role')!='calibration' or vh[0].get('stationary_role')!='calibration':
        raise RuntimeError(f'UGC00128 dual-reference mapping changed: VB99={vb}, VH93={vh}')
    if not VH93.exists():raise RuntimeError('Existing VH93 audit missing; restore it rather than restarting source search')
    vtxt=VH93.read_text(encoding='utf-8')
    required=['UGC00128','Figure 2','radial H I surface-density','figure-scan','No raster digitization']
    missing=[s for s in required if s not in vtxt]
    if missing:raise RuntimeError(f'VH93 audit no longer contains expected locked evidence: {missing}')

    payload,url=fetch_precursor();texts=unpack_text(payload)
    hits=[]
    patterns=[
        re.compile(r'data.{0,100}UGC\s*128.{0,180}van\s+der\s+Hulst.{0,120}1993',re.I|re.S),
        re.compile(r'UGC\s*128.{0,180}van\s+der\s+Hulst.{0,120}1993',re.I|re.S),
    ]
    for n,t in texts:
        for pat in patterns:
            for m in pat.finditer(t):
                lo=max(0,m.start()-250);hi=min(len(t),m.end()+250)
                hits.append({'file':n,'match':re.sub(r'\s+',' ',t[lo:hi]).strip()})
    # Deduplicate contexts.
    uniq=[];seen=set()
    for h in hits:
        key=(h['file'],h['match'])
        if key not in seen:seen.add(key);uniq.append(h)
    if not uniq:
        raise RuntimeError('Public de Blok & McGaugh 1996 source did not verify UGC128 -> van der Hulst et al. 1993 provenance')

    audit={
        'status':'VB99_UGC00128_REDIRECT_TO_VH93_CONFIRMED',
        'galaxy':'UGC00128','stationary_role':'calibration','sparc_ref_id':'VB99',
        'vb99_resolution':{
            'reference':'Verheijen & de Blok 1999, The HSB/LSB Galaxies NGC 2403 and UGC 128',
            'publication':'Astrophysics and Space Science 269, 673-674',
            'doi':'10.1023/A:1017015229229',
            'scope':'two-page rotation-curve decomposition/comparison; not treated as an independent 21-cm observing source'
        },
        'sparc_dual_reference':{
            'VB99':vb[0],
            'VH93':vh[0],
            'interpretation':'SPARC/Lelli lists both VB99 and VH93 for the same frozen UGC00128 calibration target.'
        },
        'upstream_provenance_check':{
            'source':'de Blok & McGaugh 1996, Does low surface brightness mean low surface density?, arXiv:astro-ph/9607042',
            'source_url':url,'source_sha256':sha(payload),'matching_contexts':uniq[:10],
            'conclusion':'The related UGC128 comparison literature explicitly attributes UGC128 data to van der Hulst et al. 1993.'
        },
        'existing_vh93_state':{
            'artifact':str(VH93),
            'conclusion':'VH93 directly publishes the UGC00128 radial H I surface-density profile in Figure 2, but the currently recovered public profile values are figure-scan only; no exact numerical/native-vector route was found.'
        },
        'decision':'Redirect VB99 to existing VH93 source state; do not repeat VH93 public scan/table searches under the VB99 label.',
        'reopen_rule':'reopen_only_for_a_genuinely_new_machine_readable_radial_table_exact_native_vector_direct_profile_array_or_documented_independent_HI_source_for_UGC00128',
        'boundary':'No raster digitization, map/cube reconstruction, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')

    rows=read_csv(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
    new={
        'sparc_ref_id':'VB99','queue_status':'redirect_existing_source_family',
        'disposition':'downstream_UGC128_rotation_curve_decomposition_uses_same_van_der_Hulst1993_HI_source_already_audited_as_VH93',
        'validation_artifact':str(OUT),
        'reopen_rule':audit['reopen_rule'],
        'notes':(
            'UGC00128/UGC128 (calibration). VB99 resolved as Verheijen & de Blok 1999, a two-page NGC2403/UGC128 rotation-curve decomposition/comparison. '
            'SPARC/Lelli separately lists VH93 for the same galaxy, and the related de Blok & McGaugh 1996 comparison source explicitly attributes UGC128 data to van der Hulst et al. 1993. '
            'The existing VH93 audit already establishes a direct radial H I surface-density profile in Figure 2 but only scan-level public values with no exact numeric/native-vector route. '
            'Do not repeat the exhausted VH93 mechanism under the VB99 label. No raster digitization.'
        )
    }
    if 'VB99' in by:by['VB99'].update(new)
    else:rows.append(new)
    rows.sort(key=lambda r:r['sparc_ref_id']);write_csv(DISP,rows,fields)

    CHECK.write_text(
        '# VB99 / UGC00128 stationary H I checkpoint\n\n'
        'Status: **DOWNSTREAM ROTATION-CURVE COMPARISON REDIRECTED TO EXISTING VH93 H I SOURCE STATE**\n\n'
        '- Frozen target: UGC00128 / UGC128 — calibration.\n'
        '- SPARC/Lelli lists both `VB99` and `VH93` for this galaxy.\n'
        '- `VB99` resolves to Verheijen & de Blok (1999), a two-page NGC2403/UGC128 rotation-curve decomposition/comparison.\n'
        '- Independent provenance check in de Blok & McGaugh (1996) explicitly attributes the UGC128 data to van der Hulst et al. (1993).\n'
        '- Existing `VH93` audit: direct radial H I profile is Figure 2, but current public profile values are scan-only with no exact numeric/native-vector route.\n'
        f'- Durable provenance audit: `{OUT}`.\n'
        f'- Existing source-route authority: `{VH93}`.\n'
        '- No raster digitization, map reconstruction, persistence fitting, or blind-outcome inspection.\n'
        '- `L_A` and `C_A` remain locked.\n\n'
        '## Resume point\nRerank and continue the next actionable Lelli family. Do not reopen VH93 merely because VB99 appeared separately.\n',encoding='utf-8')
    print(json.dumps({'status':audit['status'],'provenance_contexts':len(uniq),'checkpoint':str(CHECK)},indent=2))

if __name__=='__main__':main()
