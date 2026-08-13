#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
AUD=Path('validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_DISPOSITION_V1.md')
CHECK=Path('validation/stationary/CHECKPOINT_LA90_DDO170_REDIRECT_TO_BE91.md')
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
 if not AUD.exists():raise RuntimeError('Authoritative Be91 original-source audit missing')
 text=AUD.read_text(encoding='utf-8')
 required=['DDO170` -> Lake, Schommer & van Gorkom (1990), AJ 99, 547','The paper publishes the radial H I distribution in Figure 5','a = 95 arcsec','Machine-readable/native radial `Sigma_HI(R)` values: **NOT RECOVERED**']
 if any(x not in text for x in required):raise RuntimeError('DDO170 Be91 audit evidence changed')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={'sparc_ref_id':'La90','queue_status':'redirect_existing_source_family','disposition':'same_original_DDO170_Lake1990_HI_source_already_exhaustively_audited_through_Be91_branch','validation_artifact':str(AUD),'reopen_rule':'reopen_only_for_genuinely_new_machine_readable_radial_HI_table_public_calibrated_map_cube_exact_vector_republication_or_fully_normalized_analytic_profile','notes':'La90 is Lake, Schommer & van Gorkom 1990 AJ 99,547, the exact original DDO170 H I branch already audited under Be91. Figure 5 is the radial H I distribution; the paper states a Gaussian scale a=95 arcsec but does not expose a complete independently normalized analytic profile or numerical/vector series. Do not repeat raster/scan route.'}
 if 'La90' in by:by['La90'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id'])
 with DISP.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 CHECK.write_text('# La90 / DDO170 redirect checkpoint\n\nStatus: **REDIRECTED TO EXISTING Be91 ORIGINAL-SOURCE AUDIT**\n\n- DDO170 is blind.\n- La90 is Lake, Schommer & van Gorkom (1990), AJ 99, 547.\n- Same branch was already exhaustively audited under Be91.\n- Figure 5 radial H I distribution remains figure-only; Gaussian scale a=95 arcsec is not independently normalized into a complete analytic profile.\n- No raster digitization, profile fitting, persistence fitting, or blind-outcome inspection.\n- L_A and C_A remain locked.\n\nResume at the newly reranked live family.\n',encoding='utf-8')
 print(json.dumps({'status':'LA90_DDO170_REDIRECTED_TO_BE91','profile_added':False,'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
