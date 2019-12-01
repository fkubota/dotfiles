# dotfiles

- 参考サイト
> https://qiita.com/mira010/items/927f996b278a8157f751

- vim-plugin は dein.vim で管理
  - dein.toml, dein_lazy.toml については
    > https://qiita.com/sugamondo/items/fcaf210ca86d65bcaca8
    > http://applepine1125.hatenablog.jp/entry/2017/03/24/003559
  - `~/dotfiles/.vim/configs/plugins/install` 内の、`dein.toml` と `dein_lazy.toml`内にプラグインを記述


1. `pip3 install --user jedi`  <--- jedi-vim のinstall
2. `sh ~/Git/dotfiles/01_setup_vim.sh`  <--- set up vim
3. `sh ~/Git/dotfiles/02_link_dotfiles.sh` <--- シンボリックリンクを作成


