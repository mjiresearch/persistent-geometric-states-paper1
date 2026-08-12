#!/usr/bin/env python3
"""Extract the exact Westmeier+2011 NGC300 gas profile from native LaTeX Table 2.

Continuation of CP90 after the committed source-table audit established the
row syntax. This is a later, deeper ATCA public replacement profile for the
Lelli/CP90 NGC300 branch; it is not claimed to be a numerical recovery of the
Puche+1990 VLA profile.

The final Table-2 column is Sigma_gas and already includes the paper's factor
f=1.4 for helium. Values and quoted uncertainties are retained unchanged.
"""
from __future__ import annotations

import csv, hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

URLS=['https://arxiv.org/e-print/1009.0317','https://export.arxiv.org/e-print/1009.0317']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUTCSV=Path('data/stationary/source_reconstruction/westmeier2011_ngc300_gas_profile_v1.csv')
OUTJSON=Path('validation/stationary/cp90_westmeier2011_ngc300_profile_extraction_v1.json')


def fetch():
    attempts=[]
    for u in URLS:
        rec={'url':u}
        try:
            req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
            with urllib.request.urlopen(req,timeout=180) as h:
                raw=h.read();rec.update(status='fetched',final_url=h.geturl(),content_type=h.headers.get('Content-Type',''),bytes=len(raw));attempts.append(rec);return raw,attempts
        except Exception as e:
            rec.update(status='error',error=f'{type(e).__name__}: {e}');attempts.append(rec)
    raise RuntimeError('Westmeier 2011 source fetch failed')


def scalar(field):
    s=field.strip().strip('$').strip()
    s=s.replace('~',' ').replace('{','').replace('}','')
    m=re.search(r'[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?',s)
    if not m: raise ValueError(f'No numeric scalar in field {field!r}')
    return float(m.group(0))


def valerr(field):
    s=field.strip().strip('$').strip()
    s=s.replace('~',' ').replace('{','').replace('}','')
    nums=[float(x) for x in re.findall(r'[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?',s)]
    if not nums: raise ValueError(f'No numeric value in field {field!r}')
    return nums[0], (nums[1] if len(nums)>1 else None)


def main():
    raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    tex=tf.extractfile(tf.getmember('westmeier.tex')).read().decode('latin-1','replace')
    lines=tex.splitlines()
    label=next(i for i,l in enumerate(lines) if r'\label{tab_parameters}' in l)
    beg=next(i for i in range(label,len(lines)) if r'\begin{tabular}' in lines[i])
    end=next(i for i in range(beg+1,len(lines)) if r'\end{tabular}' in lines[i])
    block=lines[beg+1:end]
    parsed=[]
    for line_no,line in enumerate(block,beg+2):
        if '&' not in line: continue
        parts=[p.strip() for p in line.split('&')]
        if len(parts)!=9: continue
        # Native data rows begin with a math-mode integer radius; headers begin with $r$.
        if not re.search(r'\$\s*\d{2,4}\s*\$',parts[0]): continue
        parts[-1]=re.sub(r'\\\\\s*$','',parts[-1]).strip()
        r_arc=scalar(parts[0]);r_kpc=scalar(parts[1]);vrot,vrot_err=valerr(parts[2]);pa=scalar(parts[3]);inc=scalar(parts[4])
        s36,s36e=valerr(parts[5]);s45,s45e=valerr(parts[6]);sstar,sstare=valerr(parts[7]);sgas,sgase=valerr(parts[8])
        parsed.append({
            'galaxy':'NGC0300','stationary_role':'calibration','source_tex_line':line_no,
            'radius_arcsec':r_arc,'radius_kpc_source_paper':r_kpc,
            'vrot_km_s':vrot,'vrot_err_km_s':vrot_err,'position_angle_deg':pa,'inclination_deg':inc,
            'sigma_star_36_msun_pc2':s36,'sigma_star_36_err_msun_pc2':s36e,
            'sigma_star_45_msun_pc2':s45,'sigma_star_45_err_msun_pc2':s45e,
            'sigma_star_combined_msun_pc2':sstar,'sigma_star_combined_err_msun_pc2':sstare,
            'sigma_gas_msun_pc2':sgas,'sigma_gas_err_msun_pc2':sgase,
            'helium_status':'already includes helium x1.4','source_table':'Westmeier et al. 2011 Table 2',
        })
    if len(parsed)!=20:
        raise RuntimeError(f'Expected 20 native Table-2 rows, got {len(parsed)}')
    expected=[float(x) for x in range(100,2001,100)]
    got=[r['radius_arcsec'] for r in parsed]
    if got!=expected: raise RuntimeError(f'Radius grid mismatch: {got}')
    if abs(parsed[0]['radius_kpc_source_paper']-0.92)>1e-9 or abs(parsed[-1]['radius_kpc_source_paper']-18.42)>0.06:
        raise RuntimeError(f'Physical radius endpoint QC failed: {parsed[0]["radius_kpc_source_paper"]}, {parsed[-1]["radius_kpc_source_paper"]}')
    if any(r['sigma_gas_msun_pc2']<0 for r in parsed):raise RuntimeError('Negative Sigma_gas encountered')
    inner=[r['sigma_gas_msun_pc2'] for r in parsed[:6]]
    if not (5.5 <= sum(inner)/len(inner) <= 8.0):raise RuntimeError(f'Inner-profile QC failed: mean={sum(inner)/len(inner)}')
    if parsed[-1]['sigma_gas_msun_pc2'] >= parsed[9]['sigma_gas_msun_pc2']:
        raise RuntimeError('Outer profile does not decline as publication describes')

    OUTCSV.parent.mkdir(parents=True,exist_ok=True)
    fields=list(parsed[0])
    with OUTCSV.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in parsed:
            q={k:(f'{v:.10g}' if isinstance(v,float) else v) for k,v in r.items()};w.writerow(q)
    out={
        'status':'CP90_WESTMEIER2011_NGC300_PROFILE_EXTRACTED',
        'source':'Westmeier, Braun & Koribalski 2011 MNRAS 410 2217; arXiv:1009.0317',
        'source_package_attempts':attempts,'source_package_sha256':hashlib.sha256(raw).hexdigest(),
        'source_tex_sha256':hashlib.sha256(tex.encode('latin-1','replace')).hexdigest(),
        'source_table':'Table 2 / tab_parameters','profile_csv':str(OUTCSV),'n_rows':len(parsed),
        'radius_arcsec_first':parsed[0]['radius_arcsec'],'radius_arcsec_last':parsed[-1]['radius_arcsec'],
        'radius_kpc_first':parsed[0]['radius_kpc_source_paper'],'radius_kpc_last':parsed[-1]['radius_kpc_source_paper'],
        'sigma_gas_first':parsed[0]['sigma_gas_msun_pc2'],'sigma_gas_last':parsed[-1]['sigma_gas_msun_pc2'],
        'helium_status':'Sigma_gas already includes the source paper factor f=1.4 for helium.',
        'provenance_rule':'Exact native LaTeX Table-2 values; later deeper ATCA public replacement for the CP90/Lelli NGC300 acquisition branch, not a numerical extraction of Puche et al. 1990.',
        'qc':{'twenty_rows':True,'100_arcsec_grid_100_to_2000':True,'paper_radius_endpoints_match':True,'inner_sigma_near_7_including_helium':True,'outer_profile_declines':True},
        'boundary':'No raster digitization, map/cube reconstruction, re-fitting, common-distance renormalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUTJSON.parent.mkdir(parents=True,exist_ok=True);OUTJSON.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
