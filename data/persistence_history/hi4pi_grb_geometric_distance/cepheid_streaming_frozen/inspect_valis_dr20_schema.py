#!/usr/bin/env python3
from pathlib import Path
import json,requests
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'osc_rv_target_rank'/'sdss_dr20_recovery'; OUT.mkdir(parents=True,exist_ok=True)
url='https://api.sdss.org/valis/openapi.json'
r=requests.get(url,timeout=20); r.raise_for_status(); spec=r.json()
want=['/target/spectra/{sdss_id}','/target/pipe/boss/{sdss_id}','/target/pipelines/{sdss_id}','/target/astra/{pipeline}/{sdss_id}','/query/sdssid']
out={p:spec.get('paths',{}).get(p) for p in want}
with open(OUT/'valis_endpoint_schemas.json','w') as f: json.dump(out,f,indent=2)
print(json.dumps(out,indent=2)[:30000])
