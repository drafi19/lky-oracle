# LKY Oracle

A retrieval-grounded chatbot that answers questions in the voice of Lee Kuan Yew. It reads 19 transcripts of his speeches and press conferences from the National Archives of Singapore, retrieves the passages that match a question, and answers using only those passages. Every answer carries citations that are checked as verbatim substrings of the cited speech. An answer with no verifiable citation is returned as a refusal.

The point is not to imitate a voice. The point is to make the imitation auditable.

## What it does

- The user asks anything: independence, geopolitics, language policy, housing, welfare.
- BM25 retrieves the five closest chunks from 367 chunks across 19 speeches.
- The model writes two to four short paragraphs in the first person, with one to three citations.
- The app verifies each citation: the chunk must exist among the retrieved passages, and the quoted span must appear in that chunk after whitespace and quote normalisation.
- If no citation survives, the answer is replaced by a refusal. The app fails closed, not open.

## The corpus

| Source | Count | Note |
|---|---|---|
| National Archives of Singapore, speech transcripts | 19 documents | 247,934 characters, 1965 to 1990 |
| Skipped during fetch | 5 documents | Under 5,000 characters after cleaning, mostly short press statements |

`scripts/fetch_corpus.py` downloads the PDFs, extracts the text, strips archive file codes and release numbers, and writes `corpus/docs.jsonl` with the title, date, and source URL for each speech. Re-running it reproduces the corpus. Only public government transcripts are used. No memoir text is copied, and the project is a non-commercial assessment demo.

## How it works

```text
corpus/docs.jsonl
      |
      v
chunking on sentence boundaries, 900 characters, 150 overlap   -> 367 chunks
      |
      v
BM25 index (offline, no embedding model, no API key)
      |
      v
question -> top 5 chunks -> persona prompt with the passages
      |
      v
model answer + citations -> substring check per citation
      |
      +-- all citations fail --> refusal
      |
      v
answer + sources panel (title, date, archive link, quote)
```

Chunking keeps the sentence boundary so a quote never starts mid-word. The chunk id encodes the speech and the position, for example `lky19651108:004`, which is what the citation check uses to find the text the model claims to quote.

## The answer contract

The system prompt gives the model three rules that matter: use only the passages, copy at least 12 words verbatim for each citation, and refuse when the passages do not answer the question. The model is allowed to answer part of a question and say what the record does not cover.

The code then checks the citations independently:

1. The cited chunk id must be one of the five passages that were actually retrieved for this question.
2. The quote must be at least 12 words.
3. The normalised quote must be a substring of the normalised chunk text.

If zero citations survive, `refused` is set to true and the app shows a warning. Two citations were rejected by this check during the committed evaluation run, which is exactly the point: the model produces quotes that look right but are not always exact, and the code catches them.

## Evaluation

`eval/questions.jsonl` holds 15 questions that the archive can answer and 5 that it cannot, such as Bitcoin, the 2024 US election, and ChatGPT. `scripts/run_eval.py` retrieves for every question and can run the full answer path with a real provider.

Results from the committed run on 7 November 2026, Gemini `gemini-3.1-flash-lite`, top 5 passages:

| Metric | Result |
|---|---|
| Recall@5 on answerable questions | 15/15 (1.00) |
| Answers with at least one verified citation | 15/15 |
| Correct refusals on out-of-corpus questions | 4/5 |
| Refused despite a matching speech | 0/15 |
| Citations rejected by the substring check | 2 |
| Median answer time | 1.6s (max 23.0s) |

Read that table with its limits in mind. The answerable questions are event-anchored, for example "What did you say at the opening of Everton Park housing estate", so recall@5 measures whether lookup works, not whether the system understands a paraphrase. BM25 has no stemming and no semantics, and a question phrased entirely in different words can miss. One out-of-corpus question, the one about ChatGPT, was answered instead of refused: the retriever found a passage about technology and the model chose to engage instead of declining. That failure is left in the results because deleting it would make the refusal metric look better than the system is.

Re-run it yourself:

```bash
uv run python scripts/run_eval.py --skip-model      # retrieval only, no API key
uv run python scripts/run_eval.py --provider gemini # full answer path
```

## Model choice

The answer model is Gemini `gemini-3.1-flash-lite`. A question costs one model call, so the free tier is enough for a demo, and the model is fast enough that the median answer time stays under two seconds. Two earlier defaults failed in practice: `gemini-2.5-flash` is rejected for new API keys, and `gemini-3-flash-preview` allows only five requests per minute on the free tier, which is tight when an evaluation run fires twenty calls in a row. The provider layer is one method, `generate_json(system, user, schema_hint) -> dict`, so the answer model can be swapped without touching retrieval. OpenRouter and CommandCode are included as alternatives.

Retrieval makes no model calls at all. That is deliberate: the part that decides which evidence is admissible should not depend on the thing being judged.

## What broke

- **BM25 has no stemming.** The query "why separate" returned nothing because the corpus says "separated" and "separation". The test suite caught it, the test queries were rewritten, and the limitation is now stated in the evaluation section instead of being hidden by a lucky query.
- **Editable install failed.** `uv pip install -e .` needs a build backend, and the project had no `[build-system]`. Instead of adding packaging scaffolding for a single app, tests use `pythonpath = ["."]` and dependencies are installed directly.
- **Archive codes leaked into citations.** Several 1990 PDFs start with release codes such as `02-1\90\07\17`, which became the speech title and then appeared in the sources panel. A cleanup regex strips leading codes, and the corpus was re-fetched.
- **Package rename broke the imports.** The provider modules were copied from another project and still imported `fondasi.config`, which does not exist here. Test collection failed immediately, which is the cheapest place to find it.
- **The first chat loop stored answers as dictionaries** and rendered them with `Answer(**entry["answer$"])`, a typo that crashed the history view. Answers are now stored as dataclasses and rendered from the object.

## Limitations

- Retrieval is keyword-based. A question that shares no vocabulary with the speeches will miss, even when the answer is there in different words.
- The corpus is 19 speeches. It is not the complete record, so a refusal can mean "not in these 19 documents" rather than "never said".
- The persona is a style prompt, not a fine-tune. It imitates register and argument, not the man.
- The model can still quote accurately out of context. The substring check proves provenance, not fairness.
- No conversation memory beyond the visible history. Each question is answered independently.

## Next changes

- Add stemming or a small embedding index and report recall for both, so the paraphrase gap becomes a measured number instead of a caveat.
- Add a contradiction check: when two retrieved passages disagree, surface both instead of letting the model pick one.
- Grow the corpus by decade and report recall per decade, so thin periods are visible.
- Cache answers for repeated questions, since the same demo questions get asked often.

## Run locally

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt pytest ruff pymupdf
uv run python scripts/fetch_corpus.py          # writes corpus/docs.jsonl
uv run pytest -q
uv run streamlit run streamlit_app.py
```

The app starts in demo mode, which returns the top retrieved passage verbatim and makes no model call, so it works without a key. To use a real model, set `GEMINI_API_KEY` and pick the provider in the sidebar.

## Decisions I made alone

- BM25 over embeddings, because it needs no key, costs nothing per query, and makes the retrieval metric reproducible offline.
- Fail closed on citations: an answer without a verifiable quote becomes a refusal, even if the prose looks fine.
- Keep the out-of-corpus failure in the results table instead of tuning the eval set until the number looked clean.
- Event-anchored questions in the eval set, because they let retrieval be measured without a human grading each answer. The limitation is documented rather than hidden.
- Demo mode returns an extract, not a generated answer, and labels itself as such in the reply.
