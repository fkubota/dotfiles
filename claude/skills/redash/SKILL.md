---
name: redash
description: Redash APIを使ってクエリ情報・結果を取得・分析する。ユーザーがRedashのURLを貼った場合、「Redashを確認して」「このクエリを見て」などRedashへのアクセスが必要な場面で自動的に使用する。
user-invocable: false
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

## 実行前の提示ルール（必須）

クエリを**実行（POST）する前に**、何が実行されるかを必ずユーザーに提示する：

- **保存済みクエリの実行**: クエリID・クエリ名・渡すパラメータ・Redash URL（`https://redash.hanzo.cloud/queries/{query_id}`）を提示してから実行する。SQL 全文の提示は不要（求められたときに提示する）
- **新規・アドホックなSQLを書く場合**: 実行前に SQL 全文を提示する（`sql-format` スキルのルールを適用）
- 複数クエリをまとめて実行する場合は、一覧（ID・名前・パラメータ）を先に提示してよい。1件ずつ承認を待つ必要はない
- キャッシュ済み結果の GET（読み取りのみ）はこのルールの対象外

## 実行フロー

### 1. API キーの確認

```bash
fish -c 'source ~/.config/fish/secrets.fish; echo $REDASH_API_KEY'
```

値が空の場合は「API キー未設定」として、以下のセットアップ手順を案内する。

---

## API キーのセットアップ（未設定の場合）

### 1. Redash から API キーを取得する

1. ブラウザで `https://redash.hanzo.cloud` を開いてログイン
2. 右上のアカウントアイコン → **Edit Profile** をクリック
3. ページ下部の **API Key** セクションに表示されている文字列をコピー

### 2. secrets.fish に追記して永続化する

```bash
echo 'set -x REDASH_API_KEY "ここにコピーしたAPIキーを貼り付け"' >> ~/.config/fish/secrets.fish
```

### 3. 現在のセッションに即時反映する

```bash
fish -c 'source ~/.config/fish/secrets.fish; echo $REDASH_API_KEY'
```

値が表示されれば設定完了。

> **注意**: `secrets.fish` は `.gitignore` に入れておくこと。dotfiles リポジトリに API キーをコミットしない。

---

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

以下のいずれかの場合のみ実行する（実行前に「実行前の提示ルール」に従うこと）：
- ユーザーが最新データを要求した場合
- パラメータ付きクエリで、目的のパラメータに対応するキャッシュ結果が無い場合（キャッシュは最後に実行されたパラメータの結果しか持たないため）

```
POST https://redash.hanzo.cloud/api/queries/{query_id}/results
Body: {"max_age": 0}
```

### 5. パラメータ付きクエリの実行

パラメータ定義は `GET /api/queries/{query_id}` の `options.parameters` から取得する。
実行は POST の Body に `parameters` を含める：

```
POST https://redash.hanzo.cloud/api/queries/{query_id}/results
Body: {"parameters": {"param_name": "value", ...}, "max_age": 0}
```

- レスポンスに `job` が含まれる場合は非同期実行。`GET /api/jobs/{job_id}` をポーリングし、`status=3`（成功）になったら `query_result_id` で結果を取得する。`status=4,5` は失敗
- ダッシュボードURL（`/dashboard/{slug}?p_xxx=...`）を渡された場合は、`GET /api/dashboards/{slug}` でウィジェット一覧からクエリIDを特定し、`p_` プレフィックスを除いた名前でパラメータを対応づける

## トラブルシューティング

| エラー | 対処 |
|--------|------|
| 401 Unauthorized | `$REDASH_API_KEY` が未設定または間違い |
| 404 Not Found | query_id / result_id が間違い。URL を再確認 |
| ログインページにリダイレクト | API キーをクエリパラメータに付けていない |
