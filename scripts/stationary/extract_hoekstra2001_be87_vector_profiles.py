#!/usr/bin/env python3
"""Recover Begeman-linked radial H I profiles from Hoekstra et al. 2001 Fig.1 vectors.

Source chain:
Lelli Be87 -> Begeman 1987 -> Hoekstra, van Albada & Sancisi 2001 public
republication of observed H I surface-density profiles.

Accepted panels (publication-layout QC already frozen):
- NGC2903 = row 1, col 1; Hoekstra refs include Begeman 1987.
- NGC5033 = row 1, col 2; Hoekstra refs include Begeman 1987.
- NGC5371 = row 3, col 4; Hoekstra refs include Begeman 1987.

NGC6503 is intentionally excluded here: its Hoekstra Table-1 profile provenance
is Broeils 1992b + Wevers 1984, not Begeman 1987.

Scientific coordinates come ONLY from native vector drawing objects and native
vector frame/tick geometry in the compiled arXiv PDF. Raster renderings were
used solely for panel-label and printed-axis-label QC, never for curve values.

Output remains a normalized-radius candidate (`R/R_out`). No physical-radius
conversion, helium correction, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import csv, json, math
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen
import pymupdf

PDF_URL="https://arxiv.org/pdf/astro-ph/0010569"
OUT=Path("data/stationary/source_reconstruction/hoekstra2001_be87_hi_vector_profiles_candidate_v1.csv")
QC=Path("validation/stationary/hoekstra2001_be87_hi_vector_profiles_candidate_v1_summary.json")
TARGETS={
    (1,1):("NGC2903","calibration","Begeman 1987 + Kent 1987"),
    (1,2):("NGC5033","blind","Kent 1986 + Begeman 1987"),
    (3,4):("NGC5371","calibration","Begeman 1987 + Wevers et al. 1984"),
}


def unique(vals,tol=0.1):
    out=[]
    for v in sorted(vals):
        if not out or abs(v-out[-1])>tol:out.append(v)
    return out


def linfit(xs,ys):
    xm=sum(xs)/len(xs);ym=sum(ys)/len(ys)
    den=sum((x-xm)**2 for x in xs)
    a=sum((x-xm)*(y-ym) for x,y in zip(xs,ys))/den
    b=ym-a*xm
    return a,b


def main():
    raw=urlopen(Request(PDF_URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0","Accept":"application/pdf"}),timeout=120).read()
    doc=pymupdf.open(stream=raw,filetype="pdf"); page=doc[3]
    drawings=page.get_drawings()

    # Recover the five shared column boundaries and seven row boundaries from
    # full-height/full-width black vector frame segments.
    vx=[]; yends=[]; hx=[]; xends=[]
    for d in drawings:
        col=d.get("color")
        if not col or max(col)>0.05:continue
        for it in d.get("items",[]):
            if it[0]!="l":continue
            p0,p1=it[1],it[2]
            if abs(p0.x-p1.x)<0.03 and abs(p0.y-p1.y)>55 and 80<p0.x<520 and 120<min(p0.y,p1.y)<540:
                vx.append(p0.x);yends.extend([p0.y,p1.y])
            if abs(p0.y-p1.y)<0.03 and abs(p0.x-p1.x)>85 and 80<min(p0.x,p1.x)<520 and 120<p0.y<540:
                hx.append(p0.y);xends.extend([p0.x,p1.x])
    x_edges=unique(vx)
    y_edges=unique(yends)
    # Some outer horizontal frame segments may be represented only once; merge
    # their y coordinates if needed. Expected Fig.1 geometry: 5 x-edges, 7 y-edges.
    y_edges=unique(y_edges+hx)
    if len(x_edges)!=5:
        raise RuntimeError(f"Expected 5 column boundaries, got {x_edges}")
    if len(y_edges)!=7:
        # restrict to the six nearly-equal panel-height intervals spanning red curves
        # by selecting the longest regular 7-value subsequence.
        cand=[]
        for i in range(max(0,len(y_edges)-6)):
            z=y_edges[i:i+7]
            if len(z)==7:
                ds=[z[j+1]-z[j] for j in range(6)]
                cand.append((max(ds)-min(ds),z))
        if not cand:raise RuntimeError(f"Could not recover row boundaries: {y_edges}")
        y_edges=min(cand,key=lambda q:q[0])[1]

    # Publication y-axis QC: on the bottom row, printed major H I labels are
    # log10(Sigma_HI/Msun pc^-2) = +1, 0, -1 at these native-vector tick y's.
    y_bottom=y_edges[-1]
    major_y=[469.8979797363281,495.2209777832031,520.3280029296875]
    major_log=[1.0,0.0,-1.0]
    # Fit against local y offset so the identical transform can be shifted to each row.
    dy=[y-y_bottom for y in major_y]
    slope,intercept=linfit(dy,major_log)

    # Identify red dashed vector drawings and assign each to a panel by center.
    panel_drawings=defaultdict(list)
    for di,d in enumerate(drawings):
        col=d.get("color")
        if not col or len(col)<3 or not (col[0]>0.75 and col[1]<0.35 and col[2]<0.35):continue
        if not d.get("dashes") or d.get("dashes") in {"[] 0","[]0"}:continue
        r=d.get("rect");cx=(r.x0+r.x1)/2;cy=(r.y0+r.y1)/2
        c=next((j+1 for j in range(4) if x_edges[j]-0.2<=cx<=x_edges[j+1]+0.2),None)
        row=next((j+1 for j in range(6) if y_edges[j]-0.2<=cy<=y_edges[j+1]+0.2),None)
        if row and c:panel_drawings[(row,c)].append((di,d))

    rows=[]; target_qc={}
    for key,(galaxy,role,profile_refs) in TARGETS.items():
        row,col=key
        ds=panel_drawings.get(key,[])
        if not ds:raise RuntimeError(f"No red dashed vector path for {galaxy} at {key}")
        xl,xr=x_edges[col-1],x_edges[col]
        yt,yb=y_edges[row-1],y_edges[row]
        pts=[]
        for di,d in ds:
            for it in d.get("items",[]):
                if it[0]!="l":continue
                a,b=it[1],it[2]
                for p in (a,b):
                    if xl-0.5<=p.x<=xr+0.5 and yt-0.5<=p.y<=yb+0.5:
                        if not pts or abs(p.x-pts[-1][0])>1e-6 or abs(p.y-pts[-1][1])>1e-6:
                            pts.append((p.x,p.y,di))
        # Preserve path order while removing exact repeated coordinates that can
        # recur at adjacent segment boundaries or split drawing objects.
        cleaned=[]
        seen_consecutive=None
        for x,y,di in pts:
            q=(round(x,6),round(y,6),di)
            if q==seen_consecutive:continue
            cleaned.append((x,y,di));seen_consecutive=q
        if len(cleaned)<3:raise RuntimeError(f"Too few vector vertices for {galaxy}: {len(cleaned)}")

        vals=[]
        for k,(x,y,di) in enumerate(cleaned):
            rnorm=1.1*(x-xl)/(xr-xl)
            local_y=y-yb
            log_sigma=slope*local_y+intercept
            sigma=10.0**log_sigma
            vals.append((rnorm,sigma,log_sigma,x,y,di))
            rows.append({
                "galaxy":galaxy,"stationary_role":role,"panel_row":row,"panel_col":col,
                "point_index":k,"pdf_drawing_index":di,
                "x_pdf":f"{x:.9f}","y_pdf":f"{y:.9f}",
                "r_over_rout":f"{rnorm:.9f}",
                "log10_sigma_hi_msun_pc2":f"{log_sigma:.9f}",
                "sigma_hi_msun_pc2":f"{sigma:.9f}",
                "radius_status":"normalized_to_Hoekstra_Rout_outermost_rotation_curve_point",
                "source_quantity":"raw HI surface density from published dashed vector profile",
                "helium_status":"raw_HI_no_helium_applied",
                "lelli_ref":"Be87",
                "profile_republication":"Hoekstra_van_Albada_Sancisi_2001_MNRAS323_453",
                "profile_reference_provenance":profile_refs,
                "acquisition_status":"vector_profile_candidate_recovered",
            })
        sig=[z[1] for z in vals]; rr=[z[0] for z in vals]
        target_qc[galaxy]={
            "panel":[row,col],"n_drawing_objects":len(ds),"drawing_indices":[z[0] for z in ds],
            "n_vertices":len(vals),"r_over_rout_min":min(rr),"r_over_rout_max":max(rr),
            "sigma_hi_min":min(sig),"sigma_hi_max":max(sig),
            "log_sigma_min":min(z[2] for z in vals),"log_sigma_max":max(z[2] for z in vals),
        }

    fields=[
        "galaxy","stationary_role","panel_row","panel_col","point_index","pdf_drawing_index",
        "x_pdf","y_pdf","r_over_rout","log10_sigma_hi_msun_pc2","sigma_hi_msun_pc2",
        "radius_status","source_quantity","helium_status","lelli_ref","profile_republication",
        "profile_reference_provenance","acquisition_status",
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)

    qc={
        "status":"HOEKSTRA2001_BE87_VECTOR_PROFILE_CANDIDATES_RECOVERED",
        "source_pdf":PDF_URL,"pdf_page_index":3,
        "x_edges":x_edges,"y_edges":y_edges,
        "x_axis_mapping":"R/Rout = 1.1*(x-x_left)/(x_right-x_left); native ticks 0.0..1.1 in 0.1 steps",
        "y_major_tick_calibration":{"native_y":major_y,"printed_log10_sigma_labels":major_log,"local_linear_slope":slope,"local_linear_intercept":intercept},
        "y_axis_mapping":"log10 Sigma_HI [Msun pc^-2] from printed +1,0,-1 major labels; Sigma=10^logSigma",
        "targets":target_qc,
        "n_total_rows":len(rows),
        "qc_expectation":"Hoekstra text states inner maximum HI surface densities are about 6 Msun pc^-2; recovered maxima should be of that order, with galaxy-specific structure retained.",
        "provenance_boundary":"NGC6503 intentionally excluded from Be87 candidate because Hoekstra Table 1 cites Broeils 1992b + Wevers 1984, not Begeman 1987, for that panel's profile provenance.",
        "freeze_boundary":"Candidate-level only pending exact Rout-to-physical-radius recovery. No helium scaling, distance normalization, persistence fitting, or blind outcomes.",
    }
    QC.parent.mkdir(parents=True,exist_ok=True);QC.write_text(json.dumps(qc,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(qc,indent=2))

if __name__=="__main__":main()
