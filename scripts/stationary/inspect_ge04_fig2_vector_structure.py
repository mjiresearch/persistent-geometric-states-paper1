#!/usr/bin/env python3
"""Inspect the native structure of Ge04 fig2.eps without executing PostScript."""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/astro-ph/0403154';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/ge04_fig2_vector_structure_v1.json')

def fetch_fig():
 req=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');return tf.extractfile(tf.getmember('fig2.eps')).read()

def ps_strings(s):
 vals=[]
 for m in re.finditer(r'\(((?:\\.|[^\\)])*)\)',s):
  x=m.group(1)
  x=re.sub(r'\\([0-7]{1,3})',lambda q:chr(int(q.group(1),8)),x)
  x=x.replace('\\(','(').replace('\\)',')').replace('\\\\','\\')
  if x.strip(): vals.append(x)
 return vals

def counts(b):
 return {k:len(re.findall(rb'(?<![A-Za-z0-9_])'+k.encode()+rb'(?![A-Za-z0-9_])',b)) for k in ['M','R','P','D','F','L','m','l','p','s','f','S']}

def main():
 b=fetch_fig();s=b.decode('latin-1','replace');lines=s.splitlines()
 begin=[];stack=[];blocks=[]
 for i,line in enumerate(lines):
  if line.startswith('%%BeginDocument'):
   stack.append((i,line))
  elif line.startswith('%%EndDocument') and stack:
   st,h=stack.pop();
   if not stack:blocks.append((st,i,h))
 defs=[{'line':i+1,'text':ln} for i,ln in enumerate(lines) if re.search(r'^\s*/[A-Za-z0-9_.-]+\s+.*(?:def|bind)',ln)]
 bbox=[{'line':i+1,'text':ln} for i,ln in enumerate(lines) if 'BoundingBox' in ln]
 blockrecs=[]
 for j,(a,z,h) in enumerate(blocks,1):
  txt='\n'.join(lines[a:z+1]);bb=txt.encode('latin-1','replace');strings=ps_strings(txt)
  blockrecs.append({'index':j,'start_line':a+1,'end_line':z+1,'header':h,'bytes':len(bb),'sha256':hashlib.sha256(bb).hexdigest(),'bounding_boxes':[ln for ln in txt.splitlines() if 'BoundingBox' in ln][:20],'strings':strings[:300],'one_letter_counts':counts(bb),'explicit_ops':{op:len(re.findall((rb'(?<![A-Za-z])'+op.encode()+rb'(?![A-Za-z])'),bb)) for op in ['moveto','lineto','rlineto','curveto','stroke','fill','arc','newpath']}})
 out={'status':'GE04_FIG2_VECTOR_STRUCTURE_INSPECTED','asset_sha256':hashlib.sha256(b).hexdigest(),'n_lines':len(lines),'top_level_bounding_boxes':bbox,'procedure_definitions':defs[:300],'all_strings':ps_strings(s)[:1000],'n_top_level_begin_document_blocks':len(blockrecs),'blocks':blockrecs,
      'head_lines':[{'line':i+1,'text':ln} for i,ln in enumerate(lines[:180])],
      'boundary':'Static source text/vector grammar inspection only; no PostScript execution, OCR, raster digitization, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'n_lines':len(lines),'n_blocks':len(blockrecs),'strings':out['all_strings'][:120],'blocks':[{k:v for k,v in r.items() if k not in {'strings'}} | {'strings':r['strings'][:80]} for r in blockrecs]},indent=2))
if __name__=='__main__':main()
