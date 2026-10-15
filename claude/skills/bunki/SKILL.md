---
name: bunki
description: 現在のClaude Codeセッションをフォークして、herdrの右paneまたは新tabで起動する。「/bunki right」「/bunki tab」「作業を分岐して」「フォークして」「このセッションを分岐して」で使用
---

# bunki — セッション分岐

現在のClaude Codeセッションを `claude --resume <セッションID> --fork-session` でフォークし、herdrの右paneまたは新tabで起動する。フォークは実行時点までの会話を丸ごと引き継いだ**新しいセッションID**で起動し、元のセッションはそのまま続行できる（gitのbranchに相当）。

## 前提チェック

Bashで `HERDR_PANE_ID` と `CLAUDE_CODE_SESSION_ID` を確認する。どちらかが空なら、herdr外で動作しているかセッションIDが不明なので、その旨を報告して終了する。

## 引数パース

- 第1引数が `right` または `tab` → 分岐先の指定。**省略時は `right`**
- それ以降のテキスト → フォーク先に渡す**初期プロンプト**（任意）
- 例: `/bunki right B案を試して` → 右paneに分岐し、起動直後に「B案を試して」を実行

## 手順

### 0. 【必須】フォーク起動ディレクトリの特定

**`claude --resume` はカレントディレクトリからプロジェクト履歴を探す。**
トランスクリプトは `~/.claude/projects/<cwdをハイフン変換した名前>/<セッションID>.jsonl` に置かれるため、
**セッション開始時と違うディレクトリで起動すると `No conversation found with session ID` になる。**

`$PWD` を使ってはいけない。**トランスクリプトから元の cwd を復元する。**

```bash
TRANSCRIPT=$(find ~/.claude/projects -name "$CLAUDE_CODE_SESSION_ID.jsonl" -print -quit 2>/dev/null)
FORK_CWD=$(python3 -c "
import json,sys
for line in open(sys.argv[1], encoding='utf-8'):
    try: d = json.loads(line)
    except Exception: continue
    if d.get('cwd'): print(d['cwd']); break
" "$TRANSCRIPT")
[ -z "$FORK_CWD" ] && FORK_CWD="$PWD"
echo "$FORK_CWD"
```

- ディレクトリ名からのパス復元は**してはいけない**。`_` も `.` も `-` に潰されるため復元不能
  （例: `work/google_drive/dekaruto` → `-Users-...-work-google-drive-dekaruto`）
- トランスクリプト内の `cwd` は途中で変わる（シェルの `cd` を追う）ので、**最初に見つかったものを使う**
- `TRANSCRIPT` が空なら、そのセッションは resume できない。その旨を報告して終了する

以降、`--cwd` にも `pane run` の `cd` にも **`$FORK_CWD` を使う**。

### 1. フォークコマンドの組み立て

**必ず `cd "$FORK_CWD" && ` を前置する**（pane の cwd 指定だけでは不十分なことがあるため二重に効かせる）。

- 初期プロンプトなし:
  ```
  cd "$FORK_CWD" && claude --resume $CLAUDE_CODE_SESSION_ID --fork-session
  ```
- 初期プロンプトあり: 末尾にシングルクォートで囲んで追加する。プロンプト内の `'` は `'\''` にエスケープすること。
  ```
  cd "$FORK_CWD" && claude --resume $CLAUDE_CODE_SESSION_ID --fork-session 'B案を試して'
  ```

### 2a. right（右pane）の場合

1. 現在のpaneを右に分割する（フォーカスは新paneへ）:
   ```bash
   herdr pane split --current --direction right --cwd "$FORK_CWD" --focus
   ```
2. JSON応答の `result.pane.pane_id` から新しいpane IDを抽出する（`python3 -c "import json,sys; print(json.load(sys.stdin)['result']['pane']['pane_id'])"` 等で堅牢にパース）
3. 新paneでフォークコマンドを実行する:
   ```bash
   herdr pane run <新pane_id> "cd '$FORK_CWD' && claude --resume $CLAUDE_CODE_SESSION_ID --fork-session '初期プロンプト'"
   ```
   `pane run` に渡す文字列全体のクォートに注意（外側ダブルクォート、パスと初期プロンプトは内側シングルクォート）。

### 2b. tab（新tab）の場合

1. 同じworkspaceに新tabを作成する（フォーカスは新tabへ）:
   ```bash
   herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$FORK_CWD" --focus
   ```
2. JSON応答の `result.root_pane.pane_id` から新tabのpane IDを直接抽出する（pane listでの逆引きは不要）
3. そのpaneでフォークコマンドを実行する（2a-3と同様）

### 3. 完了報告

フォーク先では起動時にフォルダ信頼確認（"Is this a project you created or one you trust?"）が表示されることがある。フォーカスはフォーク先に移っているので、ユーザーに「信頼確認が出たらEnterで進めてください」と伝える。

分岐先（右pane / 新tab）を伝え、以下を1行で添える：

> フォークはこの時点までの会話を引き継ぎます。以後は独立して進み、元セッションへの逆マージはありません。

## 注意点

- フォークは実行時点までのトランスクリプトを引き継ぐ。フォーク後の双方の変更は同期しない
- 元セッションが動作中でも `--fork-session` は新IDを発行するため衝突しない
- 応答の囲い（`╭── Claude ──` / `╰──`）はグローバル設定どおり付ける
- **同じファイルを複数セッションが同時に書くと後勝ちで上書きされる。**
  並走させるときは触るファイルを分けるか、出力名に接尾辞を付けるようユーザーに促す

## 既知の失敗と対処

| 症状 | 原因 | 対処 |
|---|---|---|
| `No conversation found with session ID: ...` | **起動ディレクトリがセッション開始時と違う。**`claude --resume` は cwd からプロジェクト履歴を引くため | 手順0で `$FORK_CWD` を復元して使う。手動なら `cd <元のcwd> && claude --resume <id> --fork-session` |
| `pane_not_found` | ユーザーが失敗したpane/tabを閉じた | `herdr pane list` で生存を確認してから `pane run` する |

**実例（2026-08-07）**: セッション開始 cwd が `/Users/kubotafumihiro` なのに、
作業中に移動していた `.../dekaruto/20260731_INQUIRY-6917_.../diagrams` を `--cwd` に渡して失敗。
トランスクリプトは `~/.claude/projects/-Users-kubotafumihiro/` にあり、
別プロジェクト扱いになって見つからなかった。
