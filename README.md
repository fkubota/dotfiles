# dotfiles

ユートピアの作り方
- ```bash -c "$(curl -fsSL https://raw.githubusercontent.com/fkubota/dotfiles/master/install.sh)"```

- 参考サイト
	- ditfilesについて: https://qiita.com/mira010/items/927f996b278a8157f751
	- ワンライナー: https://kisqragi.hatenablog.com/entry/2020/02/17/224129

- vim-plugin は dein.vim で管理
  - dein.toml, dein_lazy.toml については
    > https://qiita.com/sugamondo/items/fcaf210ca86d65bcaca8
    > http://applepine1125.hatenablog.jp/entry/2017/03/24/003559
  - `~/dotfiles/.vim/configs/plugins/install` 内の、`dein.toml` と `dein_lazy.toml`内にプラグインを記述
