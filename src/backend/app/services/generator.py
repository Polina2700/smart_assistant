"""
Generator Service — Answer generation using Groq API
Supports conversation history and multilingual responses.
"""

import os
import logging
from typing import List, Dict, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"


class GeneratorService:
    """
    Generates answers using Groq API.
    Maintains conversation history per session.
    """

    def __init__(self):
        try:
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            logger.info(f"Generator initialized with model: {GROQ_MODEL}")
        except Exception as e:
            logger.error(f"Generator initialization failed: {e}")
            self.client = None

        self._history: Dict[str, List[Dict]] = {}

    # ─────────────────────────────────────────────
    # PUBLIC METHODS
    # ─────────────────────────────────────────────

    def generate(
        self,
        query: str,
        context_chunks: List[Dict],
        session_id: str,
        language: str = "English",
    ) -> Dict:
        if not self.client:
            return self._fallback_response(context_chunks, query)

        context_text = self._build_context(context_chunks)
        has_context = bool(context_text.strip())

        prompt = self._build_prompt(
            query=query,
            context=context_text,
            history=self._history.get(session_id, []),
            language=language,
            has_context=has_context,
        )

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
            )
            answer = response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq generation failed: {e}", exc_info=True)
            return self._fallback_response(context_chunks, query)

        self._update_history(session_id, query, answer)
        sources = self._extract_sources(context_chunks)
        confidence = self._get_confidence(context_chunks, answer)

        return {
            "answer": answer,
            "sources": sources,
            "used_context": len(context_chunks),
            "confidence": confidence,
        }

    def get_history(self, session_id: str) -> List[Dict]:
        return self._history.get(session_id, [])

    def clear_history(self, session_id: str):
        if session_id in self._history:
            del self._history[session_id]
            logger.info(f"Cleared history for session: {session_id}")

    def is_simple_query(self, query: str) -> bool:
        """Detect greetings, small talk, math — skip document search."""
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
        """Generate a short friendly response for greetings/small talk."""
        if not self.client:
            return "Hello! I'm NovaTech Assistant. How can I help you?"

        prompt = (
            f"You are a friendly assistant for NovaTech Consulting's knowledge base. "
            f"The user sent a casual message (greeting, small talk, question about you). "
            f"Respond naturally in {language} in 1-2 sentences. "
            f"Mention you can help find information about NovaTech projects, clients, and team.\n\n"
            f"User: {query}"
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

    # ─────────────────────────────────────────────
    # PRIVATE METHODS
    # ─────────────────────────────────────────────

    def _build_context(self, chunks: List[Dict]) -> str:
        if not chunks:
            return ""
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"[Source {i}: {chunk['filename']} | {chunk['type']}]\n{chunk['text']}"
            )
        return "\n\n---\n\n".join(parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        history: List[Dict],
        language: str,
        has_context: bool,
    ) -> str:
        system = f"""You are an AI assistant for NovaTech Consulting's internal knowledge base.
NovaTech is an ERP consulting company with projects, clients, consultants, and methodologies documented internally.

RULES:
1. Answer ONLY based on the provided documents. Do not use outside knowledge.
2. Always cite which source document(s) support your answer using [Source N] notation.
3. If documents contain contradictory information, point it out explicitly.
4. If the answer is not in the documents, say: "I don't have information in the NovaTech knowledge base to answer this."
5. For outdated documents, note that information may be superseded.
6. Be concise but complete.
7. Always respond in {language}."""

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
            task = f"\n\n=== CURRENT QUESTION ===\n{query}\n\nProvide a clear answer with [Source N] citations:"
        else:
            docs_section = ""
            task = (
                f"\n\n=== CURRENT QUESTION ===\n{query}\n\n"
                f"No relevant documents were found. "
                f"State clearly that you don't have information to answer this question."
            )

        return system + history_text + docs_section + task

    def _update_history(self, session_id: str, query: str, answer: str):
        if session_id not in self._history:
            self._history[session_id] = []
        self._history[session_id].append({"role": "user", "content": query})
        self._history[session_id].append({"role": "model", "content": answer})
        if len(self._history[session_id]) > 20:
            self._history[session_id] = self._history[session_id][-20:]

    def _extract_sources(self, chunks: List[Dict], max_sources: int = 3) -> List[Dict]:
        seen = set()
        sources = []
        for chunk in chunks:
            doc_id = chunk["doc_id"]
            if doc_id not in seen:
                seen.add(doc_id)
                sources.append({
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
        top_score = chunks[0].get("rrf_score", 0)
        no_info_phrases = [
            "don't have information", "not in the", "cannot find",
            "no documentation", "knowledge base to answer",
        ]
        if any(p in answer.lower() for p in no_info_phrases):
            return "none"
        if top_score > 0.015:
            return "high"
        elif top_score > 0.008:
            return "medium"
        return "low"

    def _fallback_response(self, chunks: List[Dict], query: str) -> Dict:
        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the NovaTech knowledge base.",
                "sources": [], "used_context": 0, "confidence": "none",
            }
        parts = ["AI generation unavailable. Raw excerpts:\n"]
        for i, chunk in enumerate(chunks[:3], 1):
            parts.append(f"**{i}. {chunk['filename']}**")
            parts.append(chunk["text"][:200] + "...")
        return {
            "answer": "\n".join(parts),
            "sources": self._extract_sources(chunks),
            "used_context": len(chunks),
            "confidence": "low",
        }