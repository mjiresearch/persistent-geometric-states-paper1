#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
AUDIT=Path('validation/stationary/pu91_ngc0055_public_hi_route_v1.json')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_PU91_NGC0055_PUBLIC_ROUTE.md')
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
 audit=json.loads(AUDIT.read_text(encoding='utf-8'))
 if audit.get('status')!='PU91_NGC0055_PUBLIC_ROUTE_EXHAUSTED_CURRENT_PASS' or audit.get('certified_profile_added') is not False:
  raise RuntimeError(f'Pu91 durable audit state changed: {audit}')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={'sparc_ref_id':'Pu91','queue_status':'defer_until_new_mechanism','disposition':audit['disposition'],'validation_artifact':str(AUDIT),'reopen_rule':audit['reopen_rule'],'notes':'NGC0055 blind. Puche et al. 1991 is the original VLA H I source. Westmeier et al. 2013 documents retrieval of the original reduced Puche cube from NED, but the current exact NED SIA target+refcode query returns zero records. Later Westmeier/LVHIS products checked in this pass do not expose an exact machine-readable axisymmetric radial H I profile. No raster digitization or blind-outcome inspection; no certified profile added.'}
 if 'Pu91' in by:by['Pu91'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id'])
 with DISP.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 CHECK.write_text('# Pu91 / NGC0055 public H I route checkpoint\n\nStatus: **DEFERRED UNTIL NEW EXACT PUBLIC MECHANISM**\n\n- Target: NGC0055 — blind.\n- Original Puche et al. 1991 reduced VLA cube was historically available through NED, as documented by Westmeier et al. 2013.\n- Current exact NED SIA query returns zero records.\n- Later ATCA work publishes major/minor-axis column-density cuts, not an axisymmetric radial H I profile.\n- LVHIS supplies global flux/radius QC values but no recovered exact radial series in this pass.\n- Reopen only under the durable audit rule.\n- No raster digitization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.\n',encoding='utf-8')
 print(json.dumps({'status':'PU91_NGC0055_DEFERRED','profile_added':False,'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
