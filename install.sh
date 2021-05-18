#!/bin/bash

# ::setup::
# dein のインストール
curl https//raw.githubusercontent.com/Shougo/dein.vim/master/bin/installer.sh > ~/installer.sh
sh ~/installer.sh ~/.cache

# flake8のインストール
pip3 install flake8 --user

# tmux
mkdir -p /home/fkubota/.tmux/theme/
git clone https://github.com/arcticicestudio/nord-tmux.git ~/.tmux/themes/nord-tmux


# ::シンボリックリンク::
DOT_DIR="$HOME/Git/dotfiles"

has() {
    type "$1" > /dev/null 2>&1
}

if [ ! -d ${DOT_DIR} ]; then
    if has "git"; then
        git clone https://github.com/fkubota/dotfiles.git ${DOT_DIR}
    elif has "curl" || has "wget"; then
        TARBALL="https://github.com/fkubota/dotfiles/archive/master.tar.gz"
        if has "curl"; then
            curl -L ${TARBALL} -o master.tar.gz
        else
            wget ${TARBALL}
        fi
        tar -zxvf master.tar.gz
        rm -f master.tar.gz
        mv -f dotfiles-master "${DOT_DIR}"
    else
        echo "curl or wget or git required"
        exit 1
    fi

    cd ${DOT_DIR}
    for f in *;
    do
        [[ "$f" == ".git" ]] && continue
        [[ "$f" == ".gitignore" ]] && continue
        [[ "$f" == ".DS_Store" ]] && continue
        [[ "$f" == "README.md" ]] && continue
        [[ "$f" == "install.sh" ]] && continue
        [[ "$f" == "LICENSE" ]] && continue

        ln -snf $DOT_DIR/"$f" $HOME/"$f"
        echo "Installed $f"
    done
else
    echo "dotfiles already exists"
    exit 1
fi
