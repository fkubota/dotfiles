---
name: query-db
description: staging/hotfix/production環境のPostgreSQLにSSHトンネル経由で読み取り専用クエリを実行する
disable-model-invocation: false
---

# DB クエリ実行コマンド

## 目的

staging / hotfix / production 環境のPostgreSQLデータベースに対してクエリを実行する。

## 最重要ルール（クエリ実行の順序）

クエリを1回実行するたびに、必ず以下の順序を守る。**SSHトンネル・パスワードが既に揃っていて接続手順（1〜5）を省略できる場合でも、このルールは省略できない。**

1. **実行前**: なぜこのクエリを実行するのか目的を一言説明する
2. **実行前**: 実行するSQL文をコードブロックで提示する
3. ここで実際にクエリを実行する（psqlコマンド）
4. **実行後**: 結果をMarkdownの表に整形して表示する

調査のために複数回試行する場合も、**各回で**この順序を守る（まとめて最後に一括表示しない）。「調査の途中経過だから」「軽い確認クエリだから」は省略の理由にならない。

## 接続情報

| 項目 | 値 |
|------|-----|
| Host | localhost |
| Port | 5432 |
| User | table_plus |
| Password | ユーザーに確認 |
| Database | foodies |

## 実行手順

### 1. 環境の選択

ユーザーに接続する環境を確認する：

> 「どの環境に接続しますか？（staging / hotfix / production）」

### 2. AWS SSO ログイン

```bash
aws sso login --profile goals-hanzo
```

### 3. SSHトンネル確認・起動

```bash
lsof -iTCP:5432 -sTCP:LISTEN
```

未接続の場合はバックグラウンドで起動する。環境に応じて以下のコマンドを使用：

#### staging

```bash
ssh -f -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -L 5432:database.staging.internal.foodies.jp:5432 \
    -i ~/.ssh/minedup.pem \
    -p 22 ec2-user@staging.bastion.hanzo.cloud
```

#### hotfix

```bash
ssh -f -N \
    -L 5432:database.hotfix.internal.foodies.jp:5432 \
    -i ~/.ssh/minedup.pem \
    -p 22 ec2-user@hotfix.bastion.hanzo.cloud
```

#### production

```bash
ssh -f -N \
    -L 5432:readerdatabase.production.internal.foodies.jp:5432 \
    -i ~/.ssh/minedup.pem \
    -p 22 ec2-user@production.bastion.hanzo.cloud
```

### 4. パスワードの確認

ユーザーにデータベースのパスワードを確認する（「DBのパスワードを教えてください（いつものやつです）」）。

### 5. 接続確認

```bash
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "SELECT 1;"
```

#### トラブルシューティング

| エラー | 対処 |
|--------|------|
| SSO認証エラー | `aws sso login --profile goals-hanzo` を再実行 |
| SSHトンネル接続失敗 | AWS SSOの有効期限切れの可能性。SSO再ログイン後にリトライ |
| psql接続失敗 | トンネルが起動しているか `lsof -iTCP:5432` で確認 |

### 6. クエリ実行

**冒頭の「最重要ルール（クエリ実行の順序）」を必ず守る**（説明→SQL提示→実行→結果表示。結果は目安10行程度、それ以上ある場合は全体件数を添える）。

```bash
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "<SQL文>"
```

### 例（手順 6）

```bash
# テーブル一覧
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "\dt"

# shopsテーブルの先頭5件
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "SELECT * FROM shops LIMIT 5;"

# レコード数カウント
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "SELECT COUNT(*) FROM shops;"
```

## SSHトンネルの終了

作業完了後、SSHトンネルを終了する場合:

```bash
# SSHトンネルのプロセスを確認
lsof -i :5432

# プロセスを終了
kill <PID>
```

## 複数対象クエリの軽量化（高速PDCAのために必須）

複数の食材・店舗・日付などを対象にするクエリは、**必ずサブクエリでLIMITをかけてから結合**すること。
本番データは大量のため、絞らずにJOINすると非常に重くなる。

### 基本パターン：サブクエリでLIMIT

```sql
-- NG: そのままJOINすると全件スキャンで重い
SELECT * FROM orders
LEFT JOIN order_items ON orders.id = order_items.order_id
LEFT JOIN shops ON orders.shop_id = shops.id;

-- OK: ベーステーブルをLIMITで絞ってからJOIN
SELECT *
FROM (SELECT * FROM orders LIMIT 100) AS o
LEFT JOIN order_items ON o.id = order_items.order_id
LEFT JOIN shops ON o.shop_id = shops.id;
```

### 条件を加えてさらに絞る

```sql
-- 特定の店舗IDや日付範囲で絞ってからJOIN
SELECT *
FROM (
  SELECT * FROM orders
  WHERE shop_id IN (1, 2, 3)
    AND created_at >= '2024-01-01'
  LIMIT 50
) AS o
LEFT JOIN order_items ON o.id = order_items.order_id;
```

### 食材・タグなど多対多の場合

```sql
-- ingredientsをLIMITで絞って関連データを取得
SELECT *
FROM (SELECT * FROM ingredients LIMIT 20) AS i
LEFT JOIN dish_ingredients ON i.id = dish_ingredients.ingredient_id
LEFT JOIN dishes ON dish_ingredients.dish_id = dishes.id;
```

### PDCAのコツ

1. **まずLIMIT 10〜50で動作確認** → 結果の形・カラムを確認
2. **条件を追加・調整** → WHERE句でさらに絞り込む
3. **正しければLIMITを外すか増やす** → 全件または必要数で実行
4. **重い場合はEXPLAIN ANALYZEで確認**

```sql
-- クエリの実行計画を確認
EXPLAIN ANALYZE
SELECT * FROM (SELECT * FROM shops LIMIT 10) AS s
LEFT JOIN orders ON s.id = orders.shop_id;
```

## 注意事項

- **読み取り専用**: 各環境は読み取り専用権限のみ
- **productionは本番データ**: 実際のユーザーデータが含まれているため慎重に扱うこと
- **ポート競合**: ローカルでPostgreSQLが起動している場合は停止するか、別ポートを使用すること
- **重いクエリに注意**: LIMITなしの大規模JOINは環境に負荷をかけるため避けること
- **説明→クエリ提示→実行→結果表示の順序を必ず守ること**: 詳細は「6. クエリ実行」参照。実行前の説明・クエリ提示を省略したり、実行後にまとめて表示したりしない。
