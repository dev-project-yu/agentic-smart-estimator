from __future__ import annotations

import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RAGService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self.reference_path = self.base_dir / "data" / "reference_documents.md"
        self.documents = self._load_documents()
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.index = self.vectorizer.fit_transform([doc["content"] for doc in self.documents])

    def _load_documents(self):
        text = self.reference_path.read_text(encoding="utf-8")
        sections = re.split(r"(?m)^## ", text)
        items = []
        for section in sections:
            if not section.strip():
                continue
            title, _, body = section.partition("\n")
            content = body.strip() if body.strip() else title.strip()
            title = title.strip()
            if not title:
                continue
            items.append({"title": title, "content": content})
        return items

    def retrieve(self, query: str, top_k: int = 3):
        if not self.documents:
            return []
        query_vector = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vector, self.index).flatten()
        ranked = sorted(enumerate(sims), key=lambda item: item[1], reverse=True)
        hits = []
        for idx, score in ranked[:top_k]:
            item = self.documents[idx]
            hits.append({
                "title": item["title"],
                "score": round(float(score), 4),
                "snippet": item["content"][:220],
            })
        return hits
