---
name: sql-format
description: SQLを書くとき・例示するときのフォーマットルール。SQL作成、クエリ作成、SQLフォーマットに関連するタスクで参照。
---

# SQL Format Rules

SQLを書くとき・例示するときは以下のフォーマットに従う。

## クエリ保存ルール

作成したSQLクエリは以下のルールで保存する:

- **保存先**: `~/sandpit/YYYYMMDD/` ディレクトリ（当日の日付）
- **ディレクトリ作成**: 存在しない場合は `mkdir -p` で作成
- **ファイル名**: クエリの目的がわかる名前（例: `yoy_sales_query.sql`, `monthly_summary.sql`）
- **ファイル形式**: `.sql` 拡張子
- **ヘッダコメント**: ファイル先頭に以下を記載
  - クエリの目的
  - 主要なパラメータ（company_id等）
  - 対象データの説明

## 基本ルール

- **すべて小文字** - キーワード（select, from, where, left join など）も小文字
- **カンマは行頭** - 2つ目以降のカラムは `, column_name` の形式

## CTE (Common Table Expression)

```sql
with config as (
select
    hoge1
    , hoge2
)

, tbl as (
select *
from aaa
)
```

- 最初のCTEは `with xxx as (`
- 2つ目以降は `, xxx as (` （行頭カンマ）
- CTE間は空行を入れる

## SELECT句

```sql
select
    column1
    , column2
    , column3
```

- 1カラム目はインデントのみ
- 2カラム目以降は行頭カンマ `    , column`

## JOIN

```sql
-- 単一条件: 同じ行に書く
left join bbb b on a.id = b.id

-- 複数条件: 改行してインデント
left join ccc c
    on a.id = c.id
    and a.key = c.key
```

## WHERE句

```sql
where 1=1
    and a.status = 'active'
    and a.date >= '2024-01-01'
```

- `where 1=1` を使用
- 条件は次行にインデントして `and` で始める

## 完全な例

```sql
with config as (
select
    hoge1
    , hoge2
)

, tbl as (
select *
from aaa a
left join bbb b on a.abc = b.abc
left join ccc c
    on a.abc = c.abc
    and a.def = c.def
where 1=1
    and a.xxx = 'xxx'
)

select *
from tbl t
order by t.date
```
