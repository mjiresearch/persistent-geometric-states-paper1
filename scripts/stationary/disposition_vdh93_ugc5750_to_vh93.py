#!/usr/bin/env python3
"""Race-safe launcher for the current source-disposition rerank pass.

The VdH93/UGC05750 state is already durable. Revalidate that its artifacts remain
present, then apply the current Ca90/NGC0247 disposition before the existing
workflow reranks the source-family queue.
"""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path

REQUIRED=[
 Path('validation/stationary/vdh93_ugc5750_provenance_redirect_v1.json'),
 Path('validation/stationary/CHECKPOINT_VDH93_UGC5750_REDIRECT_TO_VH93.md'),
 Path('scripts/stationary/disposition_ca90_ngc0247.py'),
]

def main():
 missing=[str(p) for p in REQUIRED if not p.exists()]
 if missing: raise RuntimeError(f'Required durable source-state artifacts missing: {missing}')
 old=json.loads(REQUIRED[0].read_text(encoding='utf-8'))
 if old.get('status')!='VDH93_UGC05750_REDIRECT_TO_VH93_CONFIRMED':
  raise RuntimeError('Existing VdH93 disposition status changed')
 subprocess.run([sys.executable,'scripts/stationary/disposition_ca90_ngc0247.py'],check=True)
 print(json.dumps({'status':'SOURCE_DISPOSITION_RERANK_LAUNCH_READY','preserved':'VdH93/UGC05750','advanced':'Ca90/NGC0247'},indent=2))

if __name__=='__main__':main()
