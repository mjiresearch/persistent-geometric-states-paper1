#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
PRIORITY=Path('validation/stationary/sparc_hi_reference_family_priority_v1_summary.json')
CHECK=Path('validation/stationary/CHECKPOINT_PU91_NGC0055_PUBLIC_ROUTE.md')
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
 q=json.loads(PRIORITY.read_text())
 probe=q.get('live_family_public_route_probe',{})
 if probe.get('status')!='PU91_NGC55_NED_SIA_PROBED' or probe.get('n_records')!=0:
  raise RuntimeError(f'Pu91 NED route state changed: {probe}')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={'sparc_ref_id':'Pu91','queue_status':'defer_until_new_mechanism','disposition':'NGC0055_original_Puche1991_VLA_cube_historically_retrieved_from_NED_but_current_exact_NED_SIA_query_returns_zero_records_later_ATCA_products_do_not_publish_axisymmetric_numeric_radial_HI_profile','validation_artifact':str(PRIORITY),'reopen_rule':'reopen_for_restored_Puche1991_NED_cube_public_LVHIS_or_Westmeier_science_ready_FITS_or_exact_machine_readable_axisymmetric_radial_HI_profile','notes':'NGC0055 blind. Westmeier et al. 2013 documents retrieving the original reduced Puche et al. 1991 VLA cube from NED, but the current NED SIA query TARGET=NGC55 + REFCODE=1991AJ....101..447P returns zero records. Westmeier 2013 publishes major/minor-axis H I column-density cuts, not the required axisymmetric radial profile. LVHIS publishes global checks (F_HI=2025.4 Jy km/s; R_HI=1106 arcsec) but no currently recovered machine-readable radial profile in this acquisition pass. No raster digitization or blind-outcome inspection.'}
 if 'Pu91' in by:by['Pu91'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id'])
 with DISP.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 CHECK.write_text('# Pu91 / NGC0055 public H I route checkpoint\n\nStatus: **DEFERRED UNTIL NEW EXACT PUBLIC MECHANISM**\n\n- Target: NGC0055 — blind.\n- Original Puche et al. 1991 reduced VLA cube was historically available through NED, as documented by Westmeier et al. 2013.\n- Current exact NED SIA query returns zero records.\n- Later ATCA work publishes major/minor-axis column-density cuts, not an axisymmetric radial H I profile.\n- LVHIS supplies global flux/radius QC values but no recovered exact radial series in this pass.\n- Reopen only for restored cube/FITS or an exact machine-readable radial profile.\n- No raster digitization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.\n',encoding='utf-8')
 print(json.dumps({'status':'PU91_NGC0055_DEFERRED','profile_added':False,'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
