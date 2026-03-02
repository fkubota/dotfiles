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

## 注意事項

- **読み取り専用**: Staging環境は読み取り専用権限のみ
- **本番環境ではない**: テストデータが含まれている可能性あり
- **ポート競合**: ローカルでPostgreSQLが起動している場合は停止するか、別ポートを使用すること
