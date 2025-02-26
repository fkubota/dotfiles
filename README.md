# dotfiles

## ユートピアの作り方
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/fkubota/dotfiles/master/install.sh)"
```


## info
- https2ssh: `git remote set-url origin git@github.com:fkubota/dotfiles.git`
- 参考サイト
	- ditfilesについて: https://qiita.com/mira010/items/927f996b278a8157f751
	- ワンライナー: https://kisqragi.hatenablog.com/entry/2020/02/17/224129

- vim-plugin は dein.vim で管理
  - dein.toml, dein_lazy.toml については
    > https://qiita.com/sugamondo/items/fcaf210ca86d65bcaca8


# fzf.fish のインストール
ref: https://github.com/PatrickF1/fzf.fish
- Mac
	1. brew install fisher
  2. brew install fd
  3. brew install bat
  4. fisher install PatrickF1/fzf.fish


# tmux
- powerline用のフォントが必要になるのでインストール。
  - git clone https://github.com/powerline/fonts.git --depth=1
  - cd fonts
  - ./install.sh
  - cd ..
  - rm -rf fonts
- その後、利用するターミナルでそのフォントを指定する。
