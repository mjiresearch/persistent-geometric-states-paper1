#!/usr/bin/env python3
"""Bounded recovery of the Swaters 2002 full WHISP-I atlas.

Tries the paper's live HTTP/HTTPS URL once each, then the Internet Archive
Availability API and CDX index for the exact historical filename.  If a valid
archived gzip is recovered, inventory it without extracting scientific profile
coordinates.  Acquisition/provenance only; no blind outcomes or persistence fit.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

UA = "PersistenceFrameworkPaperI/1.0"
ORIGINAL = "http://www.robswork.net/publications/WHISPI.ps.gz"
HTTPS = "https://www.robswork.net/publications/WHISPI.ps.gz"
AVAILABLE = "https://archive.org/wayback/available?url=" + quote(ORIGINAL, safe="")
CDX = (
    "https://web.archive.org/cdx/search/cdx?url=" + quote(ORIGINAL, safe="")
    + "&output=json&filter=statuscode:200&filter=collapse:digest&fl=timestamp,original,mimetype,statuscode,digest,length&limit=50"
)
OUT = Path("validation/stationary/sw02_full_atlas_wayback_recovery_v1.json")


def fetch(url: str, timeout=120) -> tuple[bytes, str, str]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urlopen(req, timeout=timeout) as h:
        return h.read(), h.geturl(), h.headers.get("Content-Type", "")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def classify_payload(raw: bytes) -> dict:
    rec = {"bytes": len(raw), "sha256": sha256(raw), "prefix_hex": raw[:24].hex()}
    try:
        ps = gzip.decompress(raw)
        rec.update({
            "gzip_valid": True,
            "decompressed_bytes": len(ps),
            "decompressed_sha256": sha256(ps),
            "postscript_header": ps[:16].decode("latin-1", "replace"),
            "postscript_like": ps.startswith(b"%!") or b"%!PS" in ps[:128],
            "showpage_count": ps.count(b"showpage"),
            "image_operator_count": ps.count(b" image") + ps.count(b"\nimage"),
            "colorimage_operator_count": ps.count(b"colorimage"),
            "imagemask_operator_count": ps.count(b"imagemask"),
            "moveto_literal_count": ps.count(b"moveto"),
            "lineto_literal_count": ps.count(b"lineto"),
        })
    except Exception as exc:
        rec.update({"gzip_valid": False, "gzip_error": f"{type(exc).__name__}: {exc}"})
    return rec


def main() -> None:
    attempts = []
    recovered = None

    for label, url in (("live_http", ORIGINAL), ("live_https", HTTPS)):
        rec = {"route": label, "url": url}
        try:
            raw, final, ct = fetch(url, timeout=45)
            rec.update({"status": "fetched", "final_url": final, "content_type": ct, **classify_payload(raw)})
            if rec.get("gzip_valid") and rec.get("postscript_like"):
                recovered = {"route": label, "url": final, "raw": raw, "classification": rec}
                attempts.append(rec)
                break
        except Exception as exc:
            rec.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)

    availability = None
    cdx_rows = []
    if recovered is None:
        try:
            raw, final, ct = fetch(AVAILABLE, timeout=45)
            availability = json.loads(raw.decode("utf-8", "replace"))
        except Exception as exc:
            availability = {"error": f"{type(exc).__name__}: {exc}"}

        try:
            raw, final, ct = fetch(CDX, timeout=60)
            table = json.loads(raw.decode("utf-8", "replace"))
            if isinstance(table, list) and len(table) > 1:
                header = table[0]
                cdx_rows = [dict(zip(header, row)) for row in table[1:]]
        except Exception as exc:
            cdx_rows = [{"error": f"{type(exc).__name__}: {exc}"}]

        candidates = []
        closest = None
        if isinstance(availability, dict):
            closest = availability.get("archived_snapshots", {}).get("closest")
            if closest and closest.get("available") and closest.get("url"):
                candidates.append(("wayback_available", closest["url"]))
        for row in reversed(cdx_rows):
            ts = row.get("timestamp")
            orig = row.get("original") or ORIGINAL
            if ts:
                candidates.append(("wayback_cdx", f"https://web.archive.org/web/{ts}id_/{orig}"))

        seen = set()
        for label, url in candidates[:12]:
            if url in seen:
                continue
            seen.add(url)
            rec = {"route": label, "url": url}
            try:
                raw, final, ct = fetch(url, timeout=120)
                rec.update({"status": "fetched", "final_url": final, "content_type": ct, **classify_payload(raw)})
                attempts.append(rec)
                if rec.get("gzip_valid") and rec.get("postscript_like"):
                    recovered = {"route": label, "url": final, "raw": raw, "classification": rec}
                    break
            except Exception as exc:
                rec.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
                attempts.append(rec)

    result = {
        "status": "SW02_FULL_ATLAS_WAYBACK_RECOVERY_COMPLETE",
        "historical_url": ORIGINAL,
        "https_variant": HTTPS,
        "availability_api": availability,
        "cdx_rows": cdx_rows,
        "attempts": attempts,
        "recovered": recovered is not None,
        "recovered_route": None if recovered is None else recovered["route"],
        "recovered_url": None if recovered is None else recovered["url"],
        "recovered_classification": None if recovered is None else recovered["classification"],
        "boundary": (
            "Transport/provenance recovery only. Even a recovered atlas is not a promoted source profile "
            "until galaxy identity, bottom-left radial profile panel, axes, quantity, and curve geometry pass QC."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
