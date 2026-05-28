"""
LLM-as-Judge Evaluation for NovaTech Smart Assistant
8 questions, 2 per category.

Usage:
    python eval.py
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api")
JUDGE_MODEL = "llama-3.3-70b-versatile"
RESULTS_DIR = Path(__file__).parent.parent / "eval"

EVAL_QUESTIONS = [
    # SIMPLE (2)
    {
        "id": "S01", "category": "simple",
        "question": "Who was the project manager for FoodDist?",
        "expected": "Sarah Chen",
    },
    {
        "id": "S03", "category": "simple",
        "question": "Which NovaTech consultant is certified for SAP S/4HANA Public Cloud?",
        "expected": "Anna Wolff — the only consultant with public cloud certification",
    },
    # MULTI-HOP (2)
    {
        "id": "M01", "category": "multi_hop",
        "question": "Which NovaTech projects involved cloud migration and what were the key lessons learned?",
        "expected": "MediaGroup (NAV to BC): custom reports underestimated, 70-80% need redesign. RetailPro: cancelled. GreenEnergy: SAP Public Cloud in progress. Key lesson: audit customizations before quoting.",
    },
    {
        "id": "M02", "category": "multi_hop",
        "question": "Who from the NovaTech team worked on pharmaceutical or medical clients?",
        "expected": "Tomasz Kowalski (PharmaCro — SAP ECC MM/QM), Mark Horvat (BioMed — SAP ECC FI/CO/MM/QM), Anna Wolff (PharmaCro remote FI support)",
    },
    # UNANSWERABLE (2)
    {
        "id": "U01", "category": "unanswerable",
        "question": "What is NovaTech's office address in Ljubljana?",
        "expected": "NOT IN DOCUMENTS — system should clearly refuse",
    },
    {
        "id": "U04", "category": "unanswerable",
        "question": "What is NovaTech's total revenue for 2022?",
        "expected": "NOT IN DOCUMENTS — no annual revenue figures in corpus",
    },
    # TRICK/CONTRADICTORY (2)
    {
        "id": "T01", "category": "trick_contradictory",
        "question": "What was the BioMed Solutions budget spent as of May 2023?",
        "expected": "CONTRADICTORY: May 10 meeting notes say 142000 EUR, May 31 status report says 145400 EUR. System should note both and explain the difference.",
    },
    {
        "id": "T03", "category": "trick_contradictory",
        "question": "What is the price of Microsoft Dynamics 365 BC per user per month?",
        "expected": "CONTRADICTORY: OUTDATED 2021 document says 57 EUR, current 2022 proposal says 17.78 EUR. System should prefer newer source and flag outdated document.",
    },
]


def ask_assistant(question: str, session_id: str) -> dict:
    try:
        r = requests.post(
            f"{API_BASE}/chat",
            json={"message": question, "session_id": session_id, "language": "English"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"response": f"ERROR: {e}", "sources": [], "confidence": "error", "log_id": 0}


def judge_answer(client, question, expected, actual, category) -> dict:
    prompt = f"""You are evaluating an AI assistant for NovaTech Consulting's internal knowledge base.

Category: {category}
Question: {question}
Expected: {expected}
Actual answer: {actual}

Score 0-3 each:
1. CORRECTNESS: factual accuracy (3=correct, 0=wrong)
2. HALLUCINATION: avoids fabrication (3=no hallucinations, 0=makes things up)
3. SOURCE_CITATION: proper [N] citations (3=clear, 0=none)
4. UNCERTAINTY: handles unknowns/contradictions (unanswerable: 3=refuses correctly; contradictory: 3=notes both values; 0=guesses)

Reply ONLY valid JSON:
{{"correctness":<0-3>,"hallucination":<0-3>,"source_citation":<0-3>,"uncertainty":<0-3>,"total":<sum>,"explanation":"<2 sentences>"}}"""

    try:
        r = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=250,
        )
        text = r.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            scores = json.loads(match.group())
            scores["total"] = sum([
                scores.get("correctness", 0), scores.get("hallucination", 0),
                scores.get("source_citation", 0), scores.get("uncertainty", 0)
            ])
            return scores
    except Exception as e:
        print(f"  Judge error: {e}")
    return {"correctness":0,"hallucination":0,"source_citation":0,"uncertainty":0,"total":0,"explanation":"failed"}


def run_evaluation():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    print("=" * 60)
    print("NovaTech Smart Assistant — LLM-as-Judge Evaluation")
    print(f"Questions: {len(EVAL_QUESTIONS)} | Judge: {JUDGE_MODEL}")
    print("=" * 60)

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    results = []
    category_scores = {}

    for i, item in enumerate(EVAL_QUESTIONS, 1):
        print(f"\n[{i}/{len(EVAL_QUESTIONS)}] {item['id']} ({item['category']})")
        print(f"  Q: {item['question'][:70]}")

        session_id = f"eval_{ts}_{item['id']}"
        t0 = time.time()
        api_result = ask_assistant(item["question"], session_id)
        latency = round(time.time() - t0, 2)

        actual = api_result.get("response", "")
        sources = api_result.get("sources", [])
        confidence = api_result.get("confidence", "")

        print(f"  A: {actual[:100]}...")
        time.sleep(1)

        scores = judge_answer(client, item["question"], item["expected"], actual, item["category"])
        pct = round(scores["total"] / 12 * 100)
        print(f"  Score: {scores['total']}/12 ({pct}%) | {scores.get('explanation','')[:80]}")
        print(f"  Latency: {latency}s | Confidence: {confidence} | Sources: {len(sources)}")

        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected": item["expected"],
            "actual_answer": actual,
            "sources": [s.get("filename","") for s in sources],
            "confidence": confidence,
            "latency_seconds": latency,
            "scores": scores,
        })

        cat = item["category"]
        category_scores.setdefault(cat, []).append(scores["total"])
        time.sleep(1)

    total = sum(r["scores"]["total"] for r in results)
    max_score = len(results) * 12
    overall_pct = round(total / max_score * 100, 1)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(results),
        "total_score": total,
        "max_possible": max_score,
        "overall_pct": overall_pct,
        "judge_model": JUDGE_MODEL,
        "by_category": {
            cat: {
                "questions": len(sc),
                "avg_score": round(sum(sc)/len(sc), 2),
                "avg_pct": round(sum(sc)/len(sc)/12*100, 1),
            }
            for cat, sc in category_scores.items()
        },
        "results": results,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"eval_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"Overall: {total}/{max_score} ({overall_pct}%)")
    print(f"\nBy category:")
    for cat, data in summary["by_category"].items():
        bar = "█" * int(data["avg_pct"]/10) + "░" * (10 - int(data["avg_pct"]/10))
        print(f"  {cat:<22} {bar} {data['avg_score']}/12 ({data['avg_pct']}%)")
    print(f"\nSaved: {out}")
    return summary


if __name__ == "__main__":
    run_evaluation()