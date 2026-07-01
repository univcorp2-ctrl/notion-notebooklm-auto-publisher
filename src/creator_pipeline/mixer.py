from __future__ import annotations

import json
import textwrap

from openai import OpenAI

from .config import Settings
from .models import ContentPackage, ContentSource


def build_content_package(sources: list[ContentSource], theme: str, settings: Settings) -> ContentPackage:
    if len(sources) < 2 and not settings.dry_run:
        raise ValueError("本番モードでは2つ以上の素材が必要です。")
    if settings.openai_api_key and not settings.dry_run:
        package = _build_with_openai(sources, theme, settings)
        if package:
            return package
    return _build_fallback(sources, theme)


def _build_with_openai(sources: list[ContentSource], theme: str, settings: Settings) -> ContentPackage | None:
    client = OpenAI(api_key=settings.openai_api_key)
    source_block = "\n\n".join(f"SOURCE {i + 1}: {s.title}\nURL: {s.source_url or 'n/a'}\n{s.body[:3500]}" for i, s in enumerate(sources))
    prompt = f"""あなたはAI量産コンテンツではなく独自価値のある日本語コンテンツを作る編集長です。
テーマ: {theme}
条件: 2つ以上の素材を比較し、共通点、差分、矛盾、具体例、視聴者の実用価値を示す。ラジオ風2人会話台本、記事、概要、説明文、ハッシュタグ、画像プロンプトを作る。元素材の丸写しを避ける。JSONのみで返す。
JSON keys: title, summary, script, article, description, hashtags, image_prompts
素材:
{source_block}"""
    try:
        response = client.chat.completions.create(model=settings.openai_text_model, messages=[{"role": "system", "content": "Return strict JSON. No markdown fences."}, {"role": "user", "content": prompt}], temperature=0.7)
        payload = json.loads(response.choices[0].message.content or "{}")
        return ContentPackage(title=payload["title"], theme=theme, script=payload["script"], article=payload["article"], summary=payload["summary"], description=payload["description"], hashtags=list(payload.get("hashtags") or []), image_prompts=list(payload.get("image_prompts") or []), sources=sources)
    except Exception:
        return None


def _build_fallback(sources: list[ContentSource], theme: str) -> ContentPackage:
    first = sources[0]
    second = sources[1] if len(sources) > 1 else sources[0]
    title = f"{theme}: {first.title} と {second.title} から作る実用AIラジオ"
    source_summaries = "\n".join(f"- 素材{i + 1}: {s.title} / {s.body[:160].replace(chr(10), ' ')}" for i, s in enumerate(sources[:4]))
    hashtags = ["#AI活用", "#NotebookLM", "#Notion", "#コンテンツ自動化", "#クリエイター"]
    script = textwrap.dedent(f"""
    A: 今日のテーマは「{theme}」です。単なる要約ではなく、複数の素材を比較して見える違いを話します。
    B: 素材の由来です。\n{source_summaries}
    A: 共通しているのは、情報をただ保存するだけでは価値にならないという点です。Notionのタスク、NotebookLMの音声、手元のメモをつなげることで制作の流れが見えます。
    B: 一方で違いもあります。{first.title} は入口や管理、{second.title} は表現や配信に近い。ここを混ぜると、ただのAI自動化ではなく編集システムになります。
    A: 矛盾点もあります。完全自動化を求めるほど、投稿プラットフォームの審査、著作権、認証、品質チェックは厳しくなります。
    B: だから自動化の中に、独自性と出典確認のQuality Gateを入れます。具体例として、NotebookLMのラジオ風メモをそのまま転載せず、別のNotionタスクや調査メモと比較します。
    A: 視聴者に役立つのは、情報の羅列ではなく、明日使える判断軸です。{hashtags[0]} {hashtags[1]} {hashtags[2]}
    """).strip()
    article = textwrap.dedent(f"""
    # {title}

    今回の素材は、{', '.join(s.title for s in sources[:4])} です。この記事では、これらの素材を単純に要約するのではなく、Notionでのタスク管理、NotebookLM由来のラジオ的なやりとり、動画配信までをひとつの制作パイプラインとして捉え直します。

    ## なぜ今、この自動化が必要なのか

    生成AIの出力は増え続けていますが、量だけでは視聴者に届きません。価値が出るのは、複数の素材を比較し、違いを見つけ、矛盾を整理し、視聴者の行動に変換したときです。

    ## 素材同士の比較

    素材A「{first.title}」は制作の入口を整理する視点を持っています。素材B「{second.title}」は視聴者に届く形へ変換する視点を持っています。この2つを混ぜると、単なるメモ管理でも単なる動画生成でもなく、継続的に投稿できる編集システムになります。

    ## 矛盾と注意点

    完全自動化を目指すほど、AIスロップ化のリスクが上がります。素材の意味を確認しないまま、似た構成、薄い結論を量産しやすいからです。本パイプラインでは、2つ以上の素材、比較、反論、出典言及、コピー率、汎用表現をQuality Gateとして確認します。

    ## 実務での使い方

    Notionに配信テーマをタスク化し、NotebookLMやローカルメモから素材を取り込みます。AIは記事とラジオ台本を作り、GPT Image 2で画像を作り、TTSで音声化し、FFmpegで縦型動画へ変換します。最後にYouTubeとTikTokへ投稿し、Notionへ結果を戻します。

    ## 出典・素材の由来

    {source_summaries}

    ## 結論

    独自価値は、AIを使ったかどうかではなく、素材をどう組み合わせたかで決まります。視聴者に役立つのは、情報の羅列ではなく、比較から生まれる判断軸です。{' '.join(hashtags)}
    """).strip()
    return ContentPackage(title=title, theme=theme, script=script, article=article, summary="複数素材を混ぜ、AIスロップ化を避けながら記事・音声・縦動画・配信まで自動化する提案です。", description="NotionとNotebookLM由来の素材を組み合わせ、独自価値のあるAIラジオ/記事/動画を自動生成する実験です。", hashtags=hashtags, image_prompts=[f"Vertical 9:16 editorial illustration, Japanese creator desk, Notion task board, NotebookLM audio waves, YouTube and TikTok publishing pipeline, clean modern style, theme: {theme}", "Vertical 9:16 diagram showing two source documents merging into radio audio, article text, and short video frames, premium Japanese tech magazine aesthetic"], sources=sources)
