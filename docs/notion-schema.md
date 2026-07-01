# Notion Database Schema

推奨DB名: `Content Automation Tasks`

| Property | Type | Purpose |
|---|---|---|
| `Name` | Title | タスク名 |
| `Status` | Status | `Ready`, `Generating`, `Needs Review`, `Published`, `Failed` |
| `Sources` | Rich text | 参考URLや素材メモ |
| `Theme` | Rich text | 配信テーマ |
| `Platforms` | Multi-select | YouTube, TikTok, Blog |
| `Quality Score` | Number | Quality Gateスコア |
| `Last Result` | Rich text | 生成・投稿結果 |
| `Published URL` | URL | 投稿URL |

最低限必要なのは `Name`, `Status`, `Sources` です。
