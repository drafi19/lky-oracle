"""Offline BM25 retrieval over the speech chunks."""

from __future__ import annotations

import math
import re
from collections import Counter

from lkybot.corpus import Chunk

TOKEN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = ["a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "for", "from", "had", "has", "have", "he", "her", "his", "i", "if", "in", "into", "is", "it", "its", "me", "my", "no", "not", "of", "on", "or", "our", "so", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those", "to", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will", "with", "you", "your"]
STOP = set(_STOP_WORDS)

def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if len(t) > 1 and t not in STOP]


class BM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.4, b: float = 0.75) -> None:
        self.chunks = chunks
        self.freqs = [Counter(tokenize(chunk.text)) for chunk in chunks]
        self.lengths = [sum(f.values()) for f in self.freqs]
        self.avg_length = sum(self.lengths) / max(1, len(self.lengths))
        self.k1 = k1
        self.b = b
        document_freq: Counter[str] = Counter()
        for freq in self.freqs:
            document_freq.update(freq.keys())
        total = len(chunks)
        self.idf = {
            term: math.log(1 + (total - count + 0.5) / (count + 0.5))
            for term, count in document_freq.items()
        }

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        terms = tokenize(query)
        scored: list[tuple[float, int]] = []
        for position, freq in enumerate(self.freqs):
            score = 0.0
            for term in terms:
                tf = freq.get(term)
                if not tf:
                    continue
                denom = tf + self.k1 * (
                    1 - self.b + self.b * self.lengths[position] / self.avg_length
                )
                score += self.idf[term] * tf * (self.k1 + 1) / denom
            if score > 0:
                scored.append((score, position))
        scored.sort(key=lambda row: (-row[0], row[1]))
        return [(self.chunks[pos], score) for score, pos in scored[:k]]
