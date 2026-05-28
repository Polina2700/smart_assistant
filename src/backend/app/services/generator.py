"""
Generator Service — Answer generation using Groq API (llama-3.3-70b-versatile)
Supports conversation history and multilingual responses.
"""

import os
import re
import logging
from typing import List, Dict
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)
GROQ_MODEL = "llama-3.3-70b-versatile"


class GeneratorService:

    def __init__(self):
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not set in .env")
            self.client = Groq(api_key=api_key)
            logger.info(f"Generator initialized with model: {GROQ_MODEL}")
        except Exception as e:
            logger.error(f"Generator initialization failed: {e}")
            self.client = None
        self._history: Dict[str, List[Dict]] = {}

    def generate(self, query: str, context_chunks: List[Dict], session_id: str, language: str = "English") -> Dict:
        if not self.client:
            return self._fallback_response(context_chunks, query)

        context_text = self._build_context(context_chunks)
        has_context = bool(context_text.strip())
        prompt = self._build_prompt(query, context_text, self._history.get(session_id, []), language, has_context)

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
            )
            answer = response.choices[0].message.content.strip()
            answer = re.sub(r'\[Source \d+: [^\]]+\]', '', answer).strip()
            answer = re.sub(r'\[Source (\d+)\]', r'[\1]', answer)
        except Exception as e:
            logger.error(f"Groq generation failed: {e}", exc_info=True)
            return self._fallback_response(context_chunks, query)

        self._update_history(session_id, query, answer)
        return {
            "answer": answer,
            "sources": self._extract_sources(context_chunks),
            "used_context": len(context_chunks),
            "confidence": self._get_confidence(context_chunks, answer),
        }

    def get_history(self, session_id: str) -> List[Dict]:
        return self._history.get(session_id, [])

    def clear_history(self, session_id: str):
        if session_id in self._history:
            del self._history[session_id]

    def is_simple_query(self, query: str) -> bool:
        if not self.client or len(query.strip()) > 60:
            return False
        prompt = (
            "Reply YES only if the message is CLEARLY one of:\n"
            "- A greeting or farewell (hi, hello, bye, ciao, zdravo)\n"
            "- A thank-you or compliment (thanks, great, awesome)\n"
            "- A pure math expression (2+2, 5*4)\n"
            "- A question about the bot itself (who are you, what can you do)\n"
            "Reply NO for everything else.\n\n"
            f"Message: {query}\n\nAnswer (YES or NO):"
        )
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=5,
            )
            return response.choices[0].message.content.strip().upper().startswith("YES")
        except Exception:
            return False

    def generate_simple_response(self, query: str, language: str = "English") -> str:
        if not self.client:
            return "Hello! I'm NovaTech Assistant. How can I help you?"
        prompt = (
            f"You are a friendly assistant for NovaTech Consulting's knowledge base. "
            f"The user sent a casual message. Respond naturally in {language} in 1-2 sentences. "
            f"Mention you can help find information about NovaTech projects, clients, and team.\n\nUser: {query}"
        )
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Hello! I'm NovaTech Assistant. Ask me anything about our projects, clients, or team."

    def _build_context(self, chunks: List[Dict]) -> str:
        if not chunks:
            return ""
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[{i}]\n{chunk['text']}")
        return "\n\n---\n\n".join(parts)

    def _build_prompt(self, query: str, context: str, history: List[Dict], language: str, has_context: bool) -> str:
        system = f"""You are an AI assistant for NovaTech Consulting's internal knowledge base.
NovaTech is an ERP consulting company. You have access to internal documents about projects, clients, team, and methodologies.

RULES:
1. Answer ONLY based on the provided documents. Never use outside knowledge.
2. Cite sources using short notation like [1], [2] — never include filenames in citations.
3. CONTRADICTION CHECK (mandatory): Before answering, scan ALL provided documents for conflicting information on the same topic. If found — report both values and their sources explicitly. Example: "Document [1] says X, but document [2] says Y — this may be because..."
4. OUTDATED CHECK: If any document is marked as OUTDATED or STATUS: OUTDATED — mention this and prefer the newer source.
5. If the answer is not in the documents, say clearly: "I don't have information in the NovaTech knowledge base to answer this."
6. Be concise. Match answer length to question complexity.
7. Always respond in {language}.
8. For questions about project managers, clients, or team assignments — always check table/CSV sources first, as they contain the most structured project data.
9. STRICT NO-HALLUCINATION for unanswerable: If information is not explicitly stated in the documents, say EXACTLY: 'I don't have information in the NovaTech knowledge base to answer this.' Do NOT say 'based in Ljubljana', 'likely', 'probably', or infer from context. Silence is better than a guess.
10. "9. For questions asking about MULTIPLE projects, clients, or team members — make sure to check ALL retrieved documents, not just the first one. List ALL relevant items you find.
"""

        history_text = ""
        if history:
            recent = history[-4:]
            history_text = "\n\n=== CONVERSATION HISTORY ===\n"
            for turn in recent:
                role = "User" if turn["role"] == "user" else "Assistant"
                history_text += f"{role}: {turn['content'][:300]}\n"
            history_text += "=== END HISTORY ===\n"

        if has_context:
            docs_section = f"\n\n=== RETRIEVED DOCUMENTS ===\n{context}\n=== END DOCUMENTS ==="
            task = f"\n\n=== QUESTION ===\n{query}\n\nAnswer concisely using [N] citations where needed:"
        else:
            docs_section = ""
            task = f"\n\n=== QUESTION ===\n{query}\n\nNo relevant documents found. State clearly you don't have this information."

        return system + history_text + docs_section + task

    def _update_history(self, session_id: str, query: str, answer: str):
        if session_id not in self._history:
            self._history[session_id] = []
        self._history[session_id].extend([
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer},
        ])
        if len(self._history[session_id]) > 20:
            self._history[session_id] = self._history[session_id][-20:]

    def _extract_sources(self, chunks: List[Dict], max_sources: int = 5) -> List[Dict]:
        seen = set()
        sources = []
        for i, chunk in enumerate(chunks, 1):
            doc_id = chunk["doc_id"]
            if doc_id not in seen:
                seen.add(doc_id)
                sources.append({
                    "index": i,
                    "filename": chunk["filename"],
                    "type": chunk["type"],
                    "doc_id": doc_id,
                    "score": chunk.get("rrf_score", 0),
                })
            if len(sources) >= max_sources:
                break
        return sources

    def _get_confidence(self, chunks: List[Dict], answer: str) -> str:
        if not chunks:
            return "none"
        if any(p in answer.lower() for p in ["don't have information", "cannot find", "knowledge base to answer"]):
            return "none"
        top_score = chunks[0].get("rrf_score", 0)
        if top_score > 0.012:
            return "high"
        elif top_score > 0.006:
            return "medium"
        return "low"

    def _fallback_response(self, chunks: List[Dict], query: str) -> Dict:
        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the NovaTech knowledge base.",
                "sources": [], "used_context": 0, "confidence": "none"
            }
        parts = ["AI generation unavailable. Raw excerpts:\n"]
        for i, chunk in enumerate(chunks[:3], 1):
            parts.append(f"**{i}. {chunk['filename']}**\n{chunk['text'][:200]}...")
        return {
            "answer": "\n".join(parts),
            "sources": self._extract_sources(chunks),
            "used_context": len(chunks),
            "confidence": "low"
        }