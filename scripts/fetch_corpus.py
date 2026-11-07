"""Download Lee Kuan Yew speech transcripts from the National Archives of Singapore.

The archive publishes one PDF per speech at a predictable path. This script
downloads the list below, extracts the text, drops documents that came back as
scans without a text layer, and writes corpus/docs.jsonl with provenance.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import httpx
import pymupdf

BASE = "https://www.nas.gov.sg/archivesonline/data/pdfdoc/"
SLUGS = [
    "lky19651015",
    "lky19651108",
    "lky19651211c",
    "lky19670619",
    "lky19700110b",
    "lky19700906b",
    "lky19700909b",
    "lky19700913",
    "lky19700925b",
    "lky19700929",
    "lky19800421",
    "lky19800520a",
    "lky19800628",
    "lky19800815",
    "lky19800922",
    "lky19801113b",
    "lky19801129",
    "lky19900216",
    "lky19900524",
    "lky19900601a",
    "lky19900717",
    "lky19900811",
    "lky19900831",
    "lky19901008",
]

OUT = Path("corpus/docs.jsonl")
MIN_CHARS = 5000
HEADER = re.compile(r"lky[\\/]\d{4}[\\/]lky\d{3,4}[a-zA-Z]?\.(?:doc|DOC)", re.IGNORECASE)
RELEASE = re.compile(r"Release No\.?:?\s*[\w\\.\- ]{0,40}", re.IGNORECASE)
PREFIX = re.compile(r"^(for record\s*[-:]?\s*not for distribution\s*)", re.IGNORECASE)
CODEC = re.compile(r"^[\d\s\\.\-]+(?=[A-Z])")


def clean(text: str) -> str:
    text = text.replace("\x00", " ").replace("\f", "\n")
    text = HEADER.sub("", text)
    text = RELEASE.sub("", text)
    text = re.sub(r"^\s*\d{1,3}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def guess_title(text: str) -> str:
    head = PREFIX.sub("", " ".join(text.split()))
    head = CODEC.sub("", head)
    stop = head.upper().find(" ON ")
    candidate = head[:stop] if 40 < stop < 220 else head[:180]
    return candidate.strip(" ,.-")


def doc_date(slug: str) -> str:
    year, month, day = slug[3:7], slug[7:9], slug[9:11]
    return date(int(year), int(month), int(day)).isoformat()


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    kept: list[dict] = []
    skipped: list[tuple[str, str]] = []

    with httpx.Client(timeout=45.0, follow_redirects=True) as client:
        for slug in SLUGS:
            url = BASE + slug + ".pdf"
            try:
                response = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                doc = pymupdf.open(stream=response.content, filetype="pdf")
                raw = "\n".join(page.get_text() for page in doc)
            except Exception as exc:  # noqa: BLE001
                skipped.append((slug, f"{type(exc).__name__}: {exc}"))
                continue

            text = clean(raw)
            if len(text) < MIN_CHARS:
                skipped.append((slug, f"only {len(text)} characters after cleaning"))
                continue

            kept.append(
                {
                    "id": slug,
                    "title": guess_title(text),
                    "date": doc_date(slug),
                    "source_url": url,
                    "char_count": len(text),
                    "text": text,
                }
            )
            print(f"kept {slug:16} {len(text):>7} chars  {guess_title(text)[:70]}")

    with OUT.open("w", encoding="utf-8") as handle:
        for row in kept:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nkept {len(kept)} documents, {sum(r['char_count'] for r in kept)} characters")
    for slug, reason in skipped:
        print(f"skipped {slug}: {reason}")
    return 0 if len(kept) >= 15 else 1


if __name__ == "__main__":
    raise SystemExit(main())
