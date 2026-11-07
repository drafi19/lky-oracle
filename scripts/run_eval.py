"""Run the evaluation set and write eval/results.md.

Retrieval is measured for every question without any model call. Answer quality
is measured on the same questions with a real provider, which costs one call per
question and rate limits apply.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lkybot.answer import ask
from lkybot.corpus import build_chunks, load_docs
from lkybot.providers import get_provider
from lkybot.retrieve import BM25Index

QUESTIONS = Path("eval/questions.jsonl")
RAW = Path("eval/raw.jsonl")
REPORT = Path("eval/results.md")


def load_questions() -> list[dict]:
    return [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="gemini")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--skip-model", action="store_true")
    args = parser.parse_args()

    index = BM25Index(build_chunks(load_docs()))
    questions = load_questions()
    provider = None if args.skip_model else get_provider(args.provider)

    rows = []
    started = time.perf_counter()
    for item in questions:
        hits = index.search(item["question"], k=args.k)
        doc_ids = [chunk.doc_id for chunk, _score in hits]
        hit = any(doc in doc_ids for doc in item["expected_docs"])
        row = {
            "id": item["id"],
            "question": item["question"],
            "answerable": item["answerable"],
            "expected_docs": item["expected_docs"],
            "retrieved_docs": doc_ids,
            "retrieval_hit": hit,
        }
        if provider is not None:
            result = ask(item["question"], index, provider, k=args.k)
            row.update(
                {
                    "refused": result.refused,
                    "citations": len(result.citations),
                    "invalid_citations": result.invalid_citations,
                    "latency_s": round(result.latency_s, 2),
                    "answer": result.text,
                }
            )
        rows.append(row)
        print(f"{row['id']} hit={hit} refused={row.get('refused')} cites={row.get('citations')}")

    RAW.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    answerable = [r for r in rows if r["answerable"]]
    unanswerable = [r for r in rows if not r["answerable"]]
    recall = sum(r["retrieval_hit"] for r in answerable) / max(1, len(answerable))

    lines = ["# Evaluation results", ""]
    lines.append(f"Corpus: {len(index.chunks)} chunks from {len({c.doc_id for c in index.chunks})} speeches.")
    lines.append(f"Questions: {len(answerable)} answerable, {len(unanswerable)} out of corpus.")
    lines.append(f"Retrieval: BM25, top {args.k}.")
    lines.append("")
    lines.append(f"**Recall@5 on answerable questions: {recall:.2f}** ({sum(r['retrieval_hit'] for r in answerable)}/{len(answerable)})")
    lines.append("")

    if provider is not None:
        cited = sum(1 for r in answerable if r.get("citations", 0) > 0)
        refused_ok = sum(1 for r in unanswerable if r.get("refused"))
        falsely_refused = sum(1 for r in answerable if r.get("refused"))
        wrong_cites = sum(r.get("invalid_citations", 0) for r in answerable)
        latencies = [r["latency_s"] for r in rows if "latency_s" in r]
        lines.append(f"**Answers with at least one verified citation: {cited}/{len(answerable)}**")
        lines.append("")
        lines.append(f"**Correct refusals on out-of-corpus questions: {refused_ok}/{len(unanswerable)}**")
        lines.append("")
        lines.append(f"Refused despite a matching speech: {falsely_refused}/{len(answerable)}")
        lines.append("")
        lines.append(f"Citations rejected by the substring check: {wrong_cites}")
        lines.append("")
        if latencies:
            lines.append(
                f"Median answer time: {statistics.median(latencies):.1f}s "
                f"(max {max(latencies):.1f}s)"
            )
        lines.append("")

    lines.append("| id | question | expected | retrieved | hit | refused | cites |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['question'][:60]} | {', '.join(row['expected_docs']) or '-'} | "
            f"{', '.join(row['retrieved_docs'][:3])} | {row['retrieval_hit']} | "
            f"{row.get('refused', '-')} | {row.get('citations', '-')} |"
        )

    lines.append("")
    lines.append(f"Total runtime: {time.perf_counter() - started:.0f}s")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {REPORT} in {time.perf_counter() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
