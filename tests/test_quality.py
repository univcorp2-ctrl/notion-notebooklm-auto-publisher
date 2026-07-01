from creator_pipeline.models import ContentSource
from creator_pipeline.quality import assess_quality, jaccard_similarity


def test_quality_rewards_multi_source_original_output() -> None:
    sources = [ContentSource(title="Notion", body="Notionでタスク管理をする。素材URLと進捗を記録する。"), ContentSource(title="NotebookLM", body="NotebookLMで音声概要を作る。別素材と比較して価値を足す。")]
    article = "出典素材としてNotionとNotebookLMを比較する。違い、矛盾、具体例、視聴者の実務価値を示し、単なる要約ではなく判断軸を作る。" * 8
    script = "A: NotionとNotebookLMの比較です。B: 具体例と反論を入れ、視聴者が明日使える形にします。" * 8
    report = assess_quality(sources, script, article, min_score=70)
    assert report.score >= 70
    assert report.passed is True


def test_quality_penalizes_single_source() -> None:
    sources = [ContentSource(title="Only", body="短い素材")]
    report = assess_quality(sources, "短い", "短い", min_score=70)
    assert report.score < 70
    assert report.passed is False


def test_jaccard_similarity_bounds() -> None:
    assert jaccard_similarity("a b c", "a b") <= 1
    assert jaccard_similarity("a", "z") == 0
