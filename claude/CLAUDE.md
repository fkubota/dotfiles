# グローバル設定

## 基本
- 日本語で応答する
- 応答の冒頭に `╭── Claude ────────────────────────────` 、末尾に `╰────────────────────────────────────────` を付けて、ユーザー入力と区別しやすくする

## リポジトリ
- ~/work/foodies: プロダクトリポジトリ
- ~/work/data-analysis-hub: 分析用リポジトリ

## 数式表示
- 数式を表示する際は `flatlatex` を使ってUnicodeレンダリングする
- 例: `python -c "import flatlatex; print(flatlatex.converter().convert(r'\frac{a}{b}'))"`
- コードブロック内のLaTeXではなく、レンダリング済みのUnicode文字で表示すること

## CSV閲覧
- CSVファイルを開く・表示する際は `csvlens` を使う
- 例: `csvlens data.csv`

## tmux連携
- 「横に出力して」「横に開いて」「横に出して」等の指示があった場合、対象ファイルを `tmux split-window -h -t $TMUX_PANE "vim {ファイルパス}"` で右ペインに開く
- 出力ファイルを作成した直後にユーザーが「横に出して」と言った場合も同様
