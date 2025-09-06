# Personal RAG Copilot — PRD v1.1 (Additions Integrated)

---

## 1) Product Strategy deltas

* **Retrieval robustness & control.** Ship **hybrid** (dense + lexical) with **RRF** rank fusion as the default, but make both the **fusion behavior** and **reranking** **user-tunable** at query time. Elastic/Milvus document RRF with a common default of **k=60**; we’ll adopt that and allow per-query overrides. ([Elastic][1], [Milvus][2], [Milvus Blog][3])
* **UX transparency.** Surface which hits came from **dense** vs **lexical** and how fusion/rerank changed ordering (badges + per-stage scores). \[Inference]
* **QA you can trust.** Add an **Evaluate** tab that runs **faithfulness** (and related) checks on the last turn using **Ragas** (commonly defined as proportion of answer claims supported by retrieved context). ([Ragas][4], [Pinecone][5])
* **Gradio 5 multipage.** Split app into **Chat**, **Ingest**, **Evaluate**, **Settings** using official **Multipage** routing APIs. ([Gradio][6])

---

## 2) Functional Requirements (new/updated)

### 2.1 Retrieval Modes (updated)

* **Modes:** `lexical | dense | hybrid` (default **hybrid**).

  * **Dense:** Sentence-Transformers **all-MiniLM-L6-v2** (**384-dim**). Ensure Pinecone index dimension = 384 and metric = cosine. ([Hugging Face][7])
  * **Lexical:** in-process BM25 (`rank-bm25` for simplicity; `bm25s` for speed via sparse matrices). ([PyPI][8], [BM25S][9])
  * **(Optional, later)** Use Pinecone’s **hybrid** pattern with **separate dense + sparse indexes** and combine results client-side. ([Pinecone Docs][10])

### 2.2 RRF-with-Awareness (new)

* **Fusion:** Apply **Reciprocal Rank Fusion** across dense and lexical lists with **k=60** default; allow `k` to be set per query. (RRF is officially documented in Elastic/Milvus; both cite k≥1, default **60**.) ([Elastic][1], [Milvus][2])
* **\[Inference] Dynamic weighting:** Detect “rare-token” queries (e.g., codes, IDs, long proper nouns) and **bias toward lexical** by lowering `k` for the lexical list and/or applying a small weight $`w_lexical > w_dense`$. For broad/natural queries, move the weight toward dense.
* **Audit output:** Return per-retriever ranks, fused score components, and the final order. (Developer toggle to log the full rank table.)

### 2.3 Toggleable Reranking (new)

* **Control:** UI switch **“Rerank top-K”** (default off). When on, rerank the top 20 retrieved chunks to a final 5 using **BGE-Reranker-v2-m3** (≈**568M** params; strong cross-encoder). ([Hugging Face][11])
* **\[Inference] Performance policy:** CPU-only laptop → only apply on demand; show ETA hint; cache embeddings for the 20 candidates within a session.

### 2.4 Hybrid Transparency (new)

* **Badges:** Each citation shows its **origin**: `DENSE`, `LEXICAL`, or `FUSED`.
* **Details drawer:** For any answer, an expandable table lists **(rank, score, retriever, snippet)**. \[Inference]

### 2.5 Multipage “Ops” in Gradio 5 (new)

* **Pages:** `Chat` (default), `Ingest`, `Evaluate`, `Settings`. Implement via **`Blocks.route()`** for clean URLs & navbar. ([Gradio][6])
* **Streaming:** Chat callbacks **return/yield** partial tokens for perceived speed (supported in `ChatInterface`). ([Gradio][12])

### 2.6 Built-in Retrieval QA (new)

* **Metrics:** Run **Faithfulness** (answer claims supported by retrieved context; 0–1) and optionally Answer Relevancy/Context Precision via **Ragas**. ([Ragas][4], [Pinecone][5])
* **Flow:** From the last turn, pass `(question, answer, contexts)` to Ragas; render scores & a short rationale.
* **\[Inference] Guardrails:** If faithfulness < threshold (e.g., 0.7), flag the turn and suggest “Expand top-K” or “Rerank”.

---

## 3) Acceptance Criteria (additions)

* **AC-RRF-01 (Fusion Correctness):** With `retrieval_mode=hybrid` and `k=60`, the API returns (a) fused ranking and (b) **per-retriever** ranks/scores for each returned chunk; changing `k` measurably changes ordering on a seeded test. (RRF `k` behavior matches Elastic/Milvus docs.) ([Elastic][1], [Milvus][2])
* **AC-RRF-02 (Awareness Heuristic):** For queries matching **rare-token** regex `[A-Z]{2,}\\-?\\d+` or idf-heavy terms, lexical weight increases (documented in response metadata as `rrf_weights`). \[Inference]
* **AC-HYB-01 (Transparency):** The UI shows a **badge** per citation (`DENSE|LEXICAL|FUSED`) and a **details drawer** listing `(rank, retriever, score, snippet)`. \[Inference]
* **AC-RER-01 (Toggle):** With **Rerank** off, fused results go straight to LLM; with **Rerank** on, top-20 are reranked using **BGE-Reranker-v2-m3** to a final 5; latency overhead is displayed. ([Hugging Face][11])
* **AC-MP-01 (Multipage):** The app exposes four routes using **`Blocks.route()`** with a navbar: `/` Chat, `/ingest`, `/evaluate`, `/settings`. ([Gradio][6])
* **AC-EVAL-01 (Faithfulness):** The **Evaluate** page computes **Faithfulness** per Ragas definition (fraction of answer claims supported by context ∈\[0,1]) and shows the score with a brief rationale. ([Ragas][4])

---

## 4) Non-Functional Notes (impacted)

* **Performance:** Hybrid + optional rerank should keep p95 under targets by **deferring rerank** and keeping it **top-20→5**. **BGE-Reranker-v2-m3** is sizeable (\~568M); only run when toggled. ([Hugging Face][11])
* **Observability:** Log `(k, weights, ranks)` for RRF; record QA metrics per turn. \[Inference]

---

## 5) Implementation Sketch (grounded hooks)

* **RRF core:** Implement standard RRF `score(d)=Σ_i 1/(k+rank_i(d))`, expose `k` and per-retriever **weights**; defaults match Elastic/Milvus guidance (k≈**60**). ([Elastic][1], [Milvus][2])
* **Hybrid sources:**

  * **Dense** via MiniLM (**384-d**); verify Pinecone index dimension==384 before upsert/query. ([Hugging Face][7])
  * **Lexical** via `rank-bm25` (simple) or `bm25s` (faster sparse-matrix). ([PyPI][8], [BM25S][9])
  * **(Optional later)** Pinecone **hybrid** using separate **dense** + **sparse** indexes, then combine client-side. ([Pinecone Docs][10])
* **Rerank:** Wrap **BGE-Reranker-v2-m3** as `rerank(topN=20)->topM=5`; keep off by default. ([Hugging Face][11])
* **Multipage:** Use **Gradio Multipage** (`Blocks.route`) for `/ingest`, `/evaluate`, `/settings`; keep `ChatInterface` on `/`. ([Gradio][6])
* **Streaming:** Chat callback **yields** partial strings to `ChatInterface` (officially supported). ([Gradio][12])
* **QA:** Evaluate last turn with **Ragas** **Faithfulness** (definition and examples in docs). ([Ragas][4])

---

## 6) Risks & Mitigations (specific to these adds)

* **CPU overhead (reranking):** Keep it **toggle-only** and small $20→5$; if latency is high, fall back to **dense-only rerank** or raise the toggle threshold. ([Hugging Face][11])
* **Fusion mis-tuning:** Expose `k` and show delta view of ordering; keep k=60 as safe default per common practice. ([Elastic][1], [Milvus Blog][3], [veso.ai][13])
* **QA metric drift:** Ragas itself can be noisy; present **Faithfulness** alongside raw context snippets; allow manual override tags. ([Pinecone][5])

---

### Source notes (key references)

* **MiniLM 384-d** (Sentence-Transformers). ([Hugging Face][7])
* **BM25 Python libs** (`rank-bm25`, `bm25s`). ([PyPI][8], [BM25S][9])
* **Pinecone hybrid (dense + sparse) pattern.** ([Pinecone Docs][10])
* **RRF defaults & formula (k≈60).** ([Elastic][1], [Milvus][2], [Milvus Blog][3])
* **BGE-Reranker-v2-m3 (≈568M).** ([Hugging Face][11])
* **Gradio Multipage & ChatInterface streaming.** ([Gradio][6])
* **Ragas Faithfulness definition & usage.** ([Ragas][4])

---

[1]: https://elastic.aiops.work/guide/en/elasticsearch/reference/current/rrf.html?utm_source=chatgpt.com "Reciprocal rank fusion | Elastic Documentation"
[2]: https://milvus.io/docs/rrf-ranker.md?utm_source=chatgpt.com "RRF Ranker | Milvus Documentation"
[3]: https://blog.milvus.io/docs/rrf-ranker.md?utm_source=chatgpt.com "RRF Ranker | Milvus Documentation"
[4]: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/?utm_source=chatgpt.com "Faithfulness - Ragas"
[5]: https://www.pinecone.io/learn/series/rag/ragas/?utm_source=chatgpt.com "Metrics-Driven Agent Development | Pinecone"
[6]: https://www.gradio.app/main/guides/multipage-apps?utm_source=chatgpt.com "Multipage Apps"
[7]: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2?utm_source=chatgpt.com "sentence-transformers/all-MiniLM-L6-v2 · Hugging Face"
[8]: https://pypi.org/project/rank-bm25/?utm_source=chatgpt.com "rank-bm25 · PyPI"
[9]: https://bm25s.github.io/?utm_source=chatgpt.com "BM25S⚡"
[10]: https://docs.pinecone.io/guides/indexes/pods/encode-sparse-vectors?utm_source=chatgpt.com "Hybrid search - Pinecone Docs"
[11]: https://huggingface.co/BAAI/bge-reranker-v2-m3?utm_source=chatgpt.com "BAAI/bge-reranker-v2-m3 · Hugging Face"
[12]: https://www.gradio.app/docs/gradio/chatinterface?utm_source=chatgpt.com "Gradio Docs"
[13]: https://veso.ai/blog/reciprical-rank-fusion/?utm_source=chatgpt.com "Reciprocal Rank Fusion (RRF) Explained | Veso AI Blog"
