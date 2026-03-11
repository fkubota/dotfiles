# Staging DB クエリ実行コマンド

## 目的

Staging環境のPostgreSQLデータベースに対してクエリを実行する。

## 接続情報

| 項目 | 値 |
|------|-----|
| Host | localhost |
| Port | 5432 |
| User | table_plus |
| Password | ユーザーに確認 |
| Database | foodies |

## 実行手順

### 1. SSHトンネル接続

まず、SSHトンネルをバックグラウンドで起動する。

```bash
ssh -f -N \
    -L 5432:database.staging.internal.foodies.jp:5432 \
    -i ~/.ssh/minedup.pem \
    -p 22 ec2-user@staging.bastion.hanzo.cloud
```

**オプション説明:**
- `-f`: バックグラウンドで実行
- `-N`: リモートコマンドを実行しない（ポートフォワーディング専用）

### 2. パスワードの確認

ユーザーにStagingデータベースのパスワードを確認する。

### 3. 接続確認

```bash
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "SELECT 1;"
```

### 4. クエリ実行

```bash
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "<SQL文>"
```

### 例

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

- **読み取り専用**: Staging環境は読み取り専用権限のみ
- **本番環境ではない**: テストデータが含まれている可能性あり
- **ポート競合**: ローカルでPostgreSQLが起動している場合は停止するか、別ポートを使用すること
- **重いクエリに注意**: LIMITなしの大規模JOINはStaging環境に負荷をかけるため避けること
