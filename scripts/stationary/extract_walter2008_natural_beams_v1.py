#!/usr/bin/env python3
"""Extract natural-weighted synthesized beam metadata from Walter+2008 source.

Source-table metadata only; no science pixels or persistence quantities.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/0810.2125';UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/walter2008_natural_beam_extraction_v1.json')
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']
def compact(s):return re.sub(r'[^A-Z0-9]','',s.upper())
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
 tex=[]
 for m in tf.getmembers():
  if m.isfile() and m.name.lower().endswith('.tex'):
   tex.append((m.name,tf.extractfile(m).read().decode('latin-1','replace')))
 contexts=[]
 for name,t in tex:
  lines=t.splitlines()
  for i,line in enumerate(lines):
   cl=compact(line)
   matched=[g for g in TARGETS if compact(g) in cl]
   if matched:
    contexts.append({'file':name,'line':i+1,'targets':matched,'line_text':line,'context':'\n'.join(lines[max(0,i-2):min(len(lines),i+3)])})
 # Candidate beam rows: target row plus tokens that look like beam dimensions / NA weighting.
 candidates=[]
 for c in contexts:
  s=c['line_text']
  if re.search(r'\bNA\b|natural|\\times|arcsec|beam',s,re.I):candidates.append(c)
 result={'status':'WALTER2008_NATURAL_BEAM_SOURCE_ROWS_EXTRACTED','arxiv':ARXIV,'targets':TARGETS,'target_contexts':contexts,'candidate_beam_rows':candidates,
  'boundary':'Published source-table metadata only; no science pixels, profile reconstruction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'candidate_beam_rows':candidates,'all_target_lines':[{'targets':c['targets'],'line':c['line_text']} for c in contexts]},indent=2))
if __name__=='__main__':main()
