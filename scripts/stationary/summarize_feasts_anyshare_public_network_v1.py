#!/usr/bin/env python3
"""Compact the redacted FEASTS AnyShare browser capture into public root metadata.

Reads only the already-committed redacted capture. Extracts shared-root IDs,
names/types, successful public API endpoints, and localStorage key names. It does
not recover, print, or persist any token/cookie/authorization value.
"""
from __future__ import annotations
import json
from pathlib import Path

SRC=Path('validation/stationary/feasts_anyshare_public_network_v1.json')
OUT=Path('validation/stationary/feasts_anyshare_public_inventory_seed_v1.json')
SENSITIVE=('token','authorization','credential','cookie','secret','password','session')
KEEP=('id','name','type','path','size','created_at','modified_at','updated_at','docid','entry_id','parent_id','object_id','item_id','title','belongs_to')

def clean_scalar_map(d):
    out={}
    for k,v in d.items():
        kl=str(k).lower()
        if any(s in kl for s in SENSITIVE): continue
        if kl in KEEP or kl.endswith('_id') or kl in ('is_dir','is_folder','item_type'):
            if isinstance(v,(str,int,float,bool)) or v is None: out[k]=v
            elif isinstance(v,dict): out[k]=clean_scalar_map(v)
    return out

def collect_objects(x,acc,depth=0):
    if depth>8:return
    if isinstance(x,dict):
        c=clean_scalar_map(x)
        if c and any(k in c for k in ('id','name','title','docid','entry_id','object_id','item_id')):
            acc.append(c)
        for k,v in x.items():
            if any(s in str(k).lower() for s in SENSITIVE):continue
            collect_objects(v,acc,depth+1)
    elif isinstance(x,list):
        for v in x:collect_objects(v,acc,depth+1)

def main():
    src=json.loads(SRC.read_text())
    shares=[]
    for s in src.get('shares',[]):
        api=[]; objs=[]
        for e in s.get('network',[]):
            if e.get('status') in (200,201) and '/api/' in e.get('url',''):
                api.append({'method':e.get('method'),'url':e.get('url'),'status':e.get('status')})
        for r in s.get('public_json_responses',[]):
            if '/api/efast/v1/entry-item' in r.get('url','') or '/api/shared-link/v1/links/' in r.get('url',''):
                collect_objects(r.get('json'),objs)
        # stable de-dup by JSON representation
        uniq=[];seen=set()
        for o in objs:
            key=json.dumps(o,sort_keys=True,ensure_ascii=False)
            if key not in seen:seen.add(key);uniq.append(o)
        shares.append({'label':s.get('label'),'share_url':s.get('share_url'),'page_title':s.get('page_title'),'visible_text':s.get('visible_text'),'local_storage_key_names':[x.get('key') for x in s.get('local_storage_keys',[])],'successful_public_api_calls':api,'public_root_objects':uniq})
    out={'status':'FEASTS_ANYSHARE_PUBLIC_INVENTORY_SEED_SUMMARIZED','shares':shares,'boundary':'Derived only from already-redacted fresh unauthenticated public-share capture; no token/cookie/authorization values stored.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
