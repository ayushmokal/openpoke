"""Smart FAQ Search tool for Ultrahuman CX Bible knowledge base.

Features:
- Pre-indexed content for fast searches
- Section-aware search (finds specific sections within docs)
- Keyword expansion with synonyms
- Relevance scoring with TF-IDF-like ranking
- Context-aware snippet extraction
- Category classification
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from html.parser import HTMLParser
from collections import defaultdict
import math

from server.logging_config import logger

# Path to the CX Bible knowledge base
FAQ_BASE_PATH = Path("/Users/ayushmokal/Downloads/UH-CXbible-main")

# Synonym mappings for smarter search
SYNONYMS = {
    "battery": ["power", "charge", "charging", "drain", "draining", "dying", "dead"],
    "size": ["sizing", "fit", "fitting", "measurement", "dimensions"],
    "replace": ["replacement", "exchange", "swap", "new ring"],
    "return": ["refund", "money back", "send back"],
    "connect": ["connection", "connectivity", "sync", "syncing", "pairing", "bluetooth"],
    "warranty": ["guarantee", "coverage", "policy", "protection"],
    "broken": ["damaged", "cracked", "defective", "faulty", "not working"],
    "app": ["application", "software", "mobile app"],
    "sleep": ["sleeping", "rest", "bedtime", "night"],
    "heart": ["hr", "heart rate", "pulse", "bpm"],
    "hrv": ["heart rate variability", "variability"],
    "steps": ["walking", "movement", "activity", "exercise"],
    "water": ["waterproof", "swimming", "shower", "wet"],
    "firmware": ["update", "software update", "version"],
    "reset": ["restart", "reboot", "factory reset", "soft reset"],
}

# Category keywords for classification
CATEGORIES = {
    "battery": ["battery", "charge", "charging", "power", "drain", "bdr"],
    "sizing": ["size", "sizing", "fit", "measurement", "too big", "too small", "loose", "tight"],
    "connectivity": ["connect", "bluetooth", "sync", "pair", "app", "phone"],
    "warranty": ["warranty", "replace", "replacement", "return", "refund", "policy"],
    "health_metrics": ["sleep", "heart", "hrv", "steps", "recovery", "spo2", "temperature"],
    "hardware": ["ring", "charger", "dock", "sensor", "led", "light"],
    "troubleshooting": ["not working", "issue", "problem", "error", "fix", "help"],
    "features": ["feature", "track", "measure", "monitor", "insight"],
}


class SmartHTMLParser(HTMLParser):
    """Extract structured content from HTML with section awareness."""

    def __init__(self):
        super().__init__()
        self.sections = []
        self.current_section = {"title": "General", "content": [], "level": 0}
        self.current_tag = None
        self.skip_tags = {"script", "style", "head", "meta", "link", "nav", "header", "footer"}
        self.heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}
        self.in_skip = False

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in self.skip_tags:
            self.in_skip = True
        if tag in self.heading_tags:
            # Save current section and start new one
            if self.current_section["content"]:
                self.sections.append(self.current_section)
            level = int(tag[1])
            self.current_section = {"title": "", "content": [], "level": level}

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.in_skip = False
        self.current_tag = None

    def handle_data(self, data):
        if self.in_skip or self.current_tag in self.skip_tags:
            return
        text = data.strip()
        if not text:
            return
        if self.current_tag in self.heading_tags:
            self.current_section["title"] = text
        else:
            self.current_section["content"].append(text)

    def get_sections(self) -> list[dict]:
        if self.current_section["content"]:
            self.sections.append(self.current_section)
        return self.sections


class FAQIndex:
    """In-memory index for fast FAQ searches."""

    def __init__(self):
        self.documents = {}  # doc_id -> {path, title, sections, full_text}
        self.inverted_index = defaultdict(set)  # word -> set of doc_ids
        self.section_index = defaultdict(list)  # word -> [(doc_id, section_idx, score)]
        self.doc_frequencies = defaultdict(int)  # word -> number of docs containing it
        self.indexed = False

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        text = text.lower()
        words = re.findall(r'\b[a-z]{2,}\b', text)
        return words

    def _expand_query(self, words: list[str]) -> set[str]:
        """Expand query words with synonyms."""
        expanded = set(words)
        for word in words:
            # Check if word is a synonym key
            if word in SYNONYMS:
                expanded.update(SYNONYMS[word])
            # Check if word is in synonym values
            for key, values in SYNONYMS.items():
                if word in values:
                    expanded.add(key)
                    expanded.update(values)
        return expanded

    def _classify_query(self, words: set[str]) -> list[str]:
        """Classify query into categories."""
        categories = []
        for cat, keywords in CATEGORIES.items():
            if words & set(keywords):
                categories.append(cat)
        return categories or ["general"]

    def index_file(self, file_path: Path) -> bool:
        """Index a single file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            if file_path.suffix == ".html":
                parser = SmartHTMLParser()
                parser.feed(content)
                sections = parser.get_sections()
            else:
                sections = [{"title": "Content", "content": [content], "level": 0}]

            doc_id = str(file_path)
            full_text = " ".join(
                s["title"] + " " + " ".join(s["content"])
                for s in sections
            )

            self.documents[doc_id] = {
                "path": str(file_path),
                "filename": file_path.name,
                "title": file_path.stem.replace("-", " ").replace("_", " ").title(),
                "sections": sections,
                "full_text": full_text,
            }

            # Index words
            words = set(self._tokenize(full_text))
            for word in words:
                self.inverted_index[word].add(doc_id)
                self.doc_frequencies[word] += 1

            # Index sections with position
            for idx, section in enumerate(sections):
                section_text = section["title"] + " " + " ".join(section["content"])
                section_words = self._tokenize(section_text)
                word_counts = defaultdict(int)
                for word in section_words:
                    word_counts[word] += 1
                for word, count in word_counts.items():
                    self.section_index[word].append((doc_id, idx, count))

            return True
        except Exception as e:
            logger.debug(f"Error indexing {file_path}: {e}")
            return False

    def build_index(self):
        """Build the full index from FAQ files."""
        if self.indexed:
            return

        logger.info("Building FAQ index...")

        if not FAQ_BASE_PATH.exists():
            logger.error(f"FAQ path not found: {FAQ_BASE_PATH}")
            return

        # Index HTML files in root
        for html_file in FAQ_BASE_PATH.glob("*.html"):
            self.index_file(html_file)

        # Index HTML files in subdirectories
        for html_file in FAQ_BASE_PATH.rglob("**/*.html"):
            if html_file not in [f for f in FAQ_BASE_PATH.glob("*.html")]:
                self.index_file(html_file)

        self.indexed = True
        logger.info(f"FAQ index built: {len(self.documents)} documents, {len(self.inverted_index)} terms")

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Search the index for relevant documents and sections."""
        if not self.indexed:
            self.build_index()

        query_words = self._tokenize(query)
        if not query_words:
            return []

        # Expand query with synonyms
        expanded_words = self._expand_query(query_words)
        categories = self._classify_query(expanded_words)

        logger.info(f"FAQ search: '{query}' -> words={query_words}, expanded={len(expanded_words)}, categories={categories}")

        # Find matching documents
        doc_scores = defaultdict(float)
        doc_matches = defaultdict(set)
        total_docs = len(self.documents)

        for word in expanded_words:
            if word in self.inverted_index:
                matching_docs = self.inverted_index[word]
                # TF-IDF-like scoring
                idf = math.log(total_docs / (1 + self.doc_frequencies[word]))

                for doc_id in matching_docs:
                    # Boost if original query word (not just synonym)
                    boost = 2.0 if word in query_words else 1.0
                    doc_scores[doc_id] += idf * boost
                    doc_matches[doc_id].add(word)

        # Rank by score and match coverage
        results = []
        for doc_id, score in sorted(doc_scores.items(), key=lambda x: -x[1])[:limit * 2]:
            doc = self.documents[doc_id]
            matched_words = doc_matches[doc_id]
            coverage = len(matched_words & set(query_words)) / len(query_words) if query_words else 0

            # Find best matching sections
            best_sections = []
            for idx, section in enumerate(doc["sections"]):
                section_text = section["title"] + " " + " ".join(section["content"])
                section_lower = section_text.lower()
                section_score = sum(1 for w in expanded_words if w in section_lower)
                if section_score > 0:
                    # Extract snippet
                    snippet = self._extract_snippet(section_text, query_words)
                    best_sections.append({
                        "title": section["title"],
                        "snippet": snippet,
                        "score": section_score,
                    })

            best_sections.sort(key=lambda x: -x["score"])

            results.append({
                "file": doc["filename"],
                "title": doc["title"],
                "path": doc["path"],
                "score": score,
                "coverage": coverage,
                "matched_words": list(matched_words)[:10],
                "categories": categories,
                "sections": best_sections[:3],
            })

        # Final ranking by combined score
        results.sort(key=lambda x: -(x["score"] * (1 + x["coverage"])))
        return results[:limit]

    def _extract_snippet(self, text: str, query_words: list[str], max_length: int = 300) -> str:
        """Extract the most relevant snippet from text."""
        text_lower = text.lower()

        # Find best position (where most query words appear close together)
        best_pos = 0
        best_score = 0

        for word in query_words:
            pos = text_lower.find(word)
            if pos != -1:
                # Count nearby query words
                window = text_lower[max(0, pos-100):pos+200]
                score = sum(1 for w in query_words if w in window)
                if score > best_score:
                    best_score = score
                    best_pos = pos

        # Extract snippet around best position
        start = max(0, best_pos - 50)
        end = min(len(text), start + max_length)

        snippet = text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet


# Global index instance
_faq_index = FAQIndex()


async def faq_search(query: str) -> dict[str, Any]:
    """
    Smart search of the Ultrahuman CX Bible knowledge base.

    Uses:
    - Synonym expansion (battery → power, charge, drain, etc.)
    - TF-IDF ranking for relevance
    - Section-aware search
    - Category classification

    Args:
        query: Natural language search query

    Returns:
        dict with ranked search results and relevant snippets
    """
    if not FAQ_BASE_PATH.exists():
        return {
            "status": "error",
            "message": f"FAQ knowledge base not found at {FAQ_BASE_PATH}",
        }

    results = _faq_index.search(query, limit=5)

    if not results:
        return {
            "status": "no_results",
            "query": query,
            "message": f"No FAQ content found for: {query}",
            "suggestions": [
                "Try simpler keywords",
                "Check spelling",
                "Try: battery, sizing, warranty, sync, sleep, heart rate"
            ],
        }

    # Format response
    formatted_results = []
    for r in results:
        formatted_results.append({
            "title": r["title"],
            "file": r["file"],
            "relevance": round(r["score"], 2),
            "matched_terms": r["matched_words"],
            "categories": r["categories"],
            "answers": [
                {
                    "section": s["title"],
                    "content": s["snippet"],
                }
                for s in r["sections"]
            ],
        })

    return {
        "status": "success",
        "query": query,
        "results_count": len(formatted_results),
        "results": formatted_results,
        "source": "UH-CXbible Knowledge Base",
    }


async def faq_get_topics() -> dict[str, Any]:
    """Get available FAQ topics with descriptions."""
    if not FAQ_BASE_PATH.exists():
        return {
            "status": "error",
            "message": f"FAQ knowledge base not found",
        }

    # Ensure index is built
    _faq_index.build_index()

    topics = []
    for doc_id, doc in _faq_index.documents.items():
        section_titles = [s["title"] for s in doc["sections"] if s["title"]][:5]
        topics.append({
            "name": doc["title"],
            "file": doc["filename"],
            "sections": section_titles,
        })

    return {
        "status": "success",
        "topics_count": len(topics),
        "topics": topics,
        "categories": list(CATEGORIES.keys()),
    }


async def faq_answer(question: str) -> dict[str, Any]:
    """
    Get a direct answer to a FAQ question.

    This is a convenience wrapper that searches and formats
    the best answer for common questions.
    """
    result = await faq_search(question)

    if result["status"] != "success" or not result.get("results"):
        return {
            "status": "no_answer",
            "question": question,
            "message": "I couldn't find a specific answer to that question in the knowledge base.",
        }

    # Get the best answer
    top_result = result["results"][0]
    best_answer = top_result["answers"][0] if top_result["answers"] else None

    return {
        "status": "success",
        "question": question,
        "answer": best_answer["content"] if best_answer else "See the full article for details.",
        "source": {
            "title": top_result["title"],
            "section": best_answer["section"] if best_answer else "General",
            "file": top_result["file"],
        },
        "related_topics": top_result["categories"],
        "confidence": "high" if top_result["relevance"] > 2 else "medium" if top_result["relevance"] > 1 else "low",
    }


# Tool schemas for LLM
FAQ_TOOL_SCHEMAS = [
    {
        "name": "faq_search",
        "description": """Smart search of the Ultrahuman CX Bible knowledge base.

Use this for ANY general question about:
- Ring features, specs, hardware, colors, sizes
- Battery issues, charging, drain problems
- Warranty, replacements, returns, refunds
- App usage, troubleshooting, connectivity
- Health metrics (sleep, HR, HRV, steps, recovery)
- Integrations (Apple Health, Google Fit, Strava)
- Water resistance, durability
- Wabi-Sabi program, trade-in

The search automatically:
- Expands synonyms (battery → power, charge, drain)
- Ranks results by relevance
- Finds specific sections with answers
- Classifies into categories""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "faq_get_topics",
        "description": "Get list of all FAQ topics and categories available in the knowledge base.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "faq_answer",
        "description": "Get a direct answer to a specific FAQ question. Returns the best matching answer with confidence level.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The specific question to answer",
                }
            },
            "required": ["question"],
        },
    },
]

# Map tool names to functions
FAQ_TOOL_FUNCTIONS = {
    "faq_search": faq_search,
    "faq_get_topics": faq_get_topics,
    "faq_answer": faq_answer,
}

__all__ = [
    "FAQ_TOOL_SCHEMAS",
    "FAQ_TOOL_FUNCTIONS",
    "faq_search",
    "faq_get_topics",
    "faq_answer",
]
