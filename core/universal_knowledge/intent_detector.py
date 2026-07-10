import re
import logging
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class IntentDetector:
    def __init__(self):
        self._keyword_patterns: Dict[str, List[str]] = {}
        self._module_descriptions: Dict[str, str] = {}
        self._embeddings_cache: Dict[str, List[float]] = {}
        self._initialized = False

    def initialize(self, module_registry: Dict[str, Dict]):
        for module_name, info in module_registry.items():
            keywords = info.get("keywords", [])
            self._keyword_patterns[module_name] = keywords

            description = info.get("description", "")
            self._module_descriptions[module_name] = description

        self._initialized = True
        logger.info(f"IntentDetector inicializado com {len(module_registry)} módulos")

    def detect_intent(self, query: str) -> List[Tuple[str, float]]:
        if not self._initialized:
            logger.warning("IntentDetector não inicializado")
            return []

        query_lower = query.lower().strip()

        keyword_results = self._detect_by_keywords(query_lower)

        semantic_results = self._detect_by_semantics(query_lower)

        combined = self._combine_results(keyword_results, semantic_results)

        combined.sort(key=lambda x: x[1], reverse=True)

        return combined[:5]

    def _detect_by_keywords(self, query: str) -> Dict[str, float]:
        results = {}

        for module_name, keywords in self._keyword_patterns.items():
            score = 0.0
            matched_keywords = []

            for keyword in keywords:
                keyword_lower = keyword.lower()

                if keyword_lower in query:
                    score += 1.0
                    matched_keywords.append(keyword)

                elif self._fuzzy_match(query, keyword_lower):
                    score += 0.7
                    matched_keywords.append(keyword)

            if score > 0:
                results[module_name] = min(score, 1.0)

        return results

    def _fuzzy_match(self, text: str, pattern: str, threshold: float = 0.8) -> bool:
        words = text.split()
        pattern_words = pattern.split()

        for i in range(len(words) - len(pattern_words) + 1):
            chunk = " ".join(words[i:i + len(pattern_words)])
            similarity = SequenceMatcher(None, chunk, pattern).ratio()
            if similarity >= threshold:
                return True

        return False

    def _detect_by_semantics(self, query: str) -> Dict[str, float]:
        results = {}

        query_words = set(query.lower().split())

        for module_name, description in self._module_descriptions.items():
            if not description:
                continue

            desc_words = set(description.lower().split())

            common_words = query_words.intersection(desc_words)

            if common_words:
                score = len(common_words) / max(len(query_words), len(desc_words))
                results[module_name] = min(score * 2, 1.0)

        return results

    def _combine_results(self, keyword_results: Dict[str, float],
                         semantic_results: Dict[str, float]) -> List[Tuple[str, float]]:
        combined = {}

        for module_name, score in keyword_results.items():
            combined[module_name] = score * 0.7

        for module_name, score in semantic_results.items():
            if module_name in combined:
                combined[module_name] += score * 0.3
            else:
                combined[module_name] = score * 0.3

        return [(name, score) for name, score in combined.items()]

    def add_keywords(self, module_name: str, keywords: List[str]):
        if module_name in self._keyword_patterns:
            self._keyword_patterns[module_name].extend(keywords)
        else:
            self._keyword_patterns[module_name] = keywords

    def update_description(self, module_name: str, description: str):
        self._module_descriptions[module_name] = description

    def get_keyword_stats(self) -> Dict[str, int]:
        return {name: len(keywords)
                for name, keywords in self._keyword_patterns.items()}
