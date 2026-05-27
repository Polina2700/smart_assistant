"""
LLM-as-Judge Evaluation Script for BINU AI Assistant
Reads real conversations from Google Sheets Q&A tab,
evaluates each answer using Groq, writes results to "Evaluation" sheet.

Usage:
    python eval_binu.py              # evaluate last 20 rows
    python eval_binu.py --n 50       # evaluate last 50 rows
    python eval_binu.py --all        # evaluate all rows
"""

import os
import sys
import json
import time
import argparse
import re
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from groq import Groq
from dotenv import load_dotenv
from src.backend.app.services.generator import GROQ_MODEL

load_dotenv()

SPREADSHEET_ID = "1tZDaOyZzq3Egdn7TP_WIpnNyODU1_d4qUapoGgz8IwY"
QA_SHEET = "Q&A"
EVAL_SHEET = "Evaluation"

CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "secrets/erp-chatbot.json")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

COL_ID = 0
COL_TIMESTAMP = 1
COL_SESSION = 2
COL_QUESTION = 3
COL_ANSWER = 4
COL_LATENCY = 5
COL_RELEVANCE = 6
COL_CONV_TYPE = 7
COL_RATING = 8
COL_COMMENT = 9
COL_SOURCES = 12


def init_sheets():
    creds = service_account.Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()


def get_qa_rows(sheets, n=None):
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{QA_SHEET}!A:N"
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    data_rows = rows[1:]
    data_rows = [r for r in data_rows if len(r) > COL_ANSWER and r[COL_QUESTION].strip()]
    if n:
        data_rows = data_rows[-n:]
    return data_rows


def ensure_eval_sheet(sheets):
    meta = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
    existing = [s["properties"]["title"] for s in meta["sheets"]]
    if EVAL_SHEET not in existing:
        sheets.batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": EVAL_SHEET}}}]}
        ).execute()
        print(f"Created sheet: {EVAL_SHEET}")
    headers = [[
        "Eval Date", "QA Row ID", "Timestamp", "Session ID",
        "Question", "Answer (truncated)",
        "Conversation Type", "User Rating",
        "Accuracy (1-5)", "Completeness (1-5)",
        "Hallucination (1-5)", "Relevance (1-5)",
        "Total (max 20)", "Groq Explanation",
        "Latency (ms)", "Retrieval Score"
    ]]
    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{EVAL_SHEET}!A1:P1",
        valueInputOption="RAW",
        body={"values": headers}
    ).execute()


def append_eval_row(sheets, row_data):
    sheets.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{EVAL_SHEET}!A:P",
        valueInputOption="RAW",
        body={"values": [row_data]}
    ).execute()


def init_groq():
    client = Groq(
        api_key=os.getenv("GROQ_API_KEY")
    )
    return client


def evaluate_answer(client, question, answer, sources, conv_type):
    prompt = f"""You are an expert evaluator for an ERP documentation chatbot called BINU AI Assistant.
The chatbot answers employee questions about how to use the BINU ERP system.

Evaluate the chatbot's answer on 4 criteria. Score each from 1 to 5.

---
QUESTION FROM USER:
{question}

CHATBOT'S ANSWER:
{answer}

SOURCE DOCUMENTS RETRIEVED:
{sources or "No sources retrieved"}

CONVERSATION TYPE: {conv_type or "unknown"}
---

SCORING CRITERIA:

1. ACCURACY (1-5): Is the answer factually correct based on the retrieved documents?
   5 = Fully accurate | 3 = Mostly correct | 1 = Wrong or contradicts documentation

2. COMPLETENESS (1-5): Does the answer fully address the question?
   5 = Complete with all steps | 3 = Partial answer | 1 = Very incomplete

3. HALLUCINATION (1-5): Does the bot avoid making up information?
   5 = No hallucinations | 3 = Minor extrapolation | 1 = Significant made-up info

4. RELEVANCE (1-5): Is the answer relevant to what was asked?
   5 = Directly answers | 3 = Partially off-topic | 1 = Does not answer

Respond ONLY with valid JSON:
{{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "hallucination": <1-5>,
  "relevance": <1-5>,
  "explanation": "<2-3 sentences explaining scores>"
}}"""

    try:
        response = client.models.generate_content(
            model=GROQ_MODEL,
            contents=prompt
        )
        text = response.text.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
            scores["total"] = (
                scores.get("accuracy", 0) +
                scores.get("completeness", 0) +
                scores.get("hallucination", 0) +
                scores.get("relevance", 0)
            )
            return scores
    except Exception as e:
        print(f"  Groq error: {e}")
        return {
            "accuracy": 0, "completeness": 0,
            "hallucination": 0, "relevance": 0,
            "total": 0, "explanation": f"Evaluation failed: {e}"
        }


def run_evaluation(n=20, evaluate_all=False):
    print("Initializing...")
    sheets = init_sheets()
    client = init_groq()

    print("Setting up Evaluation sheet...")
    ensure_eval_sheet(sheets)

    limit = None if evaluate_all else n
    print(f"Reading {'all' if evaluate_all else f'last {n}'} rows from Q&A...")
    rows = get_qa_rows(sheets, limit)

    if not rows:
        print("No rows found in Q&A sheet.")
        return

    print(f"Found {len(rows)} rows to evaluate.\n")
    results_summary = []

    for i, row in enumerate(rows, 1):
        def get(idx, default=""):
            return row[idx].strip() if len(row) > idx and row[idx] else default

        row_id = get(COL_ID)
        timestamp = get(COL_TIMESTAMP)
        session_id = get(COL_SESSION)
        question = get(COL_QUESTION)
        answer = get(COL_ANSWER)
        latency = get(COL_LATENCY)
        relevance_score = get(COL_RELEVANCE)
        conv_type = get(COL_CONV_TYPE)
        user_rating = get(COL_RATING)
        sources = get(COL_SOURCES)

        if not question or not answer:
            continue

        print(f"[{i}/{len(rows)}] ID={row_id} | {question[:55]}...")
        scores = evaluate_answer(client, question, answer, sources, conv_type)
        pct = round(scores["total"] / 20 * 100)
        print(f"   Score: {scores['total']}/20 ({pct}%) | {scores['explanation'][:70]}...")

        eval_row = [
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            row_id, timestamp, session_id,
            question, answer[:500],
            conv_type, user_rating,
            scores.get("accuracy", 0),
            scores.get("completeness", 0),
            scores.get("hallucination", 0),
            scores.get("relevance", 0),
            scores.get("total", 0),
            scores.get("explanation", ""),
            latency, relevance_score,
        ]

        append_eval_row(sheets, eval_row)
        results_summary.append(scores["total"])
        time.sleep(1)

    if results_summary:
        avg = round(sum(results_summary) / len(results_summary), 2)
        avg_pct = round(avg / 20 * 100, 1)
        print(f"\n{'='*50}")
        print(f"EVALUATION COMPLETE")
        print(f"{'='*50}")
        print(f"Evaluated: {len(results_summary)} answers")
        print(f"Average score: {avg}/20 ({avg_pct}%)")
        print(f"Results written to Google Sheets tab '{EVAL_SHEET}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    run_evaluation(n=args.n, evaluate_all=args.all)