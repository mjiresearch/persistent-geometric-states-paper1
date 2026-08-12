#!/usr/bin/env python3
"""Audit the public Barbieri et al. (2005; Ba05) NGC4559 H I radial-profile route.

This is acquisition/provenance work only. It fetches the public arXiv source,
locates Figure 3 and inventories native figure structure so that a later step can
recover the published radial H I profile without raster digitization if possible.
It does not alter the frozen sample, source normalization, or persistence model.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV_ID = "astro-ph/0504534"
URLS = [
    f"https://arxiv.org/e-print/{ARXIV_ID}",
    f"https://export.arxiv.org/e-print/{ARXIV_ID}",
]
OUT_JSON = Path("validation/stationary/ba05_ngc4559_hi_profile_audit_v1.json")
OUT_TXT = Path("validation/stationary/ba05_ngc4559_source_inventory_v1.txt")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch() -> tuple[bytes, str, str]:
    err = None
    for url in URLS:
        try:
            req = Request(url, headers={"User-Agent": "PaperI-public-source-audit/1.0"})
            with urlopen(req, timeout=60) as r:
                return r.read(), r.geturl(), r.headers.get_content_type()
        except Exception as e:
            err = repr(e)
    raise RuntimeError(f"Unable to fetch public arXiv source: {err}")


def unpack(payload: bytes) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    bio = io.BytesIO(payload)
    try:
        with tarfile.open(fileobj=bio, mode="r:*") as tf:
            for m in tf.getmembers():
                if m.isfile():
                    f = tf.extractfile(m)
                    if f is not None:
                        files[m.name] = f.read()
            return files
    except tarfile.ReadError:
        # A rare single-file source submission. Keep it auditable rather than fail.
        files["submission_source"] = payload
        return files


def decode(b: bytes) -> str:
    return b.decode("latin-1", errors="replace")


def figure_context(tex_name: str, text: str) -> list[dict]:
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        low = line.lower()
        if "fig" in low and ("3" in low or "radial" in low or "column" in low or "density" in low):
            lo, hi = max(0, i - 5), min(len(lines), i + 8)
            ctx = "\n".join(f"{j+1}: {lines[j]}" for j in range(lo, hi))
            if any(k in ctx.lower() for k in ["figure 3", "fig. 3", "fig3", "radial", "column density"]):
                hits.append({"tex_file": tex_name, "line": i + 1, "context": ctx})
    # de-duplicate heavily overlapping contexts
    out=[]
    seen=set()
    for h in hits:
        key=(h['tex_file'], h['context'])
        if key not in seen:
            seen.add(key); out.append(h)
    return out[:40]


def inspect_eps(name: str, b: bytes) -> dict:
    t = decode(b)
    # PostScript/EPS vector primitives and raster operators.
    ops = {
        "image": len(re.findall(r"(?<![A-Za-z])image(?![A-Za-z])", t)),
        "colorimage": len(re.findall(r"(?<![A-Za-z])colorimage(?![A-Za-z])", t)),
        "moveto": len(re.findall(r"(?<![A-Za-z])moveto(?![A-Za-z])", t)),
        "lineto": len(re.findall(r"(?<![A-Za-z])lineto(?![A-Za-z])", t)),
        "arc": len(re.findall(r"(?<![A-Za-z])arc(?![A-Za-z])", t)),
        "show": len(re.findall(r"(?<![A-Za-z])show(?![A-Za-z])", t)),
    }
    strings = re.findall(r"\(([^()]{1,120})\)\s*(?:show|[A-Za-z]*show)", t)
    interesting = []
    for s in strings:
        if re.search(r"H\s*I|HI|kpc|arcsec|pc|M.?sun|Sigma|density|column|radius|R\b|10\^", s, re.I):
            interesting.append(s)
    return {
        "name": name,
        "bytes": len(b),
        "sha256": sha256(b),
        "header": t[:800],
        "ops": ops,
        "native_vector_candidate": (ops["image"] == 0 and ops["colorimage"] == 0 and (ops["lineto"] + ops["arc"] + ops["show"]) > 0),
        "interesting_strings": interesting[:80],
        "begin_document": re.findall(r"%%BeginDocument:\s*([^\r\n]+)", t)[:40],
    }


def main() -> None:
    payload, final_url, content_type = fetch()
    files = unpack(payload)
    tex = {n: decode(b) for n,b in files.items() if n.lower().endswith((".tex", ".ltx")) or n == "submission_source"}
    contexts=[]
    for n,t in tex.items():
        contexts.extend(figure_context(n,t))

    # Collect graphics references explicitly mentioned near Figure 3.
    refs=[]
    pat = re.compile(r"\\(?:includegraphics|epsfig|plotone|plottwo)\s*(?:\[[^\]]*\])?\s*\{?([^}\s,]+)")
    for c in contexts:
        for m in pat.finditer(c["context"]):
            refs.append(m.group(1).strip())
    refs=list(dict.fromkeys(refs))

    graphical = {n:b for n,b in files.items() if n.lower().endswith((".eps", ".ps", ".eps.gz", ".pdf"))}
    # Rank likely Figure-3 candidates by filename/ref match, then inventory all manageable EPS/PS files.
    candidate_names=[]
    for r in refs:
        stem=Path(r).name
        for n in graphical:
            if n == r or Path(n).name == stem or Path(n).stem == Path(stem).stem:
                candidate_names.append(n)
    for n in graphical:
        if re.search(r"(^|[/_.-])(?:fig)?0?3([/_.-]|$)|rad|dens|prof", n, re.I):
            candidate_names.append(n)
    candidate_names=list(dict.fromkeys(candidate_names))

    inspected=[]
    for n,b in graphical.items():
        if n.lower().endswith((".eps", ".ps")) and len(b) <= 20_000_000:
            d=inspect_eps(n,b)
            d["figure3_candidate"] = n in candidate_names
            inspected.append(d)

    inventory = []
    for n,b in sorted(files.items()):
        inventory.append({"name":n,"bytes":len(b),"sha256":sha256(b)})

    result = {
        "status": "BA05_PUBLIC_SOURCE_PROFILE_AUDIT_COMPLETE",
        "sparc_ref_id": "Ba05",
        "galaxy": "NGC4559",
        "stationary_role": "calibration",
        "source": "Barbieri et al. 2005 A&A 439 947; arXiv:astro-ph/0504534",
        "source_title": "Extra-planar gas in the spiral galaxy NGC 4559",
        "public_source_url": final_url,
        "source_content_type": content_type,
        "source_bytes": len(payload),
        "source_sha256": sha256(payload),
        "n_source_files": len(files),
        "scientific_profile_statement": {
            "quantity": "radial H I column-density profile",
            "method": "averaging observed H I column densities in ellipses using the kinematic position/inclination angles",
            "figure": "Figure 3 right panel",
            "helium": "Figure 3 is H I; Appendix A states gas column density for mass modelling is obtained by multiplying H I density by 1.4 for helium",
            "source_distance_mpc": 9.7,
            "source_inclination_deg": 67.2,
            "source_scale": "1 arcmin = 2.8 kpc",
        },
        "figure3_contexts": contexts,
        "graphics_references_near_context": refs,
        "figure3_candidate_files": candidate_names,
        "graphics_inspection": inspected,
        "file_inventory": inventory,
        "next_action": "If Figure 3 radial-profile panel is native vector, isolate its data series and calibrate axes from native labels/ticks; otherwise disposition as public direct profile with exact vector/numeric route unavailable and move on without raster digitization.",
        "locks": ["L_A", "C_A"],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines=[
        "Ba05 / NGC4559 public source inventory",
        f"source={result['source']}",
        f"url={final_url}",
        f"content_type={content_type}",
        f"bytes={len(payload)}",
        f"sha256={result['source_sha256']}",
        f"n_files={len(files)}",
        "",
        "Figure-3 references/context:",
    ]
    for c in contexts:
        lines.append(f"--- {c['tex_file']} line {c['line']} ---")
        lines.append(c['context'])
    lines += ["", "Candidate graphics:"] + candidate_names
    lines += ["", "EPS/PS structure:"]
    for d in inspected:
        lines.append(json.dumps({k:d[k] for k in ['name','bytes','sha256','ops','native_vector_candidate','figure3_candidate','begin_document','interesting_strings']}, ensure_ascii=False))
    lines += ["", "Full file inventory:"]
    for x in inventory:
        lines.append(f"{x['bytes']:>10}  {x['sha256']}  {x['name']}")
    OUT_TXT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "n_source_files": len(files),
        "figure3_candidates": candidate_names,
        "native_vector_candidates": [d['name'] for d in inspected if d['figure3_candidate'] and d['native_vector_candidate']],
        "outputs": [str(OUT_JSON),str(OUT_TXT)],
    }, indent=2))

if __name__ == "__main__":
    main()
