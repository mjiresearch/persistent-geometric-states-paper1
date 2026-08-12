#!/usr/bin/env python3
"""Inspect the public Iorio et al. (2017) LITTLE THINGS supplement.

This script downloads the OUP supporting-material ZIP and records only a
manifest of archive members plus names matching DDO168. It does not commit the
publisher's full supplementary archive. The next ingestion step can then target
only the Paper-I-relevant numerical source file with provenance.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

# Public OUP supplementary-data link exposed by the article's Supporting
# Information section. The signed query is publisher-generated and public.
SUPPLEMENT_URL = "https://oup.silverchair-cdn.com/oup/backfile/Content_public/Journal/mnras/466/4/10.1093_mnras_stw3285/7/stw3285_Supplementary_Data.zip?Expires=2147483647&Key-Pair-Id=APKAIE5G5CRDK6RD3PGA&Signature=03skimALbafA23r-3ex-zWS2bc89EIZgd~sFBft28yRY0BnMlCp8ERTZ3MfyBPPnBRY14PZDhsjv10pbLm2iDQDCe6AJtwVgTgDUg5SK6OhehqDxnaGr7-Qw3qPTW9v4KLuSEWWSd4NZ3porWPOhEqrgkqApYuKdB0td17fIQ8umbOYSWDbxCc9iG8k~vEsJqEMhdo5Iy9Ims5KLMyczUekMCXBYckdRj~1yjHgRWBqUEK2aUXpKftOxgPC46hAh4xo6tndQWeu55bXUWRNWG5l~~oqqOQse6D0NjdYTNVzS8Bif1uu8LbdyV~rcCJSa7Vyu5bE-sE3SPvb133JWnw__"
ARTICLE_DOI = "10.1093/mnras/stw3285"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "PersistenceFrameworkPaperI/1.0"})
    with urlopen(req, timeout=90) as resp:
        return resp.read()


def inspect_zip(data: bytes, prefix: str = "") -> tuple[list[dict], list[dict]]:
    members: list[dict] = []
    matches: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            name = prefix + info.filename
            rec = {
                "path": name,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "is_dir": info.is_dir(),
            }
            members.append(rec)
            low = info.filename.lower().replace(" ", "")
            if "ddo168" in low or "ddo_168" in low or "ddo-168" in low:
                matches.append(rec)
            if not info.is_dir() and info.filename.lower().endswith(".zip"):
                nested = zf.read(info.filename)
                nested_members, nested_matches = inspect_zip(
                    nested, prefix=name + "::"
                )
                members.extend(nested_members)
                matches.extend(nested_matches)
    return members, matches


def main() -> None:
    data = download(SUPPLEMENT_URL)
    members, matches = inspect_zip(data)
    manifest = {
        "status": "PUBLIC_SUPPLEMENT_INSPECTED",
        "article_doi": ARTICLE_DOI,
        "outer_zip_sha256": sha256_bytes(data),
        "outer_zip_bytes": len(data),
        "n_recursive_members": len(members),
        "ddo168_name_matches": matches,
        "members": members,
        "boundary": (
            "Only archive metadata is committed at this stage; the full publisher "
            "supplement is not redistributed. Numerical DDO168 source data will be "
            "extracted selectively only after the relevant member is identified."
        ),
    }
    out = Path("validation/stationary/iorio2017_supplement_manifest_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
