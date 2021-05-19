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
git clone git@github.com:fkubota/dotfiles.git ${DOT_DIR}

# vim
mkdir -p ~/.vim/rc/
ln -sf ~/Git/dotfiles/vim/.vimrc ~/.vimrc
ln -sf ~/Git/dotfiles/vim/rc/dein.toml ~/.vim/rc/dein.toml
ln -sf ~/Git/dotfiles/vim/rc/dein_lazy.toml ~/.vim/rc/dein_lazy.toml

# tmux
ln -sf ~/Git/dotfiles/tmux/.tmux.conf ~/.tmux.conf

# fish
mkdir -p ~/.config/fish/functions
ln -sf ~/Git/dotfiles/fish/config.fish ~/.config/fish/config.fish
ln -sf ~/Git/dotfiles/fish/config-osx.fish ~/.config/fish/config-osx.fish
ln -sf ~/Git/dotfiles/fish/functions/fish_prompt.fish ~/.config/fish/functions/fish_prompt.fish
