from pathlib import Path

from creator_pipeline.ingest import load_sources_from_dir


def test_load_sources_from_markdown(tmp_path: Path) -> None:
    source = tmp_path / "first-note.md"
    source.write_text("本文です", encoding="utf-8")
    loaded = load_sources_from_dir(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].title == "First Note"
    assert loaded[0].body == "本文です"


def test_load_sources_from_json(tmp_path: Path) -> None:
    source = tmp_path / "sources.json"
    source.write_text('{"sources":[{"title":"A","body":"本文A"},{"title":"B","body":"本文B"}]}', encoding="utf-8")
    loaded = load_sources_from_dir(tmp_path)
    assert [item.title for item in loaded] == ["A", "B"]
