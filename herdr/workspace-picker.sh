#!/bin/bash
# herdr ワークスペースピッカー（prefix+w から popup で起動）
# 左: ワークスペース一覧 / 右: アクティブタブのペイン画面プレビュー
# j/k or ↑↓ 移動 · enter 切替 · esc/q 閉じる
set -euo pipefail

HERDR=/opt/homebrew/bin/herdr
FZF=/opt/homebrew/bin/fzf

# ワークスペース一覧とペイン一覧を突き合わせ、行を
#   workspace_id \t preview_pane_id \t focused \t 表示テキスト
# の形で生成する。preview対象はアクティブタブ内のペイン
# （エージェントがいるペインを優先、なければ先頭）。
list_workspaces() {
  "$HERDR" workspace list | jq -r --slurpfile panes <("$HERDR" pane list) '
    ($panes[0].result.panes) as $ps
    | .result.workspaces[]
    | .active_tab_id as $tab
    | ([$ps[] | select(.tab_id == $tab)]) as $tab_panes
    | (($tab_panes | map(select(.agent != null)) | first) // ($tab_panes | first)) as $p
    | (.agent_status // "-") as $st
    | ({"working":"⠐","idle":"✳","blocked":"⛔"}[$st] // "·") as $icon
    | [
        .workspace_id,
        ($p.pane_id // ""),
        (.focused // false),
        "\(.number)  \(.label)  \($icon) \($st)  \($p.terminal_title_stripped // "")"
      ]
    | @tsv
  '
}

# fzf の preview はデフォルトで $SHELL -c で実行される。fish だと構文が
# 異なるので sh に固定する。
export SHELL=/bin/sh

rows=$(list_workspaces)

# 現在フォーカス中のワークスペースの行番号（1始まり）。開いた時にカーソルを合わせる。
current_pos=$(awk -F'\t' '$3 == "true" { print NR; exit }' <<<"$rows")

selected=$(printf '%s\n' "$rows" | "$FZF" \
  --sync \
  --ansi \
  --delimiter '\t' \
  --with-nth 4.. \
  --no-multi \
  --layout reverse \
  --info hidden \
  --bind 'j:down,k:up,q:abort' \
  --bind "start:pos(${current_pos:-1})" \
  --preview '[ -n {2} ] && '"$HERDR"' pane read {2} --lines $FZF_PREVIEW_LINES --raw || echo "(no pane)"' \
  --preview-window 'right,65%,border-left' \
  --prompt 'workspace > ' \
  --header 'j/k 移動 · enter 切替 · esc/q 閉じる' \
) || exit 0

ws_id=$(cut -f1 <<<"$selected")
[ -n "$ws_id" ] && exec "$HERDR" workspace focus "$ws_id"
