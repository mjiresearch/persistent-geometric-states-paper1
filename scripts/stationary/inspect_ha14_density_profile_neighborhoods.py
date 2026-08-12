#!/usr/bin/env python3
"""Inspect raw/style neighborhoods around Ha14 density comparison curves.
Static source inspection only; PostScript is never executed.
"""
from __future__ import annotations
import io,json,re,tarfile,urllib.request,hashlib
from pathlib import Path
URL='https://arxiv.org/e-print/1407.1744';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ha14_density_profile_neighborhoods_v1.json')

def fetch():
 req=urllib.request.Request(URL,headers={'User-Agent':UA});
 with urllib.request.urlopen(req,timeout=180) as h:return h.read()

def main():
 raw=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');b=tf.extractfile(tf.getmember('fig-density.eps')).read();lines=b.decode('latin-1','replace').splitlines()
 # Locate first red threshold command in each panel.
 reds=[i for i,l in enumerate(lines) if '1.000 0.000 0.000 setrgbcolor' in l]
 neighborhoods=[]
 for j,i in enumerate(reds):
   neighborhoods.append({'red_index':j,'red_line':i+1,'before_after':[{'line':k+1,'text':lines[k]} for k in range(max(0,i-35),min(len(lines),i+12))]})
 # All black-color reset locations, linewidth changes, dash resets, and long compact R streams.
 black_resets=[{'line':i+1,'text':l} for i,l in enumerate(lines) if '0.000 0.000 0.000 setrgbcolor' in l]
 widths=[{'line':i+1,'text':l} for i,l in enumerate(lines) if 'setlinewidth' in l and i>35]
 dash=[{'line':i+1,'text':l} for i,l in enumerate(lines) if re.search(r'\bL[0-5]\b',l) and i>35]
 # Source lines containing at least 5 relative line commands; useful for profile polylines.
 rstreams=[]
 for i,l in enumerate(lines):
   n=len(re.findall(r'[-+]?\d+(?:\.\d+)?\s+[-+]?\d+(?:\.\d+)?\s+R\b',l))
   if n>=5:rstreams.append({'line':i+1,'n_R':n,'text':l[:5000]})
 out={'status':'HA14_DENSITY_PROFILE_NEIGHBORHOODS_COMPLETE','asset_sha256':hashlib.sha256(b).hexdigest(),'red_threshold_lines':[i+1 for i in reds],
      'neighborhoods':neighborhoods,'black_color_resets':black_resets,'linewidth_lines':widths,'dash_lines':dash,'rstream_lines':rstreams,
      'boundary':'Static source inspection only; no PostScript execution, raster digitization, normalization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'red_lines':out['red_threshold_lines'],'black_resets':black_resets,'widths':widths,'neighborhoods':neighborhoods},indent=2))
if __name__=='__main__':main()
