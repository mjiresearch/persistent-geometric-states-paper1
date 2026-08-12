#!/usr/bin/env python3
"""Try Groningen Pure backend URLs for Verheijen thesis H I vector assets."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from urllib.request import Request, urlopen

BASE_PATH = Path("scripts/stationary/audit_verheijen1997_thesis_hi_vectors.py")
spec = importlib.util.spec_from_file_location("v97base", BASE_PATH)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

OUT = Path("validation/stationary/verheijen1997_pure_backend_vector_audit_v1.json")


def fetch_pdf(url: str) -> bytes:
    req = Request(url, headers={
        "User-Agent": base.UA,
        "Accept": "application/pdf,*/*;q=0.8",
    })
    with urlopen(req, timeout=180) as h:
        return h.read()


def alternatives(url: str) -> list[str]:
    out = [url]
    if "research.rug.nl/files/" in url:
        tail = url.split("research.rug.nl/files/", 1)[1]
        out += [
            "https://pure.rug.nl/ws/portalfiles/portal/" + tail,
            "https://research.rug.nl/files/" + tail + "?download=1",
            "https://pure.rug.nl/ws/portalfiles/portal/" + tail + "?download=1",
        ]
    seen = []
    for u in out:
        if u not in seen:
            seen.append(u)
    return seen


def main():
    with base.PRIORITY.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    target = next(r for r in rows if r["sparc_ref_id"] == "VS01")
    galaxies = target["galaxies"].split(";")

    page = base.fetch(base.PUBLICATION)
    links = base.discover_pdf_links(page)
    attempts = []
    audits = []

    for name in ("c4.pdf", "thesis.pdf"):
        src = links.get(name)
        if not src:
            attempts.append({"document": name, "status": "link_not_found"})
            continue
        for u in alternatives(src):
            rec = {"document": name, "url": u}
            try:
                raw = fetch_pdf(u)
                rec.update({"status": "fetched", "bytes": len(raw), "prefix": raw[:12].hex()})
                if raw[:5] == b"%PDF-":
                    aud = base.audit_pdf(name, u, raw, galaxies)
                    audits.append(aud)
                    rec["status"] = "pdf_audited"
                    attempts.append(rec)
                    break
                attempts.append(rec)
            except Exception as exc:
                rec.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
                attempts.append(rec)

    best = None
    if audits:
        best = max(audits, key=lambda a: (
            a["n_priority_galaxies_found"],
            a["n_with_surface_density_text"],
            a["n_with_long_vector_candidate"],
        ))

    result = {
        "status": "VERHEIJEN1997_PURE_BACKEND_VECTOR_AUDIT_COMPLETE",
        "discovered_links": links,
        "attempts": attempts,
        "audits": audits,
        "best_document": None if best is None else best["document"],
        "best_url": None if best is None else best["url"],
        "best_n_priority_galaxies_found": 0 if best is None else best["n_priority_galaxies_found"],
        "best_n_with_surface_density_text": 0 if best is None else best["n_with_surface_density_text"],
        "best_n_with_long_vector_candidate": 0 if best is None else best["n_with_long_vector_candidate"],
        "route_viable_for_vector_extraction": bool(best and best["n_with_long_vector_candidate"] > 0),
        "boundary": "Backend transport/vector audit only; no raster digitization or persistence fitting.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "audits"}, indent=2))
    for a in audits:
        print("AUDIT", a["document"], a["url"], a["n_priority_galaxies_found"], a["n_with_long_vector_candidate"])


if __name__ == "__main__":
    main()
