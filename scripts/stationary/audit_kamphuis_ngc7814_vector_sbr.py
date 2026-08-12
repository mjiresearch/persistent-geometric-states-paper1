#!/usr/bin/env python3
"""Coordinate-level QC of Kamphuis 2008 NGC7814 Figure 5.1.

The recovered native PDF shows Figure 5.1 as vector content.  Its caption states
that the fitted tilted-ring parameters include SBR (surface brightness), plotted
against radius in arcsec.  This audit extracts text coordinates and vector-path
bounding boxes from the figure page so we can decide whether the SBR panel is a
calibrated H I radial surface-density profile and whether its curve can be
isolated exactly.

No OCR, no raster digitization, no curve inference from pixels, no persistence.
"""
from __future__ import annotations
import hashlib,json,math,urllib.request
from pathlib import Path
import fitz

URL="https://pure.rug.nl/ws/portalfiles/portal/2704953/Pagesfromkamphuisthesis.pdf"
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
OUT=Path("validation/stationary/kamphuis2008_ngc7814_vector_sbr_audit_v1.json")
PAGE_ONE_BASED=85


def ser_point(p):return [round(float(p.x),3),round(float(p.y),3)]
def ser_rect(r):return [round(float(r.x0),3),round(float(r.y0),3),round(float(r.x1),3),round(float(r.y1),3)]

def ser_item(item):
    if not item:return None
    k=item[0]
    vals=[k]
    for x in item[1:]:
        if hasattr(x,"x0") and hasattr(x,"y0"):vals.append({"rect":ser_rect(x)})
        elif hasattr(x,"x") and hasattr(x,"y"):vals.append({"point":ser_point(x)})
        elif isinstance(x,(int,float,str,bool)) or x is None:vals.append(x)
        else:vals.append(str(x)[:200])
    return vals

def main():
    req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
    with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
    if not raw.startswith(b"%PDF-"):raise RuntimeError("not PDF")
    doc=fitz.open(stream=raw,filetype="pdf");page=doc[PAGE_ONE_BASED-1]
    words=[]
    for w in page.get_text("words"):
        x0,y0,x1,y1,text,block,line,word=w[:8]
        words.append({"text":text,"rect":[round(x0,3),round(y0,3),round(x1,3),round(y1,3)],"block":block,"line":line,"word":word})
    drawings=[]
    for d in page.get_drawings():
        items=d.get("items",[])
        drawings.append({
          "rect":ser_rect(d["rect"]),"n_items":len(items),"items":[ser_item(i) for i in items[:500]],
          "color":d.get("color"),"fill":d.get("fill"),"width":d.get("width"),"dashes":d.get("dashes"),
          "closePath":d.get("closePath"),"lineCap":str(d.get("lineCap")),"lineJoin":d.get("lineJoin")
        })
    drawings.sort(key=lambda x:x["n_items"],reverse=True)
    # Text anchors relevant to plot/panel calibration.
    anchors=[w for w in words if any(k.lower() in w["text"].lower() for k in ["SBR","vrot","z0","INCL","PA","radius","arcsec","UGC","0008","Figure","5.1"])]
    numeric_words=[w for w in words if any(ch.isdigit() for ch in w["text"])]
    # Large path objects are the most plausible plotted curves/axes.
    large=[d for d in drawings if d["n_items"]>=5]
    out={
      "status":"KAMPHUIS2008_NGC7814_VECTOR_SBR_AUDIT_COMPLETE",
      "source":"Kamphuis 2008 PhD thesis, Figure 5.1, UGC0008/NGC7814 tilted-ring models",
      "pdf_url":URL,"pdf_bytes":len(raw),"pdf_sha256":hashlib.sha256(raw).hexdigest(),
      "page_number_1based":PAGE_ONE_BASED,"page_rect":ser_rect(page.rect),
      "caption_text":"Figure 5.1 caption identifies vrot, z0, surface brightness (SBR), INCL and PA for each ring, plotted against radius in arcsec.",
      "words":words,"anchor_words":anchors,"numeric_words":numeric_words,
      "n_drawings":len(drawings),"n_large_drawings":len(large),
      "drawings_top_by_item_count":drawings[:300],
      "boundary":"Coordinate/vector audit only. No OCR, raster digitization, pixel inference, physical-unit conversion, persistence fitting, or blind inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"page_rect":out["page_rect"],"anchors":anchors,"n_drawings":len(drawings),"top_drawings":[{"rect":x["rect"],"n_items":x["n_items"],"color":x["color"],"width":x["width"]} for x in drawings[:40]]},indent=2))

if __name__=="__main__":main()
