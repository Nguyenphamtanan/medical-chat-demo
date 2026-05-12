import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List

from .translation import normalize_text


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class KnowledgeDoc:
    id: str
    specialty: str
    title: str
    text: str
    tags: List[str]


DEFAULT_DOCS = [
    KnowledgeDoc(
        id="hepatic_jaundice",
        specialty="hepatology",
        title="Jaundice and cholestasis",
        text=(
            "jaundice dark urine pruritus bilirubin cholestasis hepatitis biliary "
            "obstruction liver injury right upper quadrant abdominal pain pale stool"
        ),
        tags=["gan", "máº­t", "bilirubin", "vÃ ng da"],
    ),
    KnowledgeDoc(
        id="metabolic_diabetes",
        specialty="endocrinology",
        title="Diabetes and metabolic risk",
        text=(
            "diabetes mellitus fatty liver metabolic syndrome glucose renal function "
            "medication metformin cardiovascular risk"
        ),
        tags=["Ä‘Ã¡i thÃ¡o Ä‘Æ°á»ng", "gan nhiá»…m má»¡", "metformin"],
    ),
    KnowledgeDoc(
        id="infection_red_flags",
        specialty="infectious_disease",
        title="Systemic infection red flags",
        text=(
            "fever sepsis confusion hypotension tachycardia immunosuppression "
            "abdominal infection hepatitis cholangitis"
        ),
        tags=["sá»‘t", "nhiá»…m trÃ¹ng", "cáº¥p cá»©u"],
    ),
    KnowledgeDoc(
        id="cardiopulmonary_red_flags",
        specialty="cardiology",
        title="Cardiopulmonary danger signs",
        text="chest pain dyspnea syncope cyanosis edema shock severe weakness",
        tags=["Ä‘au ngá»±c", "khÃ³ thá»Ÿ"],
    ),
    KnowledgeDoc(
        id="gastro_abdominal",
        specialty="gastroenterology",
        title="Abdominal and hepatobiliary symptoms",
        text=(
            "abdominal pain nausea vomiting jaundice stool urine gallbladder pancreas "
            "bile duct ultrasound hepatomegaly"
        ),
        tags=["bá»¥ng", "siÃªu Ã¢m", "gan to"],
    ),
]


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(normalize_text(text))


class BM25KnowledgeBase:
    def __init__(self, docs: List[KnowledgeDoc]):
        self.docs = docs
        self.doc_tokens = [tokenize(" ".join([doc.title, doc.text, *doc.tags])) for doc in docs]
        self.doc_lengths = [len(tokens) or 1 for tokens in self.doc_tokens]
        self.avgdl = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.term_freqs = [Counter(tokens) for tokens in self.doc_tokens]
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        for tokens in self.doc_tokens:
            for token in set(tokens):
                self.doc_freqs[token] += 1

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_terms = tokenize(query)
        scores = []
        for idx, doc in enumerate(self.docs):
            score = self._score_doc(query_terms, idx)
            if score > 0:
                scores.append(
                    {
                        "id": doc.id,
                        "specialty": doc.specialty,
                        "title": doc.title,
                        "score": round(score, 4),
                        "tags": doc.tags,
                    }
                )
        return sorted(scores, key=lambda item: item["score"], reverse=True)[:top_k]

    def _score_doc(self, query_terms: List[str], doc_idx: int) -> float:
        k1 = 1.5
        b = 0.75
        score = 0.0
        tf = self.term_freqs[doc_idx]
        doc_len = self.doc_lengths[doc_idx]
        n_docs = len(self.docs)
        for term in query_terms:
            freq = tf.get(term, 0)
            if not freq:
                continue
            df = self.doc_freqs.get(term, 0)
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            denom = freq + k1 * (1 - b + b * doc_len / self.avgdl)
            score += idf * (freq * (k1 + 1)) / denom
        return score


@lru_cache(maxsize=1)
def get_knowledge_base() -> BM25KnowledgeBase:
    return BM25KnowledgeBase(DEFAULT_DOCS)
