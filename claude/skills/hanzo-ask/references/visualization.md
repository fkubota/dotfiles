# ビジュアライゼーション出力の詳細仕様

ユーザーが「図解して」「フロー図を作って」「HTMLで可視化して」などと依頼した場合に参照する。

## 出力先とファイル運用

- `~/work/google_drive/hanzo-ask/visualization/` ディレクトリに出力する
- **既存ファイルがある場合は全体を確認し、十分な品質であれば `open` で表示するだけにする**。不足がある場合のみ差分編集（Edit）で対応し、Write での全体上書きはしない（git管理外のため復元不能）
- ファイル名はドメインに応じて命名する（例: `out-ratio-flow.html`, `ordering-overview.html`）

## スタイル仕様

- HTML + CSS のみで構成し、外部依存なしでブラウザで閲覧可能にする（Google Fontsは例外的にOK）
- フロー図、分岐図、テーブル構造図、ER図など適切な形式で可視化する
- **モダンクリーンスタイル**を使用する: system-ui フォント、#f8fafc背景、角丸カード、ソフトシャドウ、カラフルバッジ
- スタイルの参考: `~/work/google_drive/hanzo-ask/visualization/out-ratio-flow.html`

## ファビコン（必須）

`<head>` 内に以下のインラインSVGファビコンを追加する（虫眼鏡+構造、Claudeカラー）:

```html
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23D97757'/><circle cx='14' cy='14' r='8' fill='none' stroke='%23fff' stroke-width='2'/><line x1='20' y1='20' x2='27' y2='27' stroke='%23fff' stroke-width='2.5' stroke-linecap='round'/><rect x='10' y='10' width='3' height='3' rx='.5' fill='%23fff' opacity='.8'/><rect x='15' y='10' width='3' height='3' rx='.5' fill='%23fff' opacity='.6'/><line x1='13' y1='11.5' x2='15' y2='11.5' stroke='%23fff' stroke-width='.8'/><rect x='12' y='15' width='4' height='2.5' rx='.5' fill='%23fff' opacity='.6'/></svg>">
```

## 出力後

`open` コマンドでブラウザ表示を提案する。
