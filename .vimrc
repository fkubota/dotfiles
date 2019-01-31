" dotfiles 内の *.vim が起動する
set runtimepath+=~/dotfiles/.vim
runtime! configs/users/*.vim
runtime! configs/plugins/*.vim

" lightline.vim の設定
set laststatus=2

