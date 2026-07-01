# Setup Guide

## 1. GitHub Secrets

Repository Settings → Secrets and variables → Actions → New repository secret から必要な値を登録します。

必須ではなく、dry-runなら空で動きます。本番配信時だけ以下が必要です。

- `OPENAI_API_KEY`
- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`
- `YOUTUBE_TOKEN_JSON`
- `TIKTOK_ACCESS_TOKEN`
- `NOTEBOOKLM_ENTERPRISE_ACCESS_TOKEN`
- `NOTEBOOKLM_ENTERPRISE_API_BASE`
- `NOTEBOOKLM_NOTEBOOK_RESOURCE`

## 2. Notion

1. Notion Integrationを作成します。
2. タスクDBを作成します。
3. DBにIntegrationを招待します。
4. DB IDを `NOTION_DATABASE_ID` に入れます。

推奨プロパティは [docs/notion-schema.md](notion-schema.md) を参照してください。

## 3. NotebookLM

NotebookLM Enterpriseを使える場合はEnterprise APIを使います。個人版やAPI未利用の場合は、NotebookLMで生成したノート、要約、音声概要の文字起こしを `data/notebooklm_exports/` に `.md` / `.txt` / `.json` として保存すれば取り込めます。

## 4. YouTube

YouTube投稿はYouTube Data APIのOAuth認証が必要です。`youtube.upload` scopeを含むrefresh token入りJSONを `YOUTUBE_TOKEN_JSON` に登録します。

## 5. TikTok

TikTok Developer AppでContent Posting APIのDirect Postを使える状態にし、access tokenを `TIKTOK_ACCESS_TOKEN` に登録します。審査や権限付与はTikTok側の画面操作が必要です。

## 6. Actionsで実行

Actions → Generate and Publish Content → Run workflow

- 最初は `dry_run=true`, `publish=true`
- 生成物を確認
- 問題なければ `dry_run=false`, `publish=true`

## 本番で必要なもの

- 各APIのアカウントと利用規約への同意
- YouTube/TikTokの投稿権限
- OpenAI API利用枠
- FFmpegが入った実行環境。GitHub Actionsでは自動インストール済み
