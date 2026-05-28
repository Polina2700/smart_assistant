# NovaTech Smart Assistant

AI-powered conversational assistant for NovaTech Consulting's internal knowledge base. Answers questions about projects, clients, team members, and methodologies using a hybrid RAG (Retrieval-Augmented Generation) approach.

Built as a test task for 5element — demonstrates RAG architecture with hybrid search, LLM-as-judge evaluation, and a production-quality chat interface.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Polina2700/smart_assistant.git
cd smart_assistant

# 2. Create virtual environment
cd src/backend
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Run
python run.py
```

Open http://127.0.0.1:8000 in your browser.

---

## Architecture

```
User Question
  → FastAPI Backend
      → Simple query check (greetings → respond directly)
          → Hybrid Search
              → TF-IDF retrieval (keyword matching)
              → Sentence Embeddings (semantic similarity, all-MiniLM-L6-v2)
              → Reciprocal Rank Fusion (combines both rankings)
                  → Top 8 chunks passed to LLM
                      → Groq (llama-3.3-70b-versatile)
                          → Answer + source citations
                              → Logged to SQLite
```

### Why hybrid search?

TF-IDF alone misses semantic matches ("PM" ≠ "project manager"). Embeddings alone struggle with rare proper nouns (client names, project codes). RRF combines both — TF-IDF weight 0.4, embeddings weight 0.6.

### Why Groq instead of Gemini/OpenAI?

Fast (~1s response), generous free tier, no credit card required. Suitable for a prototype that needs to run reliably during evaluation.

---

## Project Structure

```
smart_assistant/
├── documents/                    # 31 synthetic NovaTech documents
│   ├── meeting_notes/            # 11 .md files (kickoffs, retrospectives, status)
│   ├── project_proposals/        # 5 .md files (client proposals)
│   ├── technical_reports/        # 10 .md files (guides, analysis, outdated docs)
│   └── tables/                   # 5 .csv files (portfolio, team, billing, clients)
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI app, all routes
│   │   │   └── services/
│   │   │       ├── rag.py        # Hybrid TF-IDF + embeddings + RRF
│   │   │       └── generator.py  # Groq generation, conversation history
│   │   ├── run.py
│   │   ├── requirements.txt
│   │   └── .env                  # GEMINI_API_KEY (not in git)
│   ├── eval/
│   │   └── eval.py               # 15-question LLM-as-judge evaluation
│   └── frontend/
│       └── index.html            # Chat UI
├── eval/                         # JSON evaluation results
├── README.md
└── REPORT.md
```

---

## Document Corpus

31 synthetic documents for NovaTech Consulting — an ERP implementation company based in Ljubljana with 15 consultants and ~10 completed projects.

**Intentional noise and complexity:**
- Contradictory data: BioMed budget (€142k in meeting notes vs €145k in status report)
- Contradictory system: BioMed SAP version (proposal assumed S/4HANA, actual was ECC 6.0)
- Outdated pricing: `tr_009_outdated_pricing.md` explicitly marked OUTDATED (€57/user vs actual €17.78)
- Very short docs: some meeting notes are 1-2 pages
- Very long docs: technical reports up to 8+ pages
- Structured data: 5 CSV tables (project portfolio, team skills, billing rates, client satisfaction, technology matrix)

**Key entities:**
- Consultants: Sarah Chen (PM), Mark Horvat (Architect), Riku Tanaka (Tech Lead), Anna Wolff (FI/CO, only Public Cloud certified), Tomasz Kowalski (MM/QM)
- Clients: FoodDist, Adriatic Petrochemical, BioMed Solutions, RetailPro, AutoParts, MediaGroup, GreenEnergy, BalKansSteel, LogiHub

---

## Evaluation

15 questions covering 4 categories:

| Category | Questions | Tests |
|---|---|---|
| Simple | 5 | Direct fact retrieval |
| Multi-hop | 3 | Combining info from multiple docs |
| Unanswerable | 4 | Hallucination resistance |
| Trick/Contradictory | 3 | Conflict detection |

LLM-as-judge scoring (0-3 per criterion, max 12 per question):
- **Correctness** — factual accuracy
- **Hallucination** — avoids making up facts
- **Source citation** — proper [N] references
- **Uncertainty handling** — correctly refuses or flags conflicts

```bash
# Run full evaluation (requires server running)
cd src/backend
python ../eval/eval.py

# Quick test (5 questions only)
python ../eval/eval.py --quick
```

Results saved to `eval/eval_YYYYMMDD_HHMMSS.json`.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Chat UI |
| `GET` | `/api/health` | Health check + RAG stats |
| `POST` | `/api/chat` | Main chat endpoint |
| `GET` | `/api/conversation/{session_id}` | Get conversation history |
| `DELETE` | `/api/conversation/{session_id}` | Clear history |
| `POST` | `/api/feedback` | Submit thumbs up/down |
| `GET` | `/api/stats` | Usage statistics |

### Chat request

```json
{
  "message": "Who was the project manager for FoodDist?",
  "session_id": "user_123",
  "language": "English"
}
```

### Chat response

```json
{
  "response": "The project manager for FoodDist Logistics was Sarah Chen [4].",
  "sources": [
    {"filename": "tbl_001_project_portfolio.csv", "type": "tables", "score": 0.016}
  ],
  "log_id": 42,
  "session_id": "user_123",
  "confidence": "high"
}
```

---

## Environment Variables

Create `src/backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
API_BASE=http://127.0.0.1:8000/api
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

Get a free Groq API key at https://console.groq.com

---

## Features

- **Hybrid search** — TF-IDF + sentence embeddings + RRF fusion
- **CSV row-level chunking** — each CSV row indexed separately with headers for accurate tabular data retrieval
- **Contradiction detection** — LLM instructed to scan all retrieved documents for conflicting information
- **Outdated document handling** — LLM prefers newer source when document marked as outdated
- **Conversation history** — last 10 exchanges per session kept in memory
- **Multilingual** — responds in 14 languages (EN, SL, HR, SR, RU, DE, FR, IT, ES, TR, RO, BG, HU, UK)
- **Source citations** — `[N]` inline citations matched to Sources panel
- **User feedback** — thumbs up/down with optional comment, stored in SQLite
- **LLM-as-judge evaluation** — automated quality scoring on 15 test questions

---

## Known Limitations

- **Multi-hop reasoning is inconsistent** — answers combining 3+ documents sometimes miss one source
- **No persistence of embeddings** — model reloads and re-encodes all chunks on every server restart (~10s startup time)
- **In-memory conversation history** — lost on server restart

---

## AI Tools Used

This project was built with significant assistance from ClaudeCode (Anthropic) and Gemini (Google):
- Generated all 31 synthetic documents
- Wrote `rag.py`, `generator.py`, `main.py`, `eval.py`, `index.html`
- Helped debug CSV chunking and retrieval issues