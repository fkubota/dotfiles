---
name: name2master_ingredient_id
description: CSVの食材名列にmaster_ingredient_idを付与する。デフォルトはstaging DBを検索し、完全一致→曖昧検索の順で照合する。
---

# name2master_ingredient_id スキル

食材名が入ったCSVを受け取り、staging（デフォルト）またはproduction DBを検索して `master_ingredient_id` 列を追加する。
同僚が使えるよう、このスキル内で接続から完結する。

---

## STEP 0: DB接続準備

### 0-0. 環境の選択

AskUserQuestion で確認する:
> 「どの環境のDBを使いますか？」

選択肢:
- **staging**（推奨・デフォルト）: 検証用環境
- **production**: 本番環境（実際のユーザーデータが含まれるため慎重に）

選択結果に応じて以下の接続先を使い分ける:

| 環境 | DBホスト | bastionホスト |
|------|----------|--------------|
| staging | `database.staging.internal.foodies.jp` | `staging.bastion.hanzo.cloud` |
| production | `readerdatabase.production.internal.foodies.jp` | `production.bastion.hanzo.cloud` |

### 0-1. AWS SSO 確認

```bash
aws sts get-caller-identity --profile goals-hanzo
```

失敗した場合は以下を伝えて止まる:
> 「AWS SSOセッションが切れています。次のコマンドを実行してから再度試してください：
> `aws sso login --profile goals-hanzo`」

### 0-2. SSHトンネル確認・起動

```bash
lsof -iTCP:5432 -sTCP:LISTEN
```

出力がない場合（トンネルが立ち上がっていない場合）は、選択した環境に応じて以下を実行:

#### staging（デフォルト）
```bash
ssh -f -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -L 5432:database.staging.internal.foodies.jp:5432 \
    -i ~/.ssh/minedup.pem \
    -p 22 ec2-user@staging.bastion.hanzo.cloud
sleep 2
```

#### production
```bash
ssh -f -N \
    -L 5432:readerdatabase.production.internal.foodies.jp:5432 \
    -i ~/.ssh/minedup.pem \
    -p 22 ec2-user@production.bastion.hanzo.cloud
sleep 2
```

接続後、疎通確認:
```bash
PGPASSWORD=<パスワード> psql -h localhost -p 5432 -U table_plus -d foodies -c "SELECT 1"
```

失敗した場合:
> 「SSHトンネルの接続に失敗しました。AWS SSOセッションが有効か確認してください（`aws sso login --profile goals-hanzo`）。」

### 0-3. DBパスワード

`PGPASSWORD=g0alsg0als` を使う。ユーザーへの確認は不要。

---

## STEP 1: CSVファイルの確認

ユーザーに確認する:
> 「CSVファイルのパスを教えてください」

パスを受け取ったら、ファイルを読み込んで列構成と先頭数行を確認する:

```bash
python3 -c "
import csv, sys
path = '<ユーザーが指定したパス>'
with open(path, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.reader(f))
print('列数:', len(rows[0]) if rows else 0)
print('ヘッダー:', rows[0] if rows else [])
for i, row in enumerate(rows[1:6], 1):
    print(f'行{i}:', row)
"
```

---

## STEP 2: 食材名列の確認

読み込んだ内容をもとに AskUserQuestion で確認する。
たとえば3列目のデータを見せて聞く:

> 「X列目（例: `食材名, カシミールカレー, バターライスの具, ...`）を食材名として検索します。よろしいですか？」

`multiSelect: false` で列番号を選ばせる（列が1つなら確認だけでよい）。

---

## STEP 3: 出力列の確認

AskUserQuestion で確認する:
> 「`master_ingredient_id` は一番右の列の右に追加します。よろしいですか？」

---

## STEP 4: company_id の確認

ユーザーに直接聞く:
> 「company_id を教えてください」

---

## STEP 5: 検索実行

以下の Python スクリプトを `/tmp/search_ingredients.py` として書き出して実行する。

```python
#!/usr/bin/env python3
import csv, json, os, re, subprocess, sys, unicodedata

CSV_PATH = sys.argv[1]
COL_INDEX = int(sys.argv[2])   # 0始まり
COMPANY_ID = sys.argv[3]
DB_PASSWORD = sys.argv[4]

_FW = ''.join(chr(0xFF01+i) for i in range(94)) + '　'
_HW = ''.join(chr(0x21+i) for i in range(94)) + ' '
_FW_SQL = _FW.replace("'", "''")
_HW_SQL = _HW.replace("'", "''")

def norm(s):
    return unicodedata.normalize('NFKC', s).strip()

def kata2hira(s):
    return ''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ン' else c for c in s)

def hira2kata(s):
    return ''.join(chr(ord(c)+0x60) if 'ぁ'<=c<='ん' else c for c in s)

def norm_col(col='name'):
    return f"translate({col}, '{_FW_SQL}', '{_HW_SQL}')"

def psql(sql):
    r = subprocess.run(
        ['psql','-h','localhost','-p','5432','-U','table_plus','-d','foodies','-t','-A','-F','\t','-c',sql],
        env={**os.environ,'PGPASSWORD': DB_PASSWORD},
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:200])
    rows = r.stdout.strip()
    return [row.split('\t') for row in rows.splitlines() if row.strip()] if rows else []

BASE = f"WHERE company_id='{COMPANY_ID}' AND deleted_at IS NULL AND valid_to > NOW()"
BASE_ALL = f"WHERE company_id='{COMPANY_ID}'"

def exact_active(kw):
    nc = norm_col()
    safe = norm(kw).replace("'","''")
    return psql(f"SELECT bitemporal_id, name FROM master_ingredients {BASE} AND lower({nc})=lower('{safe}') LIMIT 1")

def exact_any(kw):
    # 有効期限・削除問わず完全一致
    nc = norm_col()
    safe = norm(kw).replace("'","''")
    return psql(f"SELECT bitemporal_id, name, deleted_at, valid_to FROM master_ingredients {BASE_ALL} AND lower({nc})=lower('{safe}') ORDER BY valid_to DESC LIMIT 5")

def active_by_bitemporal(bid):
    # 同じbitemporal_idで現在有効な食材
    return psql(f"SELECT bitemporal_id, name FROM master_ingredients WHERE bitemporal_id='{bid}' AND deleted_at IS NULL AND valid_to > NOW() LIMIT 1")

def fuzzy(kw):
    nc = norm_col()
    def multi_ilike(kvs):
        kvs = list(dict.fromkeys(kvs))  # 重複除去
        conds = " OR ".join(
            f"{nc} ILIKE '%{re.sub(chr(39), chr(39)*2, re.sub(r'\\s+', '%', v))}%'"
            for v in kvs
        )
        return psql(f"SELECT bitemporal_id, name FROM master_ingredients {BASE} AND ({conds}) LIMIT 10")
    n = norm(kw)
    rows = multi_ilike([n, kata2hira(n), hira2kata(n)])
    if rows: return rows
    # トークン分割フォールバック
    tokens = [t for t in re.split(r'[\s\d()[\]×・用のに入出　]+', n) if len(t)>=3]
    for t in tokens:
        rows = multi_ilike([t, kata2hira(t), hira2kata(t)])
        if rows: return rows
    return []

with open(CSV_PATH, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.reader(f))

header = rows[0]
data = rows[1:]
results = []

for row in data:
    kw = row[COL_INDEX].strip() if len(row)>COL_INDEX else ''
    if not kw:
        results.append({'keyword':kw,'status':'skip','row':row})
        continue
    # 完全一致（有効）
    active = exact_active(kw)
    if active:
        results.append({'keyword':kw,'status':'exact','bid':active[0][0],'name':active[0][1],'row':row})
        continue
    # 完全一致（無効）
    any_match = exact_any(kw)
    if any_match:
        bid = any_match[0][0]
        current = active_by_bitemporal(bid)
        results.append({'keyword':kw,'status':'exact_inactive','bid':bid,'old_name':any_match[0][1],
                        'current':current[0] if current else None,'row':row})
        continue
    # 曖昧
    fz = fuzzy(kw)
    if fz:
        results.append({'keyword':kw,'status':'fuzzy','candidates':[{'bid':r[0],'name':r[1]} for r in fz],'row':row})
    else:
        results.append({'keyword':kw,'status':'none','row':row})

print(json.dumps(results, ensure_ascii=False))
```

実行:
```bash
python3 /tmp/search_ingredients.py "<CSVパス>" <列インデックス> "<company_id>" "g0alsg0als"
```

---

## STEP 6: 結果の処理（インタラクティブ）

JSON 結果をパースし、以下の順で処理する。

### 完全一致（有効）: `status == "exact"`
自動で `bitemporal_id` を確定。ユーザーへの確認不要。

### 完全一致（無効）: `status == "exact_inactive"`
以下を伝える:
> 「`<keyword>` は DB に完全一致しましたが、**削除済みまたは期限切れ**です。
> 同じ master_ingredient_id で現在有効な食材名は **`<current_name>`** です。
> こちらで登録してよいですか？」

AskUserQuestion で確認:
- 「はい（`<current_name>` の ID で登録）」
- 「空欄にする」

### 曖昧一致: `status == "fuzzy"`
**1件ずつ** AskUserQuestion で確認:
> 「`<keyword>` の曖昧検索結果です。どれが正しいですか？」

候補を選択肢に並べ（最大4件）、「該当なし（空欄）」も必ず含める。

### 未ヒット: `status == "none"`
空欄として記録。最後にまとめて報告する。

---

## STEP 7: CSV書き出し

全件確定後、確認を取ってから書き出す:
- **元ファイルを上書き**（header に `master_ingredient_id` 列を追加、各行に値を追記）

```bash
python3 -c "
import csv, json

results = json.loads('<JSON文字列>')
csv_path = '<CSVパス>'

with open(csv_path, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.reader(f))

header = rows[0] + ['master_ingredient_id']
out = [header]
for res in results:
    row = res['row']
    bid = res.get('bid') or ''
    out.append(row + [bid])

with open(csv_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(out)
print('書き出し完了:', csv_path)
"
```

---

## まとめ報告

処理完了後に報告する:
- 完全一致（有効）: X 件
- 完全一致（無効→更新名で登録）: X 件
- 曖昧一致: X 件
- 未ヒット（空欄）: X 件
- スキップ（空欄行）: X 件
