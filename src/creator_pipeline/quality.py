from __future__ import annotations

import re
from collections import Counter

from .models import ContentSource, QualityReport

GENERIC_AI_PHRASES = ["深掘りしていきます", "重要なのは", "本記事では", "いかがでしたか", "まとめると", "現代社会において", "様々な観点", "興味深い"]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9一-龯ぁ-んァ-ン]+", text.lower())


def jaccard_similarity(a: str, b: str) -> float:
    sa = set(tokenize(a))
    sb = set(tokenize(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def top_terms(text: str, limit: int = 10) -> list[str]:
    tokens = [t for t in tokenize(text) if len(t) >= 2]
    return [term for term, _ in Counter(tokens).most_common(limit)]


def assess_quality(sources: list[ContentSource], script: str, article: str, min_score: int = 70) -> QualityReport:
    flags: list[str] = []
    score = 100
    if len(sources) < 2:
        score -= 35
        flags.append("2つ以上の素材がありません。本番配信には複数ソースが必要です。")
    combined_output = f"{script}\n\n{article}"
    if len(tokenize(combined_output)) < 220:
        score -= 15
        flags.append("出力が短すぎます。具体例、反論、実用価値を追加してください。")
    generic_hits = [phrase for phrase in GENERIC_AI_PHRASES if phrase in combined_output]
    if generic_hits:
        score -= min(18, len(generic_hits) * 4)
        flags.append(f"汎用的なAI表現が多い可能性があります: {', '.join(generic_hits[:5])}")
    novelty_terms = ["比較", "違い", "矛盾", "反論", "具体例", "実務", "なぜ今", "視聴者"]
    novelty_hits = sum(1 for term in novelty_terms if term in combined_output)
    if novelty_hits < 3:
        score -= 18
        flags.append("比較・反論・具体例など、独自価値を示す要素が不足しています。")
    source_coverage = 0
    for source in sources:
        if any(term in combined_output for term in top_terms(source.title + " " + source.body, limit=8)):
            source_coverage += 1
    coverage_ratio = source_coverage / max(len(sources), 1)
    if coverage_ratio < 0.75:
        score -= 15
        flags.append("一部の素材が出力に十分反映されていません。")
    max_similarity = max((jaccard_similarity(source.body, article) for source in sources), default=0.0)
    if max_similarity > 0.55:
        score -= 18
        flags.append("元素材に近すぎる文章があります。新しい構成にしてください。")
    if not any(marker in article for marker in ["出典", "素材", "参考", "由来", "ソース"]):
        score -= 8
        flags.append("本文内に素材の由来や出典への言及が不足しています。")
    score = max(0, min(100, score))
    return QualityReport(score=score, passed=score >= min_score, flags=flags, checks={"source_count": len(sources), "token_count": len(tokenize(combined_output)), "generic_phrase_hits": len(generic_hits), "novelty_hits": novelty_hits, "source_coverage_ratio": round(coverage_ratio, 3), "max_source_similarity": round(max_similarity, 3)})
