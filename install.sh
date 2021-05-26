#!/bin/bash

# ::setup::
# dein のインストール
curl https//raw.githubusercontent.com/Shougo/dein.vim/master/bin/installer.sh > ~/installer.sh
sh ~/installer.sh ~/.cache

# flake8のインストール
pip3 install flake8 --user

# tmux
# mkdir -p fkubota/.tmux/theme/
git clone https://github.com/arcticicestudio/nord-tmux.git ~/.tmux/themes/nord-tmux

# ::シンボリックリンク::
DOT_DIR="$HOME/Git/dotfiles"

# clone
# git clone git@github.com:fkubota/dotfiles.git ${DOT_DIR}
git clone https://github.com/fkubota/dotfiles.git ${DOT_DIR}
cat ${DOT_DIR}/figlet_text.txt

# vim
mkdir -p ~/.vim/rc/
ln -sf ${DOT_DIR}/vim/.vimrc ~/.vimrc
ln -sf ${DOT_DIR}/vim/rc/dein.toml ~/.vim/rc/dein.toml
ln -sf ${DOT_DIR}/vim/rc/dein_lazy.toml ~/.vim/rc/dein_lazy.toml

# tmux
ln -sf ${DOT_DIR}/tmux/.tmux.conf ~/.tmux.conf

# fish
mkdir -p ~/.config/fish/functions
ln -sf ${DOT_DIR}/fish/config.fish ~/.config/fish/config.fish
ln -sf ${DOT_DIR}/fish/config-osx.fish ~/.config/fish/config-osx.fish
ln -sf ${DOT_DIR}/fish/functions/fish_prompt.fish ~/.config/fish/functions/fish_prompt.fish
