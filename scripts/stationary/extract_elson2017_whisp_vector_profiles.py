#!/usr/bin/env python3
"""Extract calibrated Elson (2017) WHISP H I curves from vector Appendix PDFs.

This is a *candidate numerical reconstruction* product, not the final frozen
stationary H I profile table. The red H I curve geometry is taken directly from
the authors' vector PDF. Physical x/y scales come from the separately audited
axis calibration, which uses published Swaters/Elson R_HI and mean-Sigma_HI
anchors. That provenance distinction is retained in every row.

No helium factor, frozen-SPARC distance conversion, interpolation, or
persistence quantity is applied here.
"""
from __future__ import annotations

import csv
import io
import json
import math
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

import fitz

ARXIV = "https://export.arxiv.org/e-print/1709.03288"
CAL = Path("validation/stationary/elson2017_whisp_vector_axis_calibration_v1.json")
OUT = Path("data/stationary/source_reconstruction/elson2017_whisp_vector_profiles_candidate_v1.csv")
SUMMARY = Path("validation/stationary/elson2017_whisp_vector_profiles_candidate_v1_summary.json")
UA = "PersistenceFrameworkPaperI/1.0"


def download() -> bytes:
    req = Request(ARXIV, headers={"User-Agent": UA})
    with urlopen(req, timeout=90) as h:
        return h.read()


def is_red(d) -> bool:
    c = d.get("color")
    return c is not None and len(c) >= 3 and abs(float(c[0])-1) < 1e-4 and abs(float(c[1])) < 1e-4 and abs(float(c[2])) < 1e-4


def inside_fraction(rect, box) -> float:
    x0,y0,x1,y1 = map(float, box)
    ix0=max(rect.x0,x0); iy0=max(rect.y0,y0); ix1=min(rect.x1,x1); iy1=min(rect.y1,y1)
    inter=max(0.0,ix1-ix0)*max(0.0,iy1-iy0)
    area=max(1e-12,(rect.x1-rect.x0)*(rect.y1-rect.y0))
    return inter/area


def choose_red(page, box):
    cand=[]
    for d in page.get_drawings():
        if not is_red(d):
            continue
        r=d.get("rect")
        if r is None:
            continue
        frac=inside_fraction(r,box)
        if frac > 0.95:
            cand.append((frac, len(d.get("items",[])), d))
    if not cand:
        raise RuntimeError(f"No red path contained by plot box {box}")
    cand.sort(key=lambda z:(z[0],z[1]), reverse=True)
    # A WHISP H I profile path is the long red polyline, not a label/glyph.
    best=cand[0][2]
    if len(best.get("items",[])) < 20:
        raise RuntimeError(f"Best red path too short: {len(best.get('items',[]))}")
    return best


def vertices(d):
    pts=[]
    for item in d.get("items",[]):
        if not item:
            continue
        kind=item[0]
        if kind != "l" or len(item) < 3:
            continue
        p0,p1=item[1],item[2]
        if not pts:
            pts.append((float(p0.x),float(p0.y)))
        if not pts or abs(pts[-1][0]-float(p1.x))>1e-7 or abs(pts[-1][1]-float(p1.y))>1e-7:
            pts.append((float(p1.x),float(p1.y)))
    if len(pts) < 20:
        raise RuntimeError(f"Recovered too few polyline vertices: {len(pts)}")
    return pts


def crossing_radius(rows, level=1.0):
    for a,b in zip(rows[:-1],rows[1:]):
        ya=float(a["sigma_hi_msun_pc2"]); yb=float(b["sigma_hi_msun_pc2"])
        if (ya-level)*(yb-level) <= 0 and ya != yb:
            xa=float(a["radius_source_kpc"]); xb=float(b["radius_source_kpc"])
            t=(level-ya)/(yb-ya)
            return xa+t*(xb-xa)
    return None


def main():
    cal=json.loads(CAL.read_text(encoding="utf-8"))
    targets=cal.get("targets",[])
    if len(targets) != 19 or cal.get("n_with_candidate") != 19 or cal.get("n_without_candidate") != 0:
        raise RuntimeError("Axis calibration is not the expected solved 19/19 product")

    raw=download()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    pdf_cache={}
    output=[]
    per=[]

    for t in targets:
        g=t["galaxy"]
        best=t.get("best")
        if not best:
            raise RuntimeError(f"No best calibration for {g}")
        pdfname=t["source_pdf"]
        if pdfname not in pdf_cache:
            pdfbytes=tf.extractfile(pdfname).read()
            pdf_cache[pdfname]=fitz.open(stream=pdfbytes,filetype="pdf")
        page=pdf_cache[pdfname][0]
        d=choose_red(page,t["plot_box_pdf"])
        pts=vertices(d)

        x0=float(t["plot_x0_pdf"]); y0=float(t["plot_y0_pdf"])
        ax=float(best["kpc_per_pdf_x"]); ay=float(best["sigma_per_pdf_y"])
        source_d=float(t["source_distance_mpc"])
        kpc_per_arcsec=source_d*1000.0/206265.0
        rows=[]
        for j,(x,y) in enumerate(pts):
            r=(x-x0)*ax
            s=(y0-y)*ay
            r_arcsec=r/kpc_per_arcsec
            row={
                "galaxy":g,
                "stationary_role":t["stationary_role"],
                "source":"Elson_2017_WHISP_vector_appendix",
                "source_pdf":pdfname,
                "source_panel_index":t["panel_index"],
                "vector_vertex_index":j,
                "radius_source_kpc":f"{r:.10g}",
                "radius_source_arcsec_derived":f"{r_arcsec:.10g}",
                "sigma_hi_msun_pc2":f"{s:.10g}",
                "source_distance_mpc":f"{source_d:.10g}",
                "source_rhi_kpc_anchor":f"{float(t['source_rhi_kpc']):.10g}",
                "source_mean_sigma_hi_3p2h_anchor":f"{float(t['source_mean_sigma_hi_3p2h']):.10g}",
                "axis_kpc_per_pdf_x":f"{ax:.12g}",
                "axis_sigma_per_pdf_y":f"{ay:.12g}",
                "axis_tick_nice_score":f"{float(best['nice_score']):.10g}",
                "helium_applied":"0",
                "frozen_distance_applied":"0",
                "profile_status":"vector_geometry_exact_axis_scale_reconstructed_candidate",
            }
            rows.append(row); output.append(row)

        rs=[float(r["radius_source_kpc"]) for r in rows]
        ss=[float(r["sigma_hi_msun_pc2"]) for r in rows]
        mono=all(b>a for a,b in zip(rs[:-1],rs[1:]))
        cross=crossing_radius(rows,1.0)
        rhi=float(t["source_rhi_kpc"])
        rel=None if cross is None else abs(cross-rhi)/max(rhi,1e-12)
        per.append({
            "galaxy":g,
            "stationary_role":t["stationary_role"],
            "n_vertices":len(rows),
            "radius_min_kpc":min(rs),
            "radius_max_kpc":max(rs),
            "sigma_min":min(ss),
            "sigma_max":max(ss),
            "radius_strictly_increasing":mono,
            "negative_sigma_count":sum(s<0 for s in ss),
            "rhi_crossing_kpc_from_sampled_vector":cross,
            "source_rhi_kpc_anchor":rhi,
            "rhi_crossing_relative_error":rel,
            "mean_sigma_anchor_abs_error":float(best["mean_abs_error"]),
            "axis_tick_nice_score":float(best["nice_score"]),
        })

    fields=[
        "galaxy","stationary_role","source","source_pdf","source_panel_index","vector_vertex_index",
        "radius_source_kpc","radius_source_arcsec_derived","sigma_hi_msun_pc2","source_distance_mpc",
        "source_rhi_kpc_anchor","source_mean_sigma_hi_3p2h_anchor","axis_kpc_per_pdf_x","axis_sigma_per_pdf_y",
        "axis_tick_nice_score","helium_applied","frozen_distance_applied","profile_status"
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(output)

    failed=[p["galaxy"] for p in per if (not p["radius_strictly_increasing"] or p["negative_sigma_count"]>0 or p["rhi_crossing_kpc_from_sampled_vector"] is None)]
    summary={
        "status":"ELSON2017_WHISP_VECTOR_PROFILE_CANDIDATES_EXTRACTED",
        "n_galaxies":len(per),
        "n_rows":len(output),
        "role_counts":{
            "calibration":sum(p["stationary_role"]=="calibration" for p in per),
            "blind":sum(p["stationary_role"]=="blind" for p in per),
        },
        "basic_qc_failed_galaxies":failed,
        "max_axis_tick_nice_score":max(p["axis_tick_nice_score"] for p in per),
        "max_rhi_crossing_relative_error":max((p["rhi_crossing_relative_error"] or 0.0) for p in per),
        "profiles":per,
        "interpretation":"Red H I curve geometry is exact vector data from Elson 2017 Appendix PDFs. Physical axes are reconstructed from audited source anchors; this file is a candidate reconstruction and is not yet the final frozen stationary_hi_profiles_v1.csv.",
        "boundary":"Raw H I only. No helium factor, frozen-SPARC distance conversion, common-grid interpolation, persistence fitting, or blind outcome inspection.",
    }
    SUMMARY.parent.mkdir(parents=True,exist_ok=True)
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="profiles"},indent=2))

if __name__=="__main__":
    main()
