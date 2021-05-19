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

has() {
    type "$1" > /dev/null 2>&1
}

if [ ! -d ${DOT_DIR} ]; then
    git clone https://github.com/fkubota/dotfiles.git ${DOT_DIR}

    cd ${DOT_DIR}
    for f in *;
    do
        [[ "$f" == ".git" ]] && continue
        [[ "$f" == ".gitignore" ]] && continue
        [[ "$f" == ".DS_Store" ]] && continue
        [[ "$f" == "README.md" ]] && continue
        [[ "$f" == "install.sh" ]] && continue
        [[ "$f" == "LICENSE" ]] && continue

        ln -snf $DOT_DIR/"$f" $HOME/".$f"
        echo "Installed $HOME/.$f"
    done
		mkdir $HOME/.config
    ln -sf "${DOT_DIR}/config/fish" "$HOME/.config/fish"
else
    echo "dotfiles already exists"
    exit 1
fi
