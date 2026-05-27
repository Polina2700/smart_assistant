"""
LLM-as-Judge Evaluation Script for NovaTech Smart Assistant
Runs 15 evaluation questions, scores answers using Groq, saves results to JSON + prints summary.

Usage:
    python eval.py              # run all 15 questions
    python eval.py --quick      # run first 5 only (simple questions)
"""

import os
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
# в начале файла после импортов:
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api")
GROQ_MODEL = "llama-3.3-70b-versatile"
EVAL_SESSION = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RESULTS_DIR = Path(__file__).parent.parent / "eval"

# ─────────────────────────────────────────────
# EVALUATION DATASET — 15 questions
# ─────────────────────────────────────────────

EVAL_QUESTIONS = [
    # ── SIMPLE (5) ────────────────────────────
    {
        "id": "S01", "category": "simple",
        "question": "Who was the project manager for FoodDist?",
        "expected": "Sarah Chen",
        "notes": "Direct fact from project portfolio CSV"
    },
    {
        "id": "S02", "category": "simple",
        "question": "What was the total budget for the Adriatic Petrochemical project?",
        "expected": "€280,000 (Phase 1 €161,000 + Phase 2 €119,000)",
        "notes": "From proposal and portfolio table"
    },
    {
        "id": "S03", "category": "simple",
        "question": "Which NovaTech consultant has experience with SAP S/4HANA Public Cloud?",
        "expected": "Anna Wolff — the only consultant with public cloud experience",
        "notes": "From team skills matrix and meeting notes"
    },
    {
        "id": "S04", "category": "simple",
        "question": "What SAP modules were implemented for FoodDist Logistics?",
        "expected": "WM, MM, PP-PI (Warehouse Management, Materials Management, Production Planning)",
        "notes": "From go-live meeting notes and portfolio"
    },
    {
        "id": "S05", "category": "simple",
        "question": "What is NovaTech's hourly rate for change requests in 2023?",
        "expected": "€150 per hour regardless of consultant level",
        "notes": "From billing rates table and Adriatic proposal"
    },

    # ── MULTI-HOP (3) ─────────────────────────
    {
        "id": "M01", "category": "multi_hop",
        "question": "Which NovaTech projects involved cloud migration and what were the key lessons learned?",
        "expected": "MediaGroup (NAV to BC, custom reports underestimated), RetailPro (cancelled, Dynamics 365), GreenEnergy (SAP Public Cloud, in progress). Lessons: audit customizations before quoting, 70-80% of custom reports need redesign, verify system version before signing contract.",
        "notes": "Requires combining meeting notes, retrospectives, tech reports"
    },
    {
        "id": "M02", "category": "multi_hop",
        "question": "Who from the NovaTech team has worked on pharmaceutical or medical clients and what technologies did they use?",
        "expected": "Tomasz Kowalski (PharmaCro — SAP ECC MM/QM, FDA 21 CFR Part 11), Mark Horvat (BioMed Solutions — SAP ECC FI/CO/MM/QM), Anna Wolff (PharmaCro remote FI support)",
        "notes": "Requires combining skills matrix, portfolio, meeting notes"
    },
    {
        "id": "M03", "category": "multi_hop",
        "question": "What was the total financial impact of all NovaTech projects that went over budget?",
        "expected": "Balkans Steel +€45,000, MediaGroup +€7,000, LogiHub +€15,000, BioMed risk +€21,500-43,500. Total confirmed overruns: at least €67,000",
        "notes": "Requires combining portfolio CSV and multiple retrospective notes"
    },

    # ── UNANSWERABLE (4) ──────────────────────
    {
        "id": "U01", "category": "unanswerable",
        "question": "What is NovaTech's office address in Ljubljana?",
        "expected": "NOT IN DOCUMENTS — system should say it cannot find this information",
        "notes": "No address in any document"
    },
    {
        "id": "U02", "category": "unanswerable",
        "question": "What is Mark Horvat's personal email address?",
        "expected": "NOT IN DOCUMENTS — no personal contact details anywhere",
        "notes": "No personal contacts in corpus"
    },
    {
        "id": "U03", "category": "unanswerable",
        "question": "Does NovaTech have experience implementing Oracle Cloud ERP?",
        "expected": "NO — technology matrix shows no Oracle ERP implementation experience. Oracle appears only as a legacy source system in migrations, not as something NovaTech implements.",
        "notes": "Easy to hallucinate — Oracle mentioned but only as source system"
    },
    {
        "id": "U04", "category": "unanswerable",
        "question": "What is NovaTech's total revenue for 2022?",
        "expected": "NOT IN DOCUMENTS — only 2023 quarterly data available, no 2022 annual figure",
        "notes": "2023 data exists but not 2022"
    },

    # ── TRICK / CONTRADICTORY (3) ─────────────
    {
        "id": "T01", "category": "trick_contradictory",
        "question": "What was the BioMed Solutions budget spent as of May 2023?",
        "expected": "CONTRADICTORY DATA: Meeting notes from May 10 say €142,000 spent; Status report from May 31 says €145,400. Both correct for their dates (3 more weeks elapsed). System should note the discrepancy.",
        "notes": "mn_002 vs tr_007 — intentional contradiction"
    },
    {
        "id": "T02", "category": "trick_contradictory",
        "question": "What SAP system was BioMed Solutions running before the NovaTech project?",
        "expected": "CONTRADICTORY: Original proposal assumed SAP S/4HANA based on RFP. Actual system discovered in week 1 was SAP ECC 6.0 Enhancement Pack 8. Project proceeded on ECC basis.",
        "notes": "Proposal says S/4HANA, meeting notes say ECC"
    },
    {
        "id": "T03", "category": "trick_contradictory",
        "question": "What is the price of Microsoft Dynamics 365 BC per user per month?",
        "expected": "CONTRADICTORY/OUTDATED: 2021 document says €57/user Essential (but explicitly marked OUTDATED). RetailPro proposal from 2022 shows €17.78/user Essential. Current price is €17.78.",
        "notes": "tr_009 is explicitly outdated, contradicts pp_002"
    },
]


# ─────────────────────────────────────────────
# ASK THE ASSISTANT
# ─────────────────────────────────────────────

def ask_assistant(question: str, session_id: str, language: str = "English") -> dict:
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={"message": question, "session_id": session_id, "language": language},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"response": f"ERROR: {e}", "sources": [], "confidence": "error", "log_id": 0}


# ─────────────────────────────────────────────
# LLM-AS-JUDGE
# ─────────────────────────────────────────────

def judge_answer(client: Groq, question: str, expected: str, actual: str, category: str) -> dict:
    prompt = f"""You are evaluating an AI assistant for NovaTech Consulting's internal knowledge base.

Category: {category}
Question: {question}
Expected answer (ground truth): {expected}
System's actual answer: {actual}

Score on 4 criteria (0-3 each):

1. CORRECTNESS (0-3): Factual accuracy
   3=fully correct | 2=mostly correct, minor gaps | 1=partially correct | 0=wrong

2. HALLUCINATION (0-3): Avoids making up information
   3=no hallucinations | 2=minor extrapolation | 1=some unsupported claims | 0=significant fabrication

3. SOURCE_CITATION (0-3): Proper source attribution
   3=clear citations | 2=general references | 1=vague | 0=none

4. UNCERTAINTY (0-3): Handles uncertainty/contradictions correctly
   For unanswerable: 3=correctly refuses | 0=makes up answer
   For contradictory: 3=identifies both values and explains | 0=picks one without noting conflict
   For simple/multi-hop: 3=appropriate confidence | 0=overconfident when wrong

Reply ONLY with valid JSON:
{{
  "correctness": <0-3>,
  "hallucination": <0-3>,
  "source_citation": <0-3>,
  "uncertainty": <0-3>,
  "total": <sum>,
  "explanation": "<2 sentences explaining the scores>"
}}"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300,
        )
        text = response.choices[0].message.content.strip()
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            scores = json.loads(match.group())
            scores["total"] = scores.get("correctness", 0) + scores.get("hallucination", 0) + scores.get("source_citation", 0) + scores.get("uncertainty", 0)
            return scores
    except Exception as e:
        print(f"  Judge error: {e}")

    return {"correctness": 0, "hallucination": 0, "source_citation": 0, "uncertainty": 0, "total": 0, "explanation": "Evaluation failed"}


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def run_evaluation(quick: bool = False):
    print("=" * 60)
    print("NovaTech Smart Assistant — Evaluation")
    print(f"Session: {EVAL_SESSION}")
    print("=" * 60)

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    questions = EVAL_QUESTIONS[:5] if quick else EVAL_QUESTIONS

    results = []
    category_scores = {}

    for i, item in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {item['id']} ({item['category']})")
        print(f"  Q: {item['question'][:70]}...")

        # Use separate session per question to avoid context bleeding
        session_id = f"{EVAL_SESSION}_{item['id']}"

        t0 = time.time()
        api_result = ask_assistant(item["question"], session_id)
        latency = round(time.time() - t0, 2)

        actual_answer = api_result.get("response", "")
        sources = api_result.get("sources", [])
        confidence = api_result.get("confidence", "")

        scores = judge_answer(client, item["question"], item["expected"], actual_answer, item["category"])

        pct = round(scores["total"] / 12 * 100)
        print(f"  Score: {scores['total']}/12 ({pct}%) | {scores['explanation'][:80]}")
        print(f"  Latency: {latency}s | Confidence: {confidence} | Sources: {len(sources)}")

        result = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected": item["expected"],
            "actual_answer": actual_answer,
            "sources": [s.get("filename", "") for s in sources],
            "confidence": confidence,
            "latency_seconds": latency,
            "scores": scores,
        }
        results.append(result)

        cat = item["category"]
        if cat not in category_scores:
            category_scores[cat] = []
        category_scores[cat].append(scores["total"])

        time.sleep(0.5)

    # ── Summary ───────────────────────────────
    total = sum(r["scores"]["total"] for r in results)
    max_score = len(results) * 12
    overall_pct = round(total / max_score * 100, 1)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "session": EVAL_SESSION,
        "total_questions": len(results),
        "total_score": total,
        "max_possible": max_score,
        "overall_pct": overall_pct,
        "by_category": {
            cat: {
                "questions": len(scores),
                "avg_score": round(sum(scores) / len(scores), 2),
                "avg_pct": round(sum(scores) / len(scores) / 12 * 100, 1),
            }
            for cat, scores in category_scores.items()
        },
        "results": results,
    }

    # Save
    RESULTS_DIR.mkdir(exist_ok=True)
    out_file = RESULTS_DIR / f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Overall: {total}/{max_score} ({overall_pct}%)")
    print(f"\nBy category:")
    for cat, data in summary["by_category"].items():
        bar = "█" * int(data["avg_pct"] / 10) + "░" * (10 - int(data["avg_pct"] / 10))
        print(f"  {cat:<20} {bar} {data['avg_score']}/12 ({data['avg_pct']}%)")
    print(f"\nResults saved: {out_file}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run only first 5 questions")
    args = parser.parse_args()
    run_evaluation(quick=args.quick)