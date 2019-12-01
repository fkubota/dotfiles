#!/bin/bash

#set -u
#cd ~/Git/dotfiles
### 実行場所のディレクトリを取得
#THIS_DIR=$(cd $(dirname $0); pwd)
#
#cd $THIS_DIR
#git submodule init
#git submodule update
#
#echo "start setup..."
#for f in .??*; do
#    [ "$f" = ".git" ] && continue
#    [ "$f" = ".gitconfig.local.template" ] && continue
#    [ "$f" = ".require_oh-my-zsh" ] && continue
#    [ "$f" = ".gitmodules" ] && continue
#
#    ln -snfv ~/Git/dotfiles/"$f" ~/
#done
#
# # [ -e ~/.gitconfig.local ] || cp ~/Git/dotfiles/.gitconfig.local.template ~/.gitconfig.local
#
#cat << END
#
#**************************************************
#DOTFILES SETUP FINISHED! bye.
#**************************************************

END
