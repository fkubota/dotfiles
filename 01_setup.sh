# create directory
mkdir ~/.vim 
mkdir ~/.vim/rc 
# mkdir ~/.vim/colors

# dein のインストール
curl https//raw.githubusercontent.com/Shougo/dein.vim/master/bin/installer.sh > ~/installer.sh
sh ~/installer.sh ~/.cache

# flake8のインストール
pip3 install flake8


# tmux
mkdir -p /home/fkubota/.tmux/theme/
git clone https://github.com/arcticicestudio/nord-tmux.git ~/.tmux/themes/nord-tmux
