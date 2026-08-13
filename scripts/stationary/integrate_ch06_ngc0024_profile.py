#!/usr/bin/env python3
import csv,json
from pathlib import Path
Q=Path('validation/stationary/ch06_ngc0024_native_hi_profile_recovery_v1.json')
P=Path('data/stationary/source_reconstruction/ch06_ngc0024_hi_profile_v1.csv')
O=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
D=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
def rd(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def wr(p,r,f):
 with p.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=f);w.writeheader();w.writerows(r)
q=json.loads(Q.read_text())
if q['status']!='CH06_NGC0024_NATIVE_VECTOR_HI_PROFILE_RECOVERED' or q['n_points']!=10 or not q['independent_qc']['passes']:raise RuntimeError('Ch06 QC failed')
p=rd(P)
if len(p)!=10 or any(x['galaxy']!='NGC0024' or x['stationary_role']!='blind' for x in p):raise RuntimeError('profile mismatch')
r=rd(O);f=list(r[0]);by={x['galaxy']:x for x in r}
new={'galaxy':'NGC0024','stationary_role':'blind','public_source_family':'Chemin et al. 2006 direct VLA H I / native IDL Figure 6 left','acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'10','source_quantity':'inclination-corrected radial H I surface density','helium_status':'helium not applied; raw H I preserved','preferred_public_source':'1','source_artifact':str(P),'notes':'10 exact native-vector IDL diamond markers from f11.eps. Source D=6.8 Mpc; frozen SPARC D=7.3 Mpc. Midpoint-annulus integral 5.53e8 Msun vs paper M_HI=5.87e8 Msun (5.8% delta). No OCR/raster digitization or blind outcome inspection.'}
if 'NGC0024' in by:by['NGC0024'].update(new)
else:r.append(new)
r.sort(key=lambda x:x['galaxy']);wr(O,r,f)
dr=rd(D);df=list(dr[0]);db={x['sparc_ref_id']:x for x in dr}
for ref,status,disp in [('Ch06','resolved_public_profile_recovered','NGC0024_direct_Ch06_native_vector_HI_profile_recovered'),('Di08','redirect_existing_source_family','NGC0024_Halpha_downstream_route_redirects_to_resolved_Ch06_direct_HI_source')]:
 z={'sparc_ref_id':ref,'queue_status':status,'disposition':disp,'validation_artifact':str(Q),'reopen_rule':'reopen_only_for_higher_fidelity_machine_readable_direct_HI_profile_or_documented_source_correction','notes':'NGC0024 blind source acquisition resolved via Chemin et al. 2006 f11.eps native-vector H I profile; 10 bins; raw H I.'}
 if ref in db:db[ref].update(z)
 else:dr.append(z)
dr.sort(key=lambda x:x['sparc_ref_id']);wr(D,dr,df)
Path('validation/stationary/CHECKPOINT_AFTER_CH06_NGC0024_PROMOTION.md').write_text('# Ch06 / NGC0024 H I checkpoint\n\nStatus: **NGC0024 native-vector H I profile promoted.**\n\n- Blind target; 10 exact source-native IDL vector bins.\n- Raw H I; no helium scaling.\n- Source distance 6.8 Mpc; frozen distance 7.3 Mpc.\n- Independent profile integral: 5.53e8 Msun vs paper 5.87e8 Msun (5.8% difference).\n- Di08 redirects to the resolved direct Ch06 H I source.\n- No persistence fitting or blind-outcome inspection. L_A and C_A remain locked.\n')
print(json.dumps({'status':'CH06_NGC0024_PROMOTED','profile_rows':10}))
