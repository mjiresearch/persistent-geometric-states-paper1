#!/usr/bin/env python3
"""Extract Walter+2008 THINGS H I QC table semantics and frozen validation roles.

Source-text and frozen-role audit only; no science pixels, velocities, residuals,
persistence parameters, or blind outcomes are evaluated.
"""
from __future__ import annotations
import csv,io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/0810.2125';UA='PersistenceFrameworkPaperI/1.0'
SPLIT=Path('validation/stationary/stationary_split_v1.csv')
OUT=Path('validation/stationary/walter2008_hi_qc_table_and_validation_subset_v1.json')
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']
def compact(s):return re.sub(r'[^A-Z0-9]','',s.upper())
def read_split():
 with SPLIT.open(newline='',encoding='utf-8-sig') as f:return {r['galaxy']:r['stationary_role'] for r in csv.DictReader(f)}
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*'); tex=''
 for m in tf.getmembers():
  if m.isfile() and m.name.endswith('THINGS_master_astroph.tex'):
   tex=tf.extractfile(m).read().decode('latin-1','replace');break
 if not tex:raise RuntimeError('THINGS_master_astroph.tex not found')
 # Capture complete deluxetable/table environments that mention H I global properties, flux, mass, or diameter.
 tables=[]
 for pat in [r'\\begin\{deluxetable\}.*?\\end\{deluxetable\}',r'\\begin\{table\*?\}.*?\\end\{table\*?\}']:
  for m in re.finditer(pat,tex,re.S):
   block=m.group(0)
   if re.search(r'HI|\\hi|flux|diameter|mass|beam|weight',block,re.I):
    tables.append({'start_line':tex[:m.start()].count('\n')+1,'block':block[:30000]})
 # Also collect local contexts around table captions / tableheads and exact target global-property lines.
 lines=tex.splitlines(); contexts=[]; target_lines=[]
 for i,line in enumerate(lines):
  if re.search(r'\\tablecaption|\\tablehead|integrated.*flux|HI.*diameter|diameter.*HI|HI.*mass|mass.*HI|global.*HI|flux.*density',line,re.I):
   contexts.append({'line':i+1,'context':'\n'.join(lines[max(0,i-8):min(len(lines),i+12)])})
  cl=compact(line)
  matched=[g for g in TARGETS if compact(g) in cl]
  if matched and line.count('&')>=5:
   target_lines.append({'line':i+1,'targets':matched,'text':line})
 roles=read_split(); role_rows=[{'galaxy':g,'stationary_role':roles[g]} for g in TARGETS]
 calibration=[g for g in TARGETS if roles[g]=='calibration']; blind=[g for g in TARGETS if roles[g]=='blind']
 result={'status':'WALTER2008_HI_QC_TABLE_AND_VALIDATION_SUBSET_AUDITED','arxiv':ARXIV,
  'target_roles':role_rows,'calibration_targets':calibration,'blind_targets':blind,
  'n_calibration_targets':len(calibration),'n_blind_targets':len(blind),
  'table_contexts':contexts,'candidate_tables':tables,'target_table_lines':target_lines,
  'boundary':'Published source-table semantics and frozen roles only; no science pixels, velocities, residuals, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'calibration_targets':calibration,'blind_targets':blind,'table_contexts':contexts,'candidate_tables':tables},indent=2))
if __name__=='__main__':main()
