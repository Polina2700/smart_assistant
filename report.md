# REPORT.md - NovaTech Smart Assistant

---

## 1. Architecture

I went with hybrid retrieval - TF-IDF combined with sentence embeddings, fused via Reciprocal Rank Fusion.

The reason is quite simple: the corpus has two different retrieval problems. TF-IDF is good for exact terms like "FoodDist" or "PP-PI" - rare words with high IDF weight that embeddings tend to miss because the model has never seen them. Embeddings handle the semantic side - "who was responsible for X" matching "PM: Sarah Chen" without shared keywords. Neither works well alone on this kind of corpus, so I combined them. Embeddings get a slightly higher weight (0.6 vs 0.4) because questions are usually paraphrased, not keyword searches.

I didn't use ChromaDB or LangChain. For 31 documents ChromaDB is overkill - the in-memory index builds in ~10 seconds and there's nothing to gain from a vector DB at this scale. LangChain hides too much behind abstractions, which makes debugging harder and would have made it difficult to explain the architecture clearly.

For generation I used Groq (llama-3.3-70b). Started with Gemini - prepaid credits ran out mid-development. Groq is free, fast (~1-2s), and good enough for a prototype.

---

## 2. What changed during development

The chunk size went through three versions: 400 → 80 → 200. At 400 we got 51 chunks for 31 documents which was too rough. At 80 the chunks were just sentence fragments that confused the LLM. Settled on 200 words with 40-word overlap, which gave 137 chunks with actual context in each.

The bigger surprise was CSV handling. I knew about chunking edge cases in theory but had always used methods that handled it automatically (solution from the box, like Vertex AI search). Here, word-boundary chunking was splitting CSV rows across two chunks - so neither chunk had both "FoodDist" and "Sarah Chen" in it, and the answer to "who was PM for FoodDist" was just not retrievable. The fix was simple once I found it: index each row separately with headers prepended. But finding it required actually looking at raw chunk content, not just retrieval scores.

Prompt engineering also took a few iterations. The main things that helped: adding an explicit instruction to check all documents for contradictions before answering (without this the bot would just return whichever number it found first), and adding a rule to prefer newer sources when a document is marked as OUTDATED. Both made a visible difference on the trick questions.

---

## 3. Where it fails

Proper noun + role queries are the weakest point. "Who was the project manager for FoodDist?" - the CSV row with Sarah Chen scores 4th or 5th in retrieval even though it has the exact answer, because TF-IDF can't match "project manager" to the "PM" column header and short CSV rows have weaker embeddings than longer document chunks.

Unanswerable questions are also inconsistent. Instead of cleanly refusing, the system sometimes says things like "NovaTech is based in Ljubljana" - technically inferable from context but not stated anywhere. The prompt rule helps but doesn't fully fix it.

Multi-hop queries work partially. The system finds some relevant documents but not always all of them, and the LLM sometimes synthesizes from only the top-ranked chunk rather than everything retrieved.

And honestly, running evaluation was a pain. Between Groq's 100k/day limit, Google AI Studio credits running out, and OpenRouter models being rate-limited or unavailable, I couldn't run a clean full evaluation. The results below are from what actually completed. These issues can usually be resolved using the organization’s Google Cloud account, where tokens for both production and training are quite low-cost.

---

## 4. What I would do differently

The main retrieval weakness - proper noun + role queries - could be fixed by rewriting the user's question into a better search query before hitting the index. If someone asks "who ran FoodDist?", first ask the LLM to rewrite it as "FoodDist Logistics project manager name", then search. That version would actually match the CSV row. Same idea applies to expanding abbreviations at index time: if "PM" in the CSV header became "Project Manager" before indexing, TF-IDF would find it correctly.

For evaluation: a paid API tier. Running 15 questions twice (ask + judge) hits free limits fast.

---

## 5. What works well

Simple factual questions are reliable when retrieval finds the right document - 91.7% in evaluation. Contradiction detection actually works, which was the hardest thing to get right - when two documents say different things about the same fact, the system reports both and explains the discrepancy. T03 (BC pricing, outdated vs current document) scored 100%.

The UI has a real-time confidence indicator on every answer so users can see immediately how much to trust the response. There's an admin dashboard at `/admin` to browse conversations and feedback without downloading anything. The interface can also run as an embeddable widget - same approach used in a production ERP chatbot I've been building, so this wasn't theoretical.

---

## 6. Evaluation results

Ran LLM-as-judge evaluation - Groq llama-3.3-70b scored each answer on 4 criteria (correctness, hallucination, citations, uncertainty handling), 0-3 points each, 12 max per question.

| Category | Questions | Avg Score | % |
|---|---|---|---|
| Simple | 2 | 10.5/12 | 91.7% |
| Multi-hop | 2 | 5.5/12 | 45.8% |
| Unanswerable | 1 | 5.0/12 | 41.7% |
| Trick/contradictory | 1 | 12.0/12 | 100% |

Simple questions work well when retrieval finds the right document. Multi-hop is weaker - system finds some but not all relevant documents. Unanswerable is the problem area - system sometimes infers things instead of refusing cleanly. The trick question about BC pricing (outdated €57 doc vs current €17.78) scored 100%, which was the most satisfying result.

Couldn't run the full 15-question set - rate limits across Groq, Google AI Studio, and OpenRouter made it hard to get a clean evaluation session. Full results in `eval/` folder.

---

## 7. AI tools

Used Claude and Claude Code throughout - for generating banch of documents, writing code, and debugging. Reviewed and edited everything manually.