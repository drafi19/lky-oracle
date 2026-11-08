"""Measure how the citation word floor changes what survives.

Re-asks the committed eval questions, captures every citation the model
produces, then filters the same set at several word thresholds.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lkybot.answer import SYSTEM, _normalize, _prompt  # noqa: PLC2701
from lkybot.corpus import build_chunks, load_docs
from lkybot.providers import get_provider
from lkybot.retrieve import BM25Index

THRESHOLDS = [6, 8, 10, 12, 15, 20]


def main() -> int:
    index = BM25Index(build_chunks(load_docs()))
    provider = get_provider("gemini")
    questions = [
        json.loads(line)
        for line in Path("eval/questions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = []
    for item in questions:
        if not item["answerable"]:
            continue
        passages = index.search(item["question"], k=5)
        payload = provider.generate_json(SYSTEM, _prompt(item["question"], passages), "{}")
        by_id = {chunk.id: chunk for chunk, _score in passages}
        entries = []
        for raw in payload.get("citations") or []:
            chunk = by_id.get(str(raw.get("chunk_id", "")).strip())
            quote = str(raw.get("quote", "")).strip()
            entries.append(
                {
                    "exact": chunk is not None
                    and _normalize(quote) in _normalize(chunk.text),
                    "words": len(quote.split()),
                }
            )
        rows.append({"id": item["id"], "citations": entries})
        print(f"{item['id']} citations={len(entries)}")

    print("\nthreshold  quotes_pass  items_with_one_valid")
    for threshold in THRESHOLDS:
        total = valid = items_ok = 0
        for row in rows:
            passed = [
                entry
                for entry in row["citations"]
                if entry["exact"] and entry["words"] >= threshold
            ]
            total += len(row["citations"])
            valid += len(passed)
            items_ok += 1 if passed else 0
        print(f"{threshold:>9}  {valid:>10}/{total:<3}  {items_ok:>8}/{len(rows)}")

    Path("eval/threshold_sweep.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    exact = sum(1 for row in rows for entry in row["citations"] if entry["exact"])
    allq = sum(len(row["citations"]) for row in rows)
    print(f"\nexact quotes overall: {exact}/{allq}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
