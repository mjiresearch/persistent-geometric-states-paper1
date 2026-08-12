#!/usr/bin/env python3
"""Audit two public acquisition routes for the Elson (2017) WHISP profiles.

Routes audited without altering any scientific source convention:
  1. arXiv:1709.03288 source package -- identify Appendix profile figure assets
     and whether they are vector graphics suitable for publication-grade point
     recovery;
  2. legacy wow.astron.nl -- probe live root/access and query the Internet
     Archive CDX index for UGC4325 URLs to recover historical FITS URL patterns.

This is an acquisition audit only. No profile points are extracted and no
persistence quantity is evaluated.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ARXIV_URL = "https://export.arxiv.org/e-print/1709.03288"
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
PROBES = [
    "http://wow.astron.nl/",
    "https://wow.astron.nl/",
    "https://www.astro.rug.nl/~whisp/Database/OverviewCatalog/ListByName/U4325/u4325.html",
]


def get_bytes(url: str, timeout: int = 60) -> tuple[bytes, dict[str, str]]:
    req = Request(url, headers={"User-Agent": "PersistenceFrameworkPaperI/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read(), {k.lower(): v for k, v in resp.headers.items()}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def probe(url: str) -> dict:
    try:
        data, headers = get_bytes(url, timeout=20)
        return {
            "url": url,
            "ok": True,
            "bytes": len(data),
            "content_type": headers.get("content-type", ""),
            "sha256": sha256(data),
            "preview": data[:300].decode("utf-8", errors="replace"),
        }
    except Exception as exc:
        return {"url": url, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def inspect_arxiv() -> dict:
    raw, headers = get_bytes(ARXIV_URL, timeout=90)
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    files = []
    candidate_profiles = []
    tex_hits = []
    for member in tf.getmembers():
        if not member.isfile():
            continue
        suffix = Path(member.name).suffix.lower()
        entry = {"name": member.name, "bytes": member.size, "suffix": suffix}
        files.append(entry)
        lname = member.name.lower()
        if any(t in lname for t in ("append", "profile", "radial", "figa", "fig_a", "whisp")):
            candidate_profiles.append(entry)
        if suffix in {".tex", ".txt"}:
            try:
                txt = tf.extractfile(member).read().decode("utf-8", errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                if re.search(r"includegraphics|appendix|radial profiles|ugc04325|ugc4325", line, re.I):
                    tex_hits.append({"file": member.name, "line": i, "text": line[:500]})

    graphics = [f for f in files if f["suffix"] in {".pdf", ".eps", ".ps", ".svg"}]
    return {
        "arxiv_url": ARXIV_URL,
        "archive_bytes": len(raw),
        "archive_sha256": sha256(raw),
        "content_type": headers.get("content-type", ""),
        "n_files": len(files),
        "n_vector_graphics": len(graphics),
        "vector_graphics": graphics,
        "candidate_profile_assets": candidate_profiles,
        "tex_hits": tex_hits[:200],
    }


def wayback_urls() -> dict:
    queries = [
        "http://wow.astron.nl/*4325*",
        "http://wow.astron.nl/*u4325*",
        "http://wow.astron.nl/*UGC4325*",
    ]
    results = []
    for target in queries:
        params = (
            f"?url={quote(target, safe=':/')}&output=json&fl=timestamp,original,statuscode,mimetype,digest"
            "&filter=statuscode:200&collapse=urlkey&limit=500"
        )
        url = WAYBACK_CDX + params
        try:
            data, _ = get_bytes(url, timeout=60)
            obj = json.loads(data.decode("utf-8"))
            rows = obj[1:] if isinstance(obj, list) and obj else []
            for row in rows:
                if len(row) >= 5:
                    results.append({
                        "query": target,
                        "timestamp": row[0],
                        "original": row[1],
                        "statuscode": row[2],
                        "mimetype": row[3],
                        "digest": row[4],
                    })
        except Exception as exc:
            results.append({"query": target, "error": f"{type(exc).__name__}: {exc}"})
    # Deduplicate originals.
    dedup = {}
    for r in results:
        dedup[r.get("original", json.dumps(r, sort_keys=True))] = r
    vals = list(dedup.values())
    fits_like = [r for r in vals if re.search(r"fits|fit|s30|2dim|cube|mom|hi", r.get("original", ""), re.I)]
    return {"n_unique_urls": len(vals), "urls": vals[:500], "fits_like": fits_like[:300]}


def main() -> None:
    result = {
        "status": "ELSON2017_WHISP_PUBLIC_ROUTE_AUDIT",
        "arxiv": inspect_arxiv(),
        "live_probes": [probe(u) for u in PROBES],
        "wayback": wayback_urls(),
        "boundary": (
            "Acquisition-route audit only. No HI profile samples, orientation parameters, "
            "helium factors, radial conversions, interpolation, persistence parameters, or blind outcomes altered/evaluated."
        ),
    }
    out = Path("validation/stationary/elson2017_whisp_public_route_audit_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
