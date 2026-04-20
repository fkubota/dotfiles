---
name: sql-format
description: "SQLフォーマットルール。TRIGGER:「SQL書いて」「クエリ書いて」「クエリサンプル」等のSQL関連の依頼時、またはSQLを含む回答を生成するとき。SQLコードを表示する前に必ず適用すること。"
user-invocable: false
---

# SQL Format Rules

SQLを書くとき・例示するときは以下のフォーマットに従う。

## クエリ保存ルール

作成したSQLクエリは以下のルールで保存する:

- 保存して欲しい時だけ保存する。  
- **他のコマンド/スキルが保存先を指定している場合は、そちらを優先する。**
- **保存先**: 保存先の指定がない場合は、`~/sandpit/YYYYMMDD/` ディレクトリ（当日の日付）
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
- with句の中身は、最初にインデントを入れない。(select, fromなどが一番左から始まる。)

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

## テスト (Test-Driven SQL)

クエリの正しさをCTEで検証する。テストは `test` CTEにまとめ、末尾で `cross join test` して実行する。

### エラー表現（PostgreSQL用）

PostgreSQLには `error()` 関数がないため、以下で代用する:

```sql
cast(date(cast('ここにエラーメッセージ' as text)) as text)
```

文字列をdateにキャストしようとして失敗することでエラーを発生させる。

### テストのカテゴリ

テストは以下の4種類に分類できる:

| | 単一テーブル | テーブル間 |
|---|---|---|
| **行レベル** | NULLチェック、負値チェック | 計算値の一致確認 |
| **集計レベル** | 合計値の検証 | レコード数の保全確認 |

### テストの書き方

```sql
, test as (
select
    -- 行レベル: NULLが存在しないか
    case
        when exists(select 1 from tbl where column1 is null)
        then cast(date(cast('column1にNULLが存在します' as text)) as text)
        else 'passed'
    end as test_no_null

    -- 集計レベル: 件数が元テーブルと一致するか
    , case
        when (select count(*) from tbl) != (select count(*) from raw)
        then cast(date(cast('件数が元テーブルと一致しません' as text)) as text)
        else 'passed'
    end as test_count_match

    -- 集計レベル: セグメント合計が全体と一致するか
    , case
        when (select sum(amount) from segment_tbl) != (select sum(amount) from tbl)
        then cast(date(cast('セグメント合計が全体合計と一致しません' as text)) as text)
        else 'passed'
    end as test_segment_sum
)

select *
from tbl t
cross join test
```

- `test` CTEは最後のCTEとして追加する
- `cross join test` を最終クエリの末尾に付ける
- テストをスキップしたい場合はコメントアウトする

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

, test as (
select
    case
        when exists(select 1 from tbl where hoge1 is null)
        then cast(date(cast('hoge1にNULLが存在します' as text)) as text)
        else 'passed'
    end as test_no_null
)

select *
from tbl t
cross join test
order by t.date
```
