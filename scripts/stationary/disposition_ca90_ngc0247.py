#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
AUD=Path('validation/stationary/ca90_ngc0247_bibliography_hi_profile_audit_v1.json')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
 a=json.loads(AUD.read_text(encoding='utf-8'))
 if a.get('status')!='CA90_NGC0247_BIBLIOGRAPHY_HI_PROFILE_AUDIT_COMPLETE':raise RuntimeError('Ca90 audit status changed')
 route=a.get('lvhis_public_fits_route',{})
 if route.get('candidate_recoverable_snapshots'):raise RuntimeError('Recoverable LVHIS FITS appeared; do not disposition')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={'sparc_ref_id':'Ca90','queue_status':'deferred_exact_profile_route_exhausted','disposition':'NGC0247_direct_CP90b_Fig4_raw_HI_profile_scan_only_LVHIS_published_FITS_route_currently_unrecoverable_VLA_ANGST_incomplete','validation_artifact':str(AUD),'reopen_rule':'reopen_for_machine_readable_CP90b_profile_or_recoverable_LVHIS_science_ready_FITS_or_other_complete_public_HI_map_product_under_frozen_reconstruction_protocol','notes':'NGC0247: SPARC Ca90 bibliography points to AJ100,394 (NGC7793); direct NGC247 paper is Carignan & Puche 1990b AJ100,641. Figure 4 is the raw radial H I distribution and helium is applied later. Public article is scan-only. LVHIS publishes a complete later ATCA mosaic (F_HI=662.5 Jy km/s, R_HI=1544 arcsec) but the bounded live/archive FITS route returned no recoverable science-ready file. VLA-ANGST is not certified because LVHIS reports its single pointing recovers only 382.6 Jy km/s and misses substantial H I.'}
 if 'Ca90' in by:by['Ca90'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id'])
 with DISP.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 print(json.dumps({'status':'CA90_NGC0247_DISPOSITIONED','validation':str(AUD)}))
if __name__=='__main__':main()
