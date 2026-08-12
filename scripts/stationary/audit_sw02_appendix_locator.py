#!/usr/bin/env python3
"""Recover Swaters et al. 2002 Appendix-B public locator from arXiv source.

One bounded pass: extract the exact surrounding TeX, all embedded URLs, all
Appendix-B figure references, and probe discovered HTTP(S) assets. No profile
coordinates are extracted here.
"""
from __future__ import annotations

import io
import json
import re
import tarfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ARXIV = "https://export.arxiv.org/e-print/astro-ph/0204525"
UA = "PersistenceFrameworkPaperI/1.0"
OUT = Path("validation/stationary/sw02_appendix_locator_audit_v1.json")


def fetch(url: str, timeout=90):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as h:
        return h.read(), h.geturl(), h.headers.get("Content-Type", "")


def main():
    raw, _, _ = fetch(ARXIV)
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    tex_member = next(m for m in tf.getmembers() if m.isfile() and m.name.endswith(".tex"))
    tex = tf.extractfile(tex_member).read().decode("latin-1", "ignore")
    lines = tex.splitlines()

    context = [
        {"line": i + 1, "text": lines[i]}
        for i in range(max(0, 1435), min(len(lines), 1535))
    ]

    urls = []
    for pat in (
        r"https?://[^\s{}\\]+",
        r"www\.[^\s{}\\]+",
    ):
        for m in re.finditer(pat, tex, re.I):
            u = m.group(0).rstrip(".,;)")
            if u.startswith("www."):
                u = "http://" + u
            if u not in urls:
                urls.append(u)

    fig_refs = []
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r"includegraphics\{([^}]+)\}", line):
            name = m.group(1)
            if re.match(r"h3074f(?:1[3-9]|[2-9][0-9])\.ps$", name, re.I):
                fig_refs.append({"line": i, "name": name, "commented": line.lstrip().startswith("%")})

    members = {m.name for m in tf.getmembers() if m.isfile()}
    missing_refs = [r for r in fig_refs if r["name"] not in members]

    probes = []
    for u in urls:
        rec = {"url": u}
        try:
            data, final, ct = fetch(u, timeout=30)
            rec.update({
                "status": "fetched",
                "final_url": final,
                "content_type": ct,
                "bytes": len(data),
                "prefix_hex": data[:16].hex(),
            })
        except Exception as exc:
            rec.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        probes.append(rec)

    result = {
        "status": "SW02_APPENDIX_LOCATOR_AUDIT_COMPLETE",
        "source": "Swaters et al. 2002 A&A 390 829; arXiv astro-ph/0204525",
        "tex_file": tex_member.name,
        "appendix_context_lines_1436_1535": context,
        "embedded_urls": urls,
        "url_probes": probes,
        "appendix_figure_refs_13plus": fig_refs,
        "n_appendix_figure_refs_13plus": len(fig_refs),
        "n_missing_from_arxiv_bundle": len(missing_refs),
        "missing_from_arxiv_bundle": missing_refs,
        "interpretation_boundary": (
            "Locator/transport audit only. Missing atlas figures are not treated as absent science; "
            "they are absent from the arXiv bundle unless a separate public locator succeeds."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "embedded_urls": urls,
        "n_appendix_figure_refs_13plus": len(fig_refs),
        "n_missing_from_arxiv_bundle": len(missing_refs),
        "first_context": context[:20],
        "url_probes": probes,
    }, indent=2))


if __name__ == "__main__":
    main()
