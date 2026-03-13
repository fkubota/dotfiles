# アラート調査コマンド

起動時に必ず以下を聞く：

> どのアラートを調査しますか？
>
> 1. `[地雷] 当日のサジェスト異常値抽出`
> 2. `[地雷] 販促_限定食材の過剰検知`
> 3. `[地雷] 最遅発注日計算不可（未サジェスト）`
> 4. `[地雷] サジェスト削除検知`
> 5. `[地雷] 納品不可日指定された発注を検知する`

番号または名前で受け取り、以降の調査フローを切り替える。

---

## 共通：引数

アラートによって必要な引数が異なる。選択後に下記を参照して確認すること。

**アラート 1・2**（食材単位）:
```
<company_id> <shop_id> <master_ingredient_id>
```

**アラート 3**（取引先単位）:
```
<company_id> <shop_id> <master_supplier_id>
```

**アラート 4**（取引先・発注日単位）:
```
<company_id> <shop_id> <master_supplier_id> <purchase_date>
```

**アラート 5**（発注単位）:
```
<company_id> <shop_id> <master_merchandise_id>
```

### 引数がない・不足している場合

不足しているものを1つずつ確認する：

> `company_id` を教えてください。
> `shop_id` を教えてください。
> `master_ingredient_id` を教えてください。

`purchase_date` は引数では受け取らない。デフォルトで `CURRENT_DATE` を使用する。

---

## 共通：alert_log ディレクトリ構造

調査結果・クエリ・知見は `~/alert_log/` に蓄積する。

```
~/alert_log/
├── INDEX.md                        # 調査ログの一覧・クイックリファレンス
├── reports/                        # 調査レポート（日付別）
│   └── YYYYMMDD/
│       └── <company_name>_<shop_name>_<ingredient_name>_<hogehoge>.md
├── queries/                        # よく使うSQL集
└── knowledge/                      # 繰り返し発生するパターン・知見
    └── patterns.md
```

### 初回実行時

ディレクトリが存在しない場合、自動的に作成する：

```bash
mkdir -p ~/alert_log/reports
mkdir -p ~/alert_log/queries
mkdir -p ~/alert_log/knowledge
```

`INDEX.md` が存在しない場合は以下の内容で作成する：

```markdown
# Alert Log Index

## 調査ログ
<!-- 調査のたびに追記 -->

## 知見・パターン
- [patterns.md](knowledge/patterns.md) - よくある異常パターンまとめ
```

---

## 共通：情報ソース

### 1. 蓄積済み知見（最優先）
- `~/alert_log/knowledge/patterns.md` - 過去の調査から蓄積したパターン

### 2. プロダクトソースコード・ドキュメント（必要に応じて参照）
- `~/work/foodies/` - プロダクトリポジトリ（ロジックの詳細確認）
- `~/work/foodies/hanzo-docs/` - HANZOのドキュメント（仕様確認）

### foodies リポジトリが見つからない場合

> `~/work/foodies/` が見つかりませんでした。プロダクトリポジトリはどこにありますか？

ユーザーが正しいパスを教えてくれたら、このコマンドファイル内の `~/work/foodies/` を正しいパスに**自動で書き換える**。

---

## 共通：DB接続情報（本番DB）

| 項目 | 値 |
|------|-----|
| Host | localhost |
| Port | 15432 |
| User | table_plus |
| Password | 実行時にユーザーへ確認（「いつものやつです」と添えて聞く） |
| Database | foodies |

### 接続手順（VPN不要・AWS SSM経由）

#### 1. AWS SSO ログイン

```bash
aws sso login --profile goals-hanzo
```

#### 2. SSHトンネル確認・起動

```bash
lsof -iTCP:15432 -sTCP:LISTEN
```

未接続の場合はバックグラウンドで起動する：

```bash
ssh -f -N \
    -L 15432:readerdatabase.production.internal.foodies.jp:5432 \
    ssm-prod
```

#### 3. 接続確認

```bash
PGPASSWORD=<password> psql -h localhost -p 15432 -U table_plus -d foodies -c "SELECT 1;"
```

#### トラブルシューティング

| エラー | 対処 |
|--------|------|
| SSO認証エラー | `aws sso login --profile goals-hanzo` を再実行 |
| SSHトンネル接続失敗 | AWS SSOの有効期限切れの可能性。SSO再ログイン後にリトライ |
| psql接続失敗 | トンネルが起動しているか `lsof -iTCP:15432` で確認 |

パスワードは毎回ユーザーに確認する：「DBのパスワードを教えてください（いつものやつです）」

---

---

# アラート 1：[地雷] 当日のサジェスト異常値抽出

`kind = 'irregular_required_base_quantity'`

## 調査フロー

### 1. 事前準備

1. `~/alert_log/` のディレクトリ・`INDEX.md` が存在するか確認し、なければ作成
2. `~/work/foodies/` の存在確認（なければユーザーに質問してパスを更新）
3. DB接続確認
4. `~/alert_log/knowledge/patterns.md` があれば読み込み、過去の知見を把握する

### 2. 並列クエリ実行

以下のクエリを**できる限り並列で**実行する。

---

#### Query A: 基本情報 + z_score詳細

```sql
SELECT
    co.name AS corporation_name,
    c.name AS company_name,
    s.name AS shop_name,
    mi.name AS ingredient_name,
    id.id AS irregular_detect_id,
    id.purchase_date,
    id.delivery_date,
    id.detail::JSONB ->> 'purchase_time' AS purchase_time,
    cast(id.detail::JSON ->> 'z_score' AS float) AS z_score,
    cast(id.detail::JSON ->> 'mean' AS float) / mm.base_unit_conversion_quantity AS mean,
    cast(id.detail::JSON ->> 'std_dev' AS float) / mm.base_unit_conversion_quantity AS std_dev,
    cast(id.detail::JSON ->> 'data_count' AS float) AS data_count,
    id.kind,
    id.created_at
FROM irregular_detects id
    LEFT JOIN companies c ON c.id = id.company_id
    LEFT JOIN corporations co ON co.id = c.corporation_id
    LEFT JOIN shops s ON s.id = id.shop_id
    LEFT JOIN master_ingredients mi ON mi.bitemporal_id = id.master_ingredient_id
        AND mi.valid_from <= NOW() AND mi.valid_to > NOW() AND mi.deleted_at IS NULL
    LEFT JOIN purchase_recommend_quantity_results prqr
        ON prqr.id = cast(id.detail::json ->> 'purchase_recommend_quantity_results_id' AS UUID)
    LEFT JOIN master_ingredient_shop_links sl ON sl.master_ingredient_id = id.master_ingredient_id
        AND sl.shop_id = id.shop_id AND sl.deleted_at IS NULL
        AND sl.valid_from <= id.purchase_date AND sl.valid_to > id.purchase_date
    LEFT JOIN master_merchandises mm ON mm.id = sl.default_master_merchandise_id
WHERE id.company_id = '<company_id>'
    AND id.shop_id = '<shop_id>'
    AND id.master_ingredient_id = '<master_ingredient_id>'
    AND id.purchase_date = '<purchase_date>'
    AND id.kind = 'irregular_required_base_quantity'
    AND id.deleted_at IS NULL
ORDER BY id.created_at DESC
LIMIT 1;
```

---

#### Query B: サジェスト詳細（最新スナップショット）

```sql
SELECT
    prqr.purchase_date,
    prqr.delivery_date,
    prqr.intermediate_values::json ->> 'next_delivery_date' AS next_delivery_date,
    prqr.purchase_time,
    prqr.snapshot_datetime,
    prqr.params::json ->> 'auto_purchase_pattern_type' AS purchase_pattern,
    cast(prqr.params::json ->> 'ordering_point_quantity' AS NUMERIC) / mm.base_unit_conversion_quantity AS order_point_qty,
    cast(prqr.intermediate_values::json ->> 'order_point' AS NUMERIC) / mm.base_unit_conversion_quantity AS auto_corrected_order_point,
    cast(prqr.intermediate_values::json ->> 'current_stock_quantity' AS NUMERIC) / mm.base_unit_conversion_quantity AS stock_at_confirm,
    cast(prqr.intermediate_values::json ->> 'stock_base_quantity' AS NUMERIC) / mm.base_unit_conversion_quantity AS stock_at_suggest,
    cast(prqr.intermediate_values::json ->> 'subtract_predict_base_quantity' AS NUMERIC) / mm.base_unit_conversion_quantity AS subtract_predict,
    cast(prqr.intermediate_values::json ->> 'subtract_predict_base_quantity_to_purchase_time' AS NUMERIC) / mm.base_unit_conversion_quantity AS subtract_predict_to_purchase_time,
    cast(prqr.intermediate_values::json ->> 'estimated_deliveries' AS NUMERIC) / mm.base_unit_conversion_quantity AS estimated_deliveries,
    cast(prqr.intermediate_values::json ->> 'predict_quantity_before_next_delivery_date' AS NUMERIC) / mm.base_unit_conversion_quantity AS predict_qty,
    cast(prqr.intermediate_values::json ->> 'safety_stock' AS NUMERIC) / mm.base_unit_conversion_quantity AS safety_stock,
    cast(prqr.intermediate_values::json ->> 'estimated_consume_and_stock_buffer' AS NUMERIC) / mm.base_unit_conversion_quantity AS estimated_consume_and_buffer,
    cast(prqr.intermediate_values::json ->> 'estimated_consume_lead_time_after_next_delivery' AS NUMERIC) / mm.base_unit_conversion_quantity AS lead_time_consume,
    cast(prqr.intermediate_values::json ->> 'required_base_quantity' AS NUMERIC) / mm.base_unit_conversion_quantity AS required_base_qty,
    prqr.recommend_quantity,
    mm.base_unit_conversion_quantity,
    prqr.intermediate_values::json ->> 'is_cut_at_estimated_max_consume' AS is_cut_at_max,
    prqr.intermediate_values::json ->> 'estimated_max_consume_quantity' AS estimated_max_consume,
    prqr.params::json -> 'top_out_base_quantities' -> 'holidays' -> 0 AS top_out_holidays,
    prqr.params::json -> 'top_out_base_quantities' -> 'weekdays' -> 0 AS top_out_weekdays,
    prqr.intermediate_values::json ->> 'purchase_constraint_id' AS constraint_id,
    prqr.intermediate_values::json ->> 'purchase_constraint_success' AS constraint_success,
    prqr.intermediate_values::json ->> 'purchase_quantity_before_constraint' AS qty_before_constraint,
    prqr.intermediate_values::json ->> 'purchase_quantity_after_constraint' AS qty_after_constraint,
    prqr.is_after_user_edit,
    pip.manual_ordering_point_quantity / mm.base_unit_conversion_quantity AS manual_order_point,
    prqr.intermediate_values,
    prqr.params
FROM purchase_recommend_quantity_results prqr
    INNER JOIN master_ingredient_shop_links sl ON sl.master_ingredient_id = prqr.master_ingredient_id
        AND sl.shop_id = prqr.shop_id
        AND sl.valid_from <= prqr.purchase_date AND sl.valid_to > prqr.purchase_date AND sl.deleted_at IS NULL
    LEFT JOIN master_merchandises mm ON mm.id = sl.default_master_merchandise_id
        AND mm.master_ingredient_id = sl.master_ingredient_id AND mm.base_unit_conversion_quantity > 0
    LEFT JOIN purchase_ingredient_props pip ON pip.company_id = prqr.company_id
        AND pip.shop_id = prqr.shop_id AND pip.master_ingredient_id = prqr.master_ingredient_id
        AND pip.deleted_at IS NULL
WHERE prqr.company_id = '<company_id>'
    AND prqr.shop_id = '<shop_id>'
    AND prqr.master_ingredient_id = '<master_ingredient_id>'
    AND prqr.purchase_date = '<purchase_date>'
ORDER BY prqr.snapshot_datetime DESC
LIMIT 1;
```

---

#### Query C: 食材設定（発注設定・自動調整・レベル別基準値）

```sql
SELECT
    mi.name AS ingredient_name,
    c.name AS company_name,
    s.name AS shop_name,
    CASE
        WHEN pip.purchase_rank = 0 THEN '何もしない'
        WHEN pip.purchase_rank = 10 THEN 'おすすめ量表示'
        WHEN pip.purchase_rank = 20 THEN 'オート下書き'
        WHEN pip.purchase_rank = 30 THEN 'HANZOにおまかせ'
    END AS purchase_rank,
    CASE
        WHEN pip.manual_selected_purchase_method = 'order_point_with_required_quantity' THEN '在庫数が基準を下回ったら'
        WHEN pip.manual_selected_purchase_method = 'order_point' THEN '在庫数が基準を下回ったら（補正なし）'
        WHEN pip.manual_selected_purchase_method = 'replenishment_point' THEN '常に上限まで補充'
        WHEN pip.manual_selected_purchase_method = 'replenishment_order_point_with_required_quantity' THEN '在庫数が基準を下回ったら、上限まで補充'
        WHEN pip.manual_selected_purchase_method = 'replenishment_order_point' THEN '在庫数が基準を下回ったら、上限まで補充（補正なし）'
        WHEN pip.manual_selected_purchase_method = 'required_quantity' THEN '在庫数の基準を自動で調整'
        WHEN pip.manual_selected_purchase_method = 'periodic_fixed' THEN '定期発注'
        WHEN pip.manual_selected_purchase_method IS NULL THEN '未設定'
        ELSE pip.manual_selected_purchase_method
    END AS purchase_method,
    CASE
        WHEN pip.manual_selected_purchase_method IN ('order_point', 'replenishment_order_point') THEN '補正しない'
        WHEN pip.safety_coefficient = 0 THEN '安全量なし'
        WHEN pip.safety_coefficient = 1.65 THEN '品切れ覚悟'
        WHEN pip.safety_coefficient = 2.33 THEN 'なるべく絞る'
        WHEN pip.safety_coefficient = 3.1 AND pip.safety_stock_lower_limit_rate = 0.5 THEN '半日分くらい多め'
        WHEN pip.safety_coefficient = 3.1 AND pip.safety_stock_lower_limit_rate = 1 THEN '1日分くらい多め'
        WHEN pip.safety_coefficient = 3.1 AND pip.safety_stock_lower_limit_rate = 1.5 THEN '1.5日分くらい多め'
        ELSE pip.safety_coefficient::text
    END AS safety_level,
    pip.manual_ordering_point_quantity / mm.base_unit_conversion_quantity AS order_point,
    pip.manual_fill_up_point_quantity / mm.base_unit_conversion_quantity AS fill_up_point,
    pip.manual_purchase_base_qty_abnormal_threshold / mm.base_unit_conversion_quantity AS max_recommend_qty,
    pip.minimum_lot / mm.base_unit_conversion_quantity AS min_lot,
    pip.purchase_step_quantity / mm.base_unit_conversion_quantity AS step_qty,
    pip.lead_time_after_next_delivery,
    pip.expiration_days_from_delivery,
    mm.name AS merchandise_name,
    mm.base_unit_conversion_quantity,
    ms.name AS supplier_name,
    mmsl.delivery_duration,
    mis.average_purchased_base_quantity / mm.base_unit_conversion_quantity AS avg_purchase_qty,
    kh.expected_out_quantity_rate,
    st.adjustment_level,
    CASE WHEN st.adjustment_enabled THEN 'ON' ELSE 'OFF' END AS adjustment_enabled,
    st.adjustment_level_auto_changed_at,
    (ra.adjustment_ordering_point_quantities::json ->> 'level1')::NUMERIC / mm.base_unit_conversion_quantity AS level1,
    (ra.adjustment_ordering_point_quantities::json ->> 'level2')::NUMERIC / mm.base_unit_conversion_quantity AS level2,
    (ra.adjustment_ordering_point_quantities::json ->> 'level3')::NUMERIC / mm.base_unit_conversion_quantity AS level3,
    (ra.adjustment_ordering_point_quantities::json ->> 'level4')::NUMERIC / mm.base_unit_conversion_quantity AS level4,
    (ra.adjustment_ordering_point_quantities::json ->> 'level5')::NUMERIC / mm.base_unit_conversion_quantity AS level5,
    ra.date AS adjustment_base_date
FROM purchase_ingredient_props pip
    INNER JOIN shops s ON s.id = pip.shop_id
    INNER JOIN companies c ON c.id = pip.company_id
    INNER JOIN master_ingredients mi ON mi.bitemporal_id = pip.master_ingredient_id
        AND mi.deleted_at IS NULL AND mi.valid_from <= NOW() AND mi.valid_to > NOW()
    LEFT JOIN master_ingredient_shop_links sl ON sl.master_ingredient_id = mi.bitemporal_id
        AND sl.shop_id = pip.shop_id AND sl.deleted_at IS NULL
        AND sl.valid_from <= NOW() AND sl.valid_to > NOW()
    LEFT JOIN master_merchandises mm ON mm.master_ingredient_id = sl.master_ingredient_id
        AND mm.id = sl.default_master_merchandise_id AND mm.is_purchasable = TRUE
    LEFT JOIN master_merchandise_shop_links mmsl ON mmsl.master_merchandise_id = mm.id AND mmsl.shop_id = s.id
    LEFT JOIN master_suppliers ms ON ms.id = mm.master_supplier_id
    LEFT JOIN purchase_rule_adjustment_settings st ON st.company_id = pip.company_id
        AND st.shop_id = pip.shop_id AND st.master_ingredient_id = pip.master_ingredient_id
    LEFT JOIN purchase_rule_adjustment_base_quantities ra ON ra.company_id = pip.company_id
        AND ra.shop_id = pip.shop_id AND ra.master_ingredient_id = pip.master_ingredient_id
        AND ra.date >= CURRENT_DATE - INTERVAL '2 month'
    LEFT JOIN master_ingredient_kpi_histories kh ON kh.master_ingredient_id = pip.master_ingredient_id
        AND kh.company_id = pip.company_id AND kh.shop_id = pip.shop_id
        AND kh.deleted_at IS NULL AND kh.valid_from <= NOW() AND kh.valid_to > NOW()
    LEFT JOIN master_ingredient_statuses mis ON mis.master_ingredient_id = pip.master_ingredient_id
        AND mis.company_id = pip.company_id AND mis.shop_id = pip.shop_id AND mis.date = CURRENT_DATE
WHERE pip.company_id = '<company_id>'
    AND pip.shop_id = '<shop_id>'
    AND pip.master_ingredient_id = '<master_ingredient_id>';
```

---

#### Query D: IN/OUT実績（60日分）

```sql
SELECT
    ls.date,
    to_char(ls.date, 'Dy') AS dow,
    ls.in_base_quantity / mm.base_unit_conversion_quantity AS in_qty,
    ls.out_base_quantity / mm.base_unit_conversion_quantity AS out_qty,
    ls.stock_base_quantity / mm.base_unit_conversion_quantity AS stock_qty
FROM ledger_subtotals ls
    INNER JOIN master_ingredient_shop_links sl ON sl.master_ingredient_id = ls.master_ingredient_id
        AND sl.shop_id = ls.shop_id AND sl.deleted_at IS NULL
        AND sl.valid_from <= ls.date AND sl.valid_to > ls.date
    LEFT JOIN master_merchandises mm ON mm.id = sl.default_master_merchandise_id
        AND mm.master_ingredient_id = sl.master_ingredient_id
WHERE ls.company_id = '<company_id>'
    AND ls.shop_id = '<shop_id>'
    AND ls.master_ingredient_id = '<master_ingredient_id>'
    AND ls.date >= CURRENT_DATE - 60
ORDER BY ls.date DESC;
```

---

#### Query E: 異常検知履歴

```sql
SELECT
    cast(id.detail::JSON ->> 'z_score' AS float) AS z_score,
    cast(id.detail::JSON ->> 'mean' AS float) AS mean_base,
    cast(id.detail::JSON ->> 'std_dev' AS float) AS std_dev_base,
    cast(id.detail::JSON ->> 'data_count' AS float) AS data_count,
    id.purchase_date,
    id.delivery_date,
    id.detail::JSONB ->> 'purchase_time' AS purchase_time,
    id.created_at
FROM irregular_detects id
WHERE id.company_id = '<company_id>'
    AND id.shop_id = '<shop_id>'
    AND id.master_ingredient_id = '<master_ingredient_id>'
    AND id.kind = 'irregular_required_base_quantity'
    AND id.deleted_at IS NULL
ORDER BY id.purchase_date DESC
LIMIT 20;
```

---

#### Query F: 自動調整基準値の変更履歴

```sql
SELECT
    prh.created_at AS adjusted_at,
    (prh.details::json -> 'manual_ordering_point_quantity' ->> 'before')::NUMERIC / mm.base_unit_conversion_quantity AS before_qty,
    (prh.details::json -> 'manual_ordering_point_quantity' ->> 'after')::NUMERIC / mm.base_unit_conversion_quantity AS after_qty
FROM purchase_rule_adjustment_histories prh
    INNER JOIN master_ingredient_shop_links sl ON sl.master_ingredient_id = prh.master_ingredient_id
        AND sl.shop_id = prh.shop_id AND sl.deleted_at IS NULL
        AND sl.valid_from <= NOW() AND sl.valid_to > NOW()
    LEFT JOIN master_merchandises mm ON mm.id = sl.default_master_merchandise_id
        AND mm.is_purchasable = TRUE
WHERE prh.company_id = '<company_id>'
    AND prh.shop_id = '<shop_id>'
    AND prh.master_ingredient_id = '<master_ingredient_id>'
ORDER BY prh.created_at DESC
LIMIT 20;
```

---

#### Query G: KPI履歴（OUT比率の変遷）

```sql
SELECT
    kh.valid_from::date,
    kh.valid_to::date,
    kh.expected_out_quantity_rate,
    kh.expected_out_quantity_rate_type,
    kh.r2,
    kh.updated_at
FROM master_ingredient_kpi_histories kh
WHERE kh.company_id = '<company_id>'
    AND kh.shop_id = '<shop_id>'
    AND kh.master_ingredient_id = '<master_ingredient_id>'
    AND kh.deleted_at IS NULL
ORDER BY kh.valid_to DESC
LIMIT 10;
```

---

#### Query H: 在庫訂正履歴（必要に応じて）

```sql
SELECT
    a.datetime AS stocktaking_datetime,
    CASE
        WHEN a.func_key = 'stocks_list' THEN '在庫リスト'
        WHEN a.func_key = 'correction' THEN '在庫訂正（鉛筆）'
        WHEN a.func_key = 'stocks' THEN '在庫カウントリクエスト'
        WHEN a.func_key = 'extinventory' THEN '外部棚卸し'
        WHEN a.func_key = 'train_ai' THEN 'AI学習'
        ELSE 'その他'
    END AS route,
    asi.stock_count,
    asi.stock_base_quantity / mm.base_unit_conversion_quantity AS stock_in_unit,
    asi.created_at
FROM act_stocktaking_items asi
    INNER JOIN act_stocktakings a ON a.id = asi.act_stocktaking_id
        AND a.is_ledger_calculation_target = TRUE
    INNER JOIN master_ingredient_shop_links sl ON sl.master_ingredient_id = asi.master_ingredient_id
        AND sl.shop_id = asi.shop_id AND sl.deleted_at IS NULL
        AND sl.valid_from <= NOW() AND sl.valid_to > NOW()
    LEFT JOIN master_merchandises mm ON mm.id = sl.default_master_merchandise_id
WHERE asi.company_id = '<company_id>'
    AND asi.shop_id = '<shop_id>'
    AND asi.master_ingredient_id = '<master_ingredient_id>'
ORDER BY a.datetime DESC
LIMIT 30;
```

---

#### Query I: OUT比率分析（ledger_analyze_stocks）

```sql
SELECT
    CASE
        WHEN las.actual_usage_base_quantity <= 0 THEN '無効'
        WHEN las.recipe_out_base_quantity <= 0 THEN '無効'
        ELSE '有効'
    END AS is_valid,
    las.stock_at,
    las.actual_usage_base_quantity,
    las.recipe_out_base_quantity,
    las.expected_out_quantity_rate,
    las.r2,
    CASE WHEN las.r2 >= 0.7 THEN '採用' ELSE '不採用' END AS is_adopted,
    las.updated_at
FROM ledger_analyze_stocks las
WHERE las.company_id = '<company_id>'
    AND las.shop_id = '<shop_id>'
    AND las.master_ingredient_id = '<master_ingredient_id>'
ORDER BY las.stock_at DESC;
```

---

#### Query J: master_ingredient_statuses（予測精度）

```sql
SELECT
    mis.date,
    mis.predict_diff_average,
    mis.predict_diff_deviation,
    mis.predict_diff_average + 1.65 * mis.predict_diff_deviation AS safety_stock_1_65,
    mis.predict_diff_average + 2.33 * mis.predict_diff_deviation AS safety_stock_2_33,
    mis.predict_diff_average + 3.10 * mis.predict_diff_deviation AS safety_stock_3_10,
    mis.updated_at
FROM master_ingredient_statuses mis
WHERE mis.company_id = '<company_id>'
    AND mis.shop_id = '<shop_id>'
    AND mis.master_ingredient_id = '<master_ingredient_id>'
    AND mis.date >= CURRENT_DATE - INTERVAL '2 month'
ORDER BY mis.date DESC
LIMIT 10;
```

---

### 3. 分析・レポート作成

#### 必ず確認する観点

1. **z_scoreが高い理由**
   - `required_base_quantity` vs `mean`（過去平均発注量）を比較
   - `required_base_quantity = estimated_consume_and_buffer - stock_at_confirm - estimated_deliveries` を検算
   - data_countが少ない（< 10）場合、統計的に不安定な可能性

2. **サジェストの妥当性**
   - IN/OUT実績の曜日パターンを確認（週末・祝日に消費が偏っていないか）
   - 次回納品日までの期間と予測消費量が整合しているか
   - `estimated_max_consume` vs `estimated_consume_and_buffer` でカットされていないか

3. **発注設定の状態**
   - 自動調整のON/OFF と現在レベル
   - 最大推奨数が設定されているか
   - ユーザーが編集済みか（`is_after_user_edit`）

4. **繰り返しアラートか**
   - 過去の異常検知履歴（Query E）で繰り返し検知されているか

5. **OUT比率の信頼性**
   - `r2` が 0.7 以上か（採用基準）

#### 判断フレームワーク

| パターン | 判断 |
|---------|------|
| data_count < 5 かつ z_score > 10 | 統計的に不安定。データ不足による誤検知の可能性大 |
| 週末/祝日をまたぐ発注で消費増 | 誤検知に近い。サジェスト自体は妥当 |
| is_after_user_edit = true | ユーザー確認済み |
| estimated_max_consume でカット済み | 異常な予測カット、要確認 |
| 発注制約あり（constraint_id != null） | 制約による発注数変更、要確認 |
| 自動調整 OFF かつ level5 | 基準値が最大。過剰発注になっていないか確認 |
| OUT比率 > 1.5 かつ r2 < 0.7 | OUT比率の信頼性低い |

---

### 4. アウトプット出力

`~/alert_log/reports/YYYYMMDD/<company_name>_<shop_name>_<ingredient_name>_<purchase_date>.md` に出力する。

```markdown
# <食材名> / <店舗名> - <YYYY-MM-DD>

## 結論

**（誤検知 / 真の異常 / 要確認）**

- 理由: （1〜2文で簡潔に）
- 推奨アクション: （確認済みにしてOK / 設定要確認 / 調査継続 など）

---

## 基本情報

| 項目 | 値 |
|------|-----|
| 業態 | ... |
| 店舗 | ... |
| 食材 | ... |
| 発注日 | ... |
| z_score | ... |
| サジェスト数 | ... |
| 発注パターン | ... |
| 自動調整 | ON/OFF（levelX） |
| ユーザー編集済み | true/false |

---

## 根拠

- required_base_qty: X袋 = estimated_consume_and_buffer(X) - 確定時在庫(X) - 納品予定(X)
- mean: X袋/回、z_score = (X - X) / X = X
- （週末/祝日パターン、data_count不足、制約など、判断に使った事実）
```

---

---

# アラート 2：[地雷] 販促_限定食材の過剰検知

`kind = 'irregular_promotion_only_excessive_suggest'`

対象：`use_purchase_type = 0`（販促・限定食材）のサジェストが閾値を超過した場合に発火するアラート。

## 調査フロー

### 1. 事前準備

アラート1と同様（ディレクトリ確認、foodies存在確認、DB接続確認、patterns.md読み込み）。

### 2. 並列クエリ実行

---

#### Query A: アラート基本情報

```sql
SELECT
    c.name                                                      AS company_name,
    s.name                                                      AS shop_name,
    mi.name                                                     AS ingredient_name,
    id.kind                                                     AS 異常種別,
    id.purchase_date                                            AS 発注日,
    id.delivery_date                                            AS 納品日,
    (id.detail ->> 'purchase_time')::TIMESTAMP                 AS 発注確定時刻,
    (id.detail ->> 'recommend_quantity')::NUMERIC              AS サジェスト,
    (id.detail ->> 'threshold')::NUMERIC                       AS 閾値,
    (id.detail ->> 'recommend_base_quantity')::NUMERIC         AS 発注量_base,
    (id.detail ->> 'average_purchased_base_quantity')::NUMERIC AS 平均発注量_base,
    prqr.is_after_user_edit                                    AS ユーザー編集後フラグ,
    pip.purchase_rank                                          AS 発注ランク,
    id.id,
    id.company_id,
    id.shop_id,
    id.master_ingredient_id,
    prqr.purchase_id,
    prqr.id AS prqr_id,
    id.created_at,
    id.updated_at
FROM irregular_detects id
LEFT JOIN purchase_recommend_quantity_results prqr
    ON prqr.id = (id.detail ->> 'purchase_recommend_quantity_results_id')::UUID
INNER JOIN companies c ON c.id = id.company_id
INNER JOIN shops s     ON s.id = id.shop_id
INNER JOIN master_ingredients mi
    ON mi.bitemporal_id = id.master_ingredient_id
    AND mi.valid_from <= NOW()
    AND mi.valid_to   >  NOW()
    AND mi.deleted_at IS NULL
INNER JOIN purchase_ingredient_props pip
    ON pip.company_id = id.company_id
    AND pip.shop_id = id.shop_id
    AND pip.master_ingredient_id = id.master_ingredient_id
    AND pip.deleted_at IS NULL
WHERE id.company_id = '<company_id>'
    AND id.shop_id = '<shop_id>'
    AND id.master_ingredient_id = '<master_ingredient_id>'
    AND id.purchase_date = '<purchase_date>'
    AND id.kind = 'irregular_promotion_only_excessive_suggest'
    AND id.deleted_at IS NULL
ORDER BY id.created_at DESC
LIMIT 1;
```

---

#### Query B: サジェスト詳細（最新スナップショット）

アラート1の Query B と同じクエリを使用する（`prqr.purchase_date = '<purchase_date>'`）。

---

#### Query C: 食材設定

アラート1の Query C と同じクエリを使用する。

---

#### Query D: IN/OUT実績（60日分）

アラート1の Query D と同じクエリを使用する。

---

#### Query E: 同種アラートの発火履歴

```sql
SELECT
    (id.detail ->> 'recommend_quantity')::NUMERIC              AS サジェスト,
    (id.detail ->> 'threshold')::NUMERIC                       AS 閾値,
    (id.detail ->> 'recommend_base_quantity')::NUMERIC         AS 発注量_base,
    (id.detail ->> 'average_purchased_base_quantity')::NUMERIC AS 平均発注量_base,
    id.purchase_date,
    id.delivery_date,
    id.created_at
FROM irregular_detects id
WHERE id.company_id = '<company_id>'
    AND id.shop_id = '<shop_id>'
    AND id.master_ingredient_id = '<master_ingredient_id>'
    AND id.kind = 'irregular_promotion_only_excessive_suggest'
    AND id.deleted_at IS NULL
ORDER BY id.purchase_date DESC
LIMIT 20;
```

---

### 3. 分析・レポート作成

#### 必ず確認する観点

1. **過剰検知の理由**
   - `recommend_quantity`（サジェスト）が `threshold`（閾値）をどれだけ超えているか
   - `recommend_base_quantity` vs `average_purchased_base_quantity`（平均比）の乖離率を算出
   - 乖離率が大きい場合、なぜ今回のサジェストが平均を大きく上回っているかを確認

2. **販促・限定食材としての妥当性**
   - IN/OUT実績（Query D）から、過去に同様の大量発注があるか確認
   - 発注日が特定の曜日・イベント前後でないか確認

3. **発注設定の状態**
   - `purchase_rank`（発注ランク）の確認
   - `is_after_user_edit`（ユーザー編集済みか）
   - 最大推奨数（`max_recommend_qty`）の設定有無

4. **繰り返しアラートか**
   - Query E の履歴から繰り返し発火していないか確認

#### 判断フレームワーク

| パターン | 判断 |
|---------|------|
| recommend ÷ average > 3 かつ履歴なし | 大幅乖離。サジェストの根拠を詳しく確認 |
| is_after_user_edit = true | ユーザーが意図的に編集した可能性 |
| 過去に同水準の発注実績あり | 季節性・イベント対応の可能性。誤検知に近い |
| max_recommend_qty 未設定 | 上限なし。閾値設定の見直し検討 |
| 繰り返し発火（同食材・同店舗） | 閾値またはサジェストロジックの根本的な見直しが必要 |

---

### 4. アウトプット出力

`~/alert_log/reports/YYYYMMDD/<company_name>_<shop_name>_<ingredient_name>_promotion_<purchase_date>.md` に出力する。

```markdown
# [販促過剰] <食材名> / <店舗名> - <YYYY-MM-DD>

## 結論

**（誤検知 / 真の異常 / 要確認）**

- 理由: （1〜2文で簡潔に）
- 推奨アクション: （確認済みにしてOK / 設定要確認 / 調査継続 など）

---

## 基本情報

| 項目 | 値 |
|------|-----|
| 店舗 | ... |
| 食材 | ... |
| 発注日 | ... |
| サジェスト | ... |
| 閾値 | ... |
| 平均発注量_base | ... |
| 乖離率 | サジェスト ÷ 平均 = X倍 |
| 発注ランク | ... |
| ユーザー編集済み | true/false |

---

## 根拠

- （発注量乖離の理由、過去実績との比較、繰り返し状況など）
```

---

---

---

---

# アラート 3：[地雷] 最遅発注日計算不可（未サジェスト）

`kind = 'missing_suggest'` / `cause = 'no_last_purchase_date'`

対象：最遅発注日が計算できず、サジェストが出せなかったケース。取引先単位で集約される。

## 調査フロー

### 1. 引数

`$ARGUMENTS` からスペース区切りで受け取る：

```
<company_id> <shop_id> <master_supplier_id>
```

不足している場合は1つずつ確認する。`purchase_date` はデフォルト `CURRENT_DATE`。

### 2. 並列クエリ実行

---

#### Query A: アラート基本情報（取引先単位）

```sql
SELECT
    c.name                                                       AS company_name,
    s.name                                                       AS shop_name,
    ms.name                                                      AS master_supplier_name,
    count(1)                                                     AS 該当商品数,
    id.detail::JSONB ->> 'purchase_time'                        AS purchase_time,
    id.detail::JSONB ->> 'before_next_delivery_date'            AS delivery_date,
    id.company_id,
    id.shop_id,
    ms.id                                                        AS master_supplier_id,
    min(mi.bitemporal_id::text)                                  AS one_master_ingredient_id,
    min(mm.id::text)                                             AS one_master_merchandise_id,
    CASE
        WHEN ms.center_supplier_id IS NOT NULL THEN true
        WHEN bool_or(mm.master_supplier_id_order_to IS NOT NULL) THEN true
        ELSE false
    END                                                          AS センター利用有無
FROM irregular_detects id
    INNER JOIN companies c ON c.id = id.company_id
    INNER JOIN shops s ON s.id = id.shop_id
    LEFT OUTER JOIN master_ingredients mi
        ON id.master_ingredient_id = mi.bitemporal_id
        AND mi.valid_from <= CURRENT_TIMESTAMP
        AND mi.valid_to > CURRENT_TIMESTAMP
        AND mi.deleted_at IS NULL
    LEFT OUTER JOIN master_merchandises mm ON mm.id = (id.detail::JSONB ->> 'master_merchandise_id')::UUID
    LEFT OUTER JOIN master_suppliers ms ON ms.id = mm.master_supplier_id
WHERE id.kind = 'missing_suggest'
    AND id.company_id = '<company_id>'
    AND id.shop_id = '<shop_id>'
    AND ms.id = '<master_supplier_id>'
    AND id.purchase_date >= CURRENT_DATE
    AND id.deleted_at IS NULL
    AND id.detail::Json ->> 'cause' = 'no_last_purchase_date'
GROUP BY
    c.name, s.name, ms.name,
    id.detail::JSONB ->> 'purchase_time',
    id.detail::JSONB ->> 'before_next_delivery_date',
    id.company_id, id.shop_id, ms.id;
```

---

#### Query B: 店舗の店休日設定

```sql
SELECT holiday FROM shops WHERE id = '<shop_id>';
```

---

#### Query C: 取引先スケジュール（発注日以降）

```sql
SELECT *
FROM ext_supplier_schedules
WHERE company_id = '<company_id>'
    AND shop_id = '<shop_id>'
    AND master_supplier_id = '<master_supplier_id>'
    AND date >= CURRENT_DATE
ORDER BY date ASC;
```

---

#### Query D: irregular_detects の発火履歴（同取引先）

```sql
SELECT
    id.purchase_date,
    id.delivery_date,
    id.detail::JSONB ->> 'purchase_time'             AS purchase_time,
    id.detail::JSONB ->> 'before_next_delivery_date' AS before_next_delivery_date,
    id.detail::JSONB ->> 'cause'                     AS cause,
    count(1)                                         AS 該当商品数,
    id.created_at
FROM irregular_detects id
    LEFT OUTER JOIN master_merchandises mm ON mm.id = (id.detail::JSONB ->> 'master_merchandise_id')::UUID
    LEFT OUTER JOIN master_suppliers ms ON ms.id = mm.master_supplier_id
WHERE id.company_id = '<company_id>'
    AND id.shop_id = '<shop_id>'
    AND ms.id = '<master_supplier_id>'
    AND id.kind = 'missing_suggest'
    AND id.deleted_at IS NULL
GROUP BY
    id.purchase_date, id.delivery_date,
    id.detail::JSONB ->> 'purchase_time',
    id.detail::JSONB ->> 'before_next_delivery_date',
    id.detail::JSONB ->> 'cause',
    id.created_at
ORDER BY id.created_at DESC
LIMIT 20;
```

---

### 3. 分析・レポート作成

#### 必ず確認する観点

1. **未サジェストの原因**
   - `cause = 'no_last_purchase_date'`：過去の発注実績がなく最遅発注日が計算できない状態
   - センター経由取引か直接取引かを確認（`センター利用有無`）

2. **取引先スケジュールの状態**
   - Query C の結果から、今後の納品スケジュールが登録されているか
   - スケジュールが空の場合、`ext_supplier_schedules` 未登録が原因の可能性

3. **店休日設定の確認**
   - Query B で店休日が適切に設定されているか

4. **繰り返しアラートか**
   - Query D から同取引先で繰り返し発火していないか

#### 判断フレームワーク

| パターン | 判断 |
|---------|------|
| ext_supplier_schedules が空 | スケジュール未登録が原因。CS対応要 |
| スケジュールはあるが発注実績なし | 新規取引先または長期未発注。初回発注の可能性 |
| 繰り返し発火 | 構造的な問題。スケジュール設定の見直し必要 |
| センター利用あり | センター側のスケジュール確認が必要 |

---

### 4. アウトプット出力

`~/alert_log/reports/YYYYMMDD/<company_name>_<shop_name>_<supplier_name>_missing_suggest_<purchase_date>.md`

```markdown
# [未サジェスト] <取引先名> / <店舗名> - <YYYY-MM-DD>

## 結論

**（スケジュール未登録 / 初回発注 / 要確認）**

- 理由:
- 推奨アクション:

---

## 基本情報

| 項目 | 値 |
|------|-----|
| 店舗 | ... |
| 取引先 | ... |
| 該当商品数 | ... |
| 発注確定時刻 | ... |
| 納品予定日 | ... |
| センター利用 | true/false |

---

## 根拠

- （スケジュール状況、店休日設定、繰り返し状況など）
```

---

---

# アラート 4：[地雷] サジェスト削除検知

テーブル：`purchase_merchandise_deletes`

発火する kind（削除理由）:
- `no_default_merchandise`: メイン仕入れ商品外れ
- `is_not_purchasable`: 発注不可
- `is_not_recommended_purchase_date`: 発注推奨日ではない

## 調査フロー

### 1. 引数

`$ARGUMENTS` からスペース区切りで受け取る：

```
<company_id> <shop_id> <master_supplier_id> [<purchase_date>]
```

`purchase_date` は省略可、デフォルト `CURRENT_DATE`。不足している場合は1つずつ確認する。

### 2. 並列クエリ実行

---

#### Query A: 削除検知一覧（取引先・発注日単位）

```sql
SELECT
    c.name                                    AS company_name,
    s.name                                    AS shop_name,
    pmd.purchase_date,
    pmd.kind,
    ms.name                                   AS supplier_name,
    count(*)                                  AS 該当商品数,
    STRING_AGG(mi.name, ',')                  AS ingredient_names,
    STRING_AGG(mm.name, ',')                  AS merchandise_names,
    c.id                                      AS company_id,
    s.id                                      AS shop_id,
    ms.id                                     AS supplier_id,
    mm.master_supplier_id_order_to            AS order_to,
    min(mi.bitemporal_id::text)               AS one_ingredient,
    min(mm.id::text)                          AS one_merchandise
FROM purchase_merchandise_deletes pmd
    INNER JOIN companies c ON c.id = pmd.company_id
    INNER JOIN shops s ON s.id = pmd.shop_id
    INNER JOIN master_ingredients mi
        ON mi.bitemporal_id = pmd.master_ingredient_id
        AND mi.valid_from <= CURRENT_TIMESTAMP
        AND mi.valid_to > CURRENT_TIMESTAMP
        AND mi.deleted_at IS NULL
    INNER JOIN master_merchandises mm ON mm.id = pmd.master_merchandise_id
    INNER JOIN master_suppliers ms ON ms.id = mm.master_supplier_id
    INNER JOIN purchase_shop_props shop_props
        ON shop_props.company_id = pmd.company_id
        AND shop_props.shop_id = pmd.shop_id
        AND shop_props.operation_start_date < CURRENT_DATE
WHERE pmd.company_id = '<company_id>'
    AND pmd.shop_id = '<shop_id>'
    AND ms.id = '<master_supplier_id>'
    AND pmd.purchase_date = '<purchase_date>'
GROUP BY
    c.name, s.name, pmd.purchase_date, pmd.kind,
    ms.name, c.id, s.id, ms.id, mm.master_supplier_id_order_to;
```

---

#### Query B: 対象食材の purchase_recommend_quantity_results（直近）

`one_ingredient` として得られた `master_ingredient_id` を使用する：

```sql
SELECT *
FROM purchase_recommend_quantity_results
WHERE purchase_date = '<purchase_date>'
    AND master_ingredient_id = '<one_ingredient>'
    AND shop_id = '<shop_id>'
    AND company_id = '<company_id>'
ORDER BY created_at DESC
LIMIT 5;
```

---

#### Query C: 取引先スケジュール（発注日以降）

```sql
SELECT *
FROM ext_supplier_schedules
WHERE company_id = '<company_id>'
    AND shop_id = '<shop_id>'
    AND master_supplier_id = '<master_supplier_id>'
    AND date >= '<purchase_date>'
ORDER BY date ASC;
```

---

#### Query D: 同取引先の削除履歴（過去30日）

```sql
SELECT
    pmd.purchase_date,
    pmd.kind,
    count(*) AS 該当商品数
FROM purchase_merchandise_deletes pmd
    INNER JOIN master_merchandises mm ON mm.id = pmd.master_merchandise_id
    INNER JOIN master_suppliers ms ON ms.id = mm.master_supplier_id
WHERE pmd.company_id = '<company_id>'
    AND pmd.shop_id = '<shop_id>'
    AND ms.id = '<master_supplier_id>'
    AND pmd.purchase_date >= CURRENT_DATE - 30
GROUP BY pmd.purchase_date, pmd.kind
ORDER BY pmd.purchase_date DESC;
```

---

### 3. 分析・レポート作成

#### kind 別の確認ポイント

| kind | 確認すること |
|------|------------|
| `no_default_merchandise` | その食材のデフォルト仕入れ商品が外れている。`master_ingredient_shop_links` の `default_master_merchandise_id` を確認 |
| `is_not_purchasable` | 商品が発注不可フラグになっている。`master_merchandises.is_purchasable` を確認 |
| `is_not_recommended_purchase_date` | 発注推奨日でない。取引先スケジュール（Query C）を確認 |

#### 必ず確認する観点

1. **削除理由（kind）の根拠確認**
   - Query B で prqr が存在するか（サジェスト計算自体は行われたか）
2. **繰り返し発火か**
   - Query D で同取引先・同 kind が繰り返し発生していないか
3. **センター・発注先変更の有無**
   - `order_to` が設定されている場合、発注先が変わっていないか

#### 判断フレームワーク

| パターン | 判断 |
|---------|------|
| `is_not_recommended_purchase_date` かつスケジュール登録あり | 正常動作。発注推奨日でないため削除は想定内 |
| `no_default_merchandise` が繰り返し | 商品マスタの紐付け設定を要確認 |
| `is_not_purchasable` が繰り返し | 発注不可フラグの意図確認が必要 |
| 複数 kind が同時発火 | 複合的な設定問題の可能性 |

---

### 4. アウトプット出力

`~/alert_log/reports/YYYYMMDD/<company_name>_<shop_name>_<supplier_name>_delete_<purchase_date>.md`

```markdown
# [削除検知] <取引先名> / <店舗名> - <YYYY-MM-DD>

## 結論

**（正常動作 / 設定問題 / 要確認）**

- 理由:
- 推奨アクション:

---

## 基本情報

| 項目 | 値 |
|------|-----|
| 店舗 | ... |
| 取引先 | ... |
| 発注日 | ... |
| kind | ... |
| 該当商品数 | ... |
| 発注先（order_to） | ... |

---

## 根拠

- （kind の理由、スケジュール状況、繰り返し状況など）
```

---

---

# アラート 5：[地雷] 納品不可日指定された発注を検知する

テーブル：`tmp_irregular_purchase_detects`

## 調査フロー

### 1. 引数

`$ARGUMENTS` からスペース区切りで受け取る：

```
<company_id> <shop_id> <master_merchandise_id>
```

不足している場合は1つずつ確認する。

### 2. 並列クエリ実行

---

#### Query A: アラート基本情報

```sql
SELECT
    c.name                                              AS company_name,
    s.name                                              AS shop_name,
    m.name                                              AS merchandise_name,
    tmp.kind,
    tmp.purchase_date,
    tmp.delivery_date,
    tmp.detail::JSONB ->> 'purchase_time'               AS purchase_time,
    tmp.company_id,
    tmp.shop_id,
    pm.master_ingredient_id,
    tmp.master_merchandise_id,
    pm.id                                               AS purchase_merchandise_id,
    pm.quantity                                         AS 発注数量,
    tmp.id                                              AS tmp_irregular_purchase_detect_id
FROM tmp_irregular_purchase_detects tmp
    INNER JOIN companies c ON c.id = tmp.company_id
    INNER JOIN shops s ON s.id = tmp.shop_id
    INNER JOIN master_merchandises m ON m.id = tmp.master_merchandise_id
    INNER JOIN purchases p ON p.id = tmp.purchase_id
    INNER JOIN purchase_merchandises pm
        ON pm.id = tmp.purchase_merchandise_id
        AND pm.master_merchandise_id = tmp.master_merchandise_id
WHERE tmp.company_id = '<company_id>'
    AND tmp.shop_id = '<shop_id>'
    AND tmp.master_merchandise_id = '<master_merchandise_id>'
    AND (tmp.detail ->> 'purchase_time')::TIMESTAMP > CURRENT_TIMESTAMP
    AND tmp.kind <> 'cannot_purchasable'
ORDER BY tmp.created_at DESC
LIMIT 10;
```

---

#### Query B: 取引先スケジュール（納品日前後）

まず商品から取引先IDを取得する：

```sql
SELECT ms.id AS master_supplier_id, ms.name AS supplier_name
FROM master_merchandises mm
    INNER JOIN master_suppliers ms ON ms.id = mm.master_supplier_id
WHERE mm.id = '<master_merchandise_id>';
```

取得した `master_supplier_id` でスケジュールを確認：

```sql
SELECT *
FROM ext_supplier_schedules
WHERE company_id = '<company_id>'
    AND shop_id = '<shop_id>'
    AND master_supplier_id = '<master_supplier_id>'
    AND date >= CURRENT_DATE - 7
ORDER BY date ASC;
```

---

#### Query C: 発注詳細（purchase_merchandises）

```sql
SELECT
    pm.id,
    pm.quantity,
    pm.master_ingredient_id,
    pm.master_merchandise_id,
    p.purchase_date,
    p.delivery_date,
    p.status
FROM purchase_merchandises pm
    INNER JOIN purchases p ON p.id = pm.purchase_id
WHERE pm.master_merchandise_id = '<master_merchandise_id>'
    AND p.shop_id = '<shop_id>'
    AND p.company_id = '<company_id>'
    AND p.purchase_date >= CURRENT_DATE - 7
ORDER BY p.purchase_date DESC
LIMIT 10;
```

---

#### Query D: 同商品の発火履歴

```sql
SELECT
    tmp.kind,
    tmp.purchase_date,
    tmp.delivery_date,
    tmp.detail::JSONB ->> 'purchase_time' AS purchase_time,
    tmp.created_at
FROM tmp_irregular_purchase_detects tmp
WHERE tmp.company_id = '<company_id>'
    AND tmp.shop_id = '<shop_id>'
    AND tmp.master_merchandise_id = '<master_merchandise_id>'
    AND tmp.kind <> 'cannot_purchasable'
ORDER BY tmp.created_at DESC
LIMIT 20;
```

---

### 3. 分析・レポート作成

#### kind 別の確認ポイント

| kind | 意味 | 確認すること |
|------|------|------------|
| `delivery_date_is_holiday` | 納品日が店休日 | 店休日設定と発注の納品日を照合 |
| `delivery_date_is_closed` | 納品日に取引先が休み | 取引先スケジュール（Query B）を確認 |
| その他 | ソースコード参照 | `~/work/foodies/` で kind の定義を確認 |

#### 必ず確認する観点

1. **kind の根拠**
   - Query B のスケジュール結果と `delivery_date` を照合
2. **発注が実際に問題かどうか**
   - Query C で発注の `status` を確認（既にキャンセル・修正済みでないか）
3. **繰り返しアラートか**
   - Query D から繰り返し発火していないか

#### 判断フレームワーク

| パターン | 判断 |
|---------|------|
| スケジュールに休日登録あり・発注は既修正 | 対処済み。確認済みにしてOK |
| スケジュールに休日登録なし | スケジュール未登録が根本原因。CS対応要 |
| 発注 status = active かつ未修正 | 即時対応が必要 |
| 繰り返し発火 | スケジュール設定の構造的な見直し必要 |

---

### 4. アウトプット出力

`~/alert_log/reports/YYYYMMDD/<company_name>_<shop_name>_<merchandise_name>_delivery_ng_<purchase_date>.md`

```markdown
# [納品不可] <商品名> / <店舗名> - <YYYY-MM-DD>

## 結論

**（対処済み / スケジュール問題 / 即時対応要）**

- 理由:
- 推奨アクション:

---

## 基本情報

| 項目 | 値 |
|------|-----|
| 店舗 | ... |
| 商品 | ... |
| kind | ... |
| 発注日 | ... |
| 納品日 | ... |
| 発注数量 | ... |
| 発注 status | ... |

---

## 根拠

- （スケジュール照合結果、発注状況、繰り返し状況など）
```

---

---

## 共通：アウトプット後処理

### INDEX.md の更新

`~/alert_log/INDEX.md` の調査ログセクションに1行追記する：

```
- [YYYY-MM-DD] <アラート種別> <食材/取引先/商品名> / <店舗名> - <総合判断> → [レポート](reports/YYYYMMDD/<file>.md)
```

### knowledge/patterns.md の更新

新たなパターンや知見が得られた場合に追記する。

---

## パーミッション

- 読み取り専用: DBへの書き込みは行わない
- 自動書き込み可能な場所: `~/alert_log/` 配下のみ
- このコマンドファイル自体は、foodiesリポジトリのパスが変わった場合のみ書き換える
