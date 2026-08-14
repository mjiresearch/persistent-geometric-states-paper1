#!/usr/bin/env python3
"""Extract source-domain validation metadata for calibration-role THINGS targets.

Walter+2008 supplies center, distance, inclination, PA, natural beam, and THINGS
integrated H I flux. Wang+2016 supplies product-matched THINGS D_HI at
Sigma_HI=1 Msun/pc^2. No science pixels, rotation residuals, persistence
parameters, or blind outcomes are evaluated.
"""
from __future__ import annotations
import csv,io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen

WALTER='https://export.arxiv.org/e-print/0810.2125'
WANG='https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/460/2143/table2.dat'
UA='PersistenceFrameworkPaperI/1.0'
SPLIT=Path('validation/stationary/stationary_split_v1.csv')
OUT=Path('validation/stationary/things_calibration_validation_metadata_v1.json')
# Calibration only. NGC2403 is blind and is deliberately excluded here.
TARGETS=['DDO154','NGC2841','NGC2976','NGC3198']

def compact(s):return re.sub(r'[^A-Z0-9]','',s.upper())
def fetch(url):
 with urlopen(Request(url,headers={'User-Agent':UA}),timeout=120) as h:return h.read()
def split_tex_row(line):
 s=line.replace('\\,','').replace('\\','').strip()
 return [x.strip() for x in s.split('&')]
def num_prefix(s):
 m=re.search(r'[-+]?\d+(?:\.\d+)?',s)
 return None if not m else float(m.group(0))
def main():
 with SPLIT.open(newline='',encoding='utf-8-sig') as f:roles={r['galaxy']:r['stationary_role'] for r in csv.DictReader(f)}
 bad={g:roles.get(g) for g in TARGETS if roles.get(g)!='calibration'}
 if bad:raise RuntimeError(f'calibration-only target role changed: {bad}')
 raw=fetch(WALTER);tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
 tex=''
 for m in tf.getmembers():
  if m.isfile() and m.name.endswith('THINGS_master_astroph.tex'):
   tex=tf.extractfile(m).read().decode('latin-1','replace');break
 if not tex:raise RuntimeError('Walter master tex not found')
 lines=tex.splitlines()
 blocks=[]
 for pat in [r'\\begin\{deluxetable\}.*?\\end\{deluxetable\}',r'\\begin\{table\*?\}.*?\\end\{table\*?\}']:
  for m in re.finditer(pat,tex,re.S):blocks.append(m.group(0))
 hi_blocks=[b for b in blocks if re.search(r'S_\{?\\?rm\s*HI|S_\{?HI|integrated.*flux|HI properties|\\hi.*properties',b,re.I)]
 out={}
 for g in TARGETS:
  cg=compact(g);all_rows=[]
  for i,line in enumerate(lines,1):
   if cg in compact(line) and '&' in line:all_rows.append({'line':i,'text':line,'fields':split_tex_row(line)})
  hib=[]
  for bi,b in enumerate(hi_blocks):
   for line in b.splitlines():
    if cg in compact(line) and '&' in line:hib.append({'block_index':bi,'text':line,'fields':split_tex_row(line)})
  geom=[r for r in all_rows if len(r['fields'])>=10 and re.search(r'\d\d\s+\d\d\s+\d',r['fields'][2] if len(r['fields'])>2 else '')]
  beam=[r for r in all_rows if len(r['fields'])>=5 and r['fields'][1].strip().upper()=='NA']
  out[g]={'all_walter_rows':all_rows,'candidate_geometry_rows':geom,'candidate_natural_beam_rows':beam,'candidate_hi_property_rows':hib}
 wt=fetch(WANG).decode('utf-8','replace');wang=[]
 for line in wt.splitlines():
  if not line.strip():continue
  for g in TARGETS:
   if compact(g) not in compact(line[:20]):continue
   wang.append({'galaxy':g,'raw_line':line})
 result={'status':'THINGS_CALIBRATION_VALIDATION_METADATA_EXTRACTED','targets':TARGETS,'roles':{g:roles[g] for g in TARGETS},'walter_hi_block_count':len(hi_blocks),'walter_hi_block_heads':[b[:2500] for b in hi_blocks],
  'targets_raw':out,'wang_target_rows':wang,
  'boundary':'Published source-domain metadata for calibration galaxies only; no science pixels, rotation residuals, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'roles':result['roles'],'hi_block_count':len(hi_blocks),'targets':out,'wang_rows':wang},indent=2))
if __name__=='__main__':main()
