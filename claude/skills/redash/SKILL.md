---
name: redash
description: Redash APIを使ってクエリ情報・結果を取得・分析する。ユーザーがRedashのURLを貼った場合、「Redashを確認して」「このクエリを見て」などRedashへのアクセスが必要な場面で自動的に使用する。
---

# Redash アクセススキル

ユーザーが Redash のURLを提示したとき、またはRedashのクエリ・結果を確認・分析する必要があるときに実行する。

## 接続情報

| 項目 | 値 |
|------|-----|
| Base URL | `https://redash.hanzo.cloud` |
| API Key | 環境変数 `$REDASH_API_KEY`（`~/.config/fish/secrets.fish` で設定済み） |

API キーは必ず環境変数から読み取る。ハードコードしない。

## URL からの ID 抽出

ユーザーが Redash URL を渡してきた場合、以下のパターンで ID を抽出する：

| URL パターン | 抽出できるもの |
|------------|--------------|
| `/queries/{query_id}/source#{result_id}` | query_id, result_id の両方 |
| `/queries/{query_id}` | query_id のみ |

## 実行フロー

### 1. API キーの確認

```bash
echo $REDASH_API_KEY
```

未設定の場合はユーザーに伝える：「`~/.config/fish/secrets.fish` に `REDASH_API_KEY` が設定されていません。設定してから再度お試しください。」

### 2. クエリ情報の取得（SQL・タイトル確認）

```
GET https://redash.hanzo.cloud/api/queries/{query_id}?api_key={REDASH_API_KEY}
```

取得後に提示する情報：
- `name`: クエリ名
- `query`: SQL 本文
- `schedule`: 実行スケジュール
- 作成者・更新日時

### 3. クエリ結果の取得

result_id がある場合は特定の結果を取得：
```
GET https://redash.hanzo.cloud/api/query_results/{result_id}?api_key={REDASH_API_KEY}
```

result_id がない場合は最新結果を取得：
```
GET https://redash.hanzo.cloud/api/queries/{query_id}/results?api_key={REDASH_API_KEY}
```

取得後に提示する情報：
- 列名・列数
- 行数
- 先頭5件のサンプルデータ
- 取得日時（`retrieved_at`）
- 行数が多い場合は「全件表示しますか？」と確認する

### 4. クエリの再実行（必要な場合のみ）

ユーザーが最新データを要求した場合のみ実行：
```
POST https://redash.hanzo.cloud/api/queries/{query_id}/results
Body: {"max_age": 0}
```

## トラブルシューティング

| エラー | 対処 |
|--------|------|
| 401 Unauthorized | `$REDASH_API_KEY` が未設定または間違い |
| 404 Not Found | query_id / result_id が間違い。URL を再確認 |
| ログインページにリダイレクト | API キーをクエリパラメータに付けていない |
