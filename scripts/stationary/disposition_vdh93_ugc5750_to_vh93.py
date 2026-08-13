#!/usr/bin/env python3
"""Race-safe launcher for current source-disposition rerank passes."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
REQUIRED=[Path('validation/stationary/vdh93_ugc5750_provenance_redirect_v1.json'),Path('scripts/stationary/disposition_ca90_ngc0247.py'),Path('scripts/stationary/disposition_la90_ddo170_to_be91.py')]
def main():
 missing=[str(p) for p in REQUIRED if not p.exists()]
 if missing:raise RuntimeError(f'Required durable source-state artifacts missing: {missing}')
 old=json.loads(REQUIRED[0].read_text(encoding='utf-8'))
 if old.get('status')!='VDH93_UGC05750_REDIRECT_TO_VH93_CONFIRMED':raise RuntimeError('Existing VdH93 disposition status changed')
 subprocess.run([sys.executable,'scripts/stationary/disposition_ca90_ngc0247.py'],check=True)
 subprocess.run([sys.executable,'scripts/stationary/disposition_la90_ddo170_to_be91.py'],check=True)
 print(json.dumps({'status':'SOURCE_DISPOSITION_RERANK_LAUNCH_READY','preserved':['VdH93/UGC05750','Ca90/NGC0247'],'advanced':'La90/DDO170'},indent=2))
if __name__=='__main__':main()
