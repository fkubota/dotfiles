"プラグインが実際にインストールされるディレクトリ                                                                                                                               
let s:dein_dir = expand('~/dotfiles/.vim/dein')
" dein.vim 本体
let s:dein_repo_dir = s:dein_dir . '/repos/github.com/Shougo/dein.vim'


" dein.vim がなければ github から落としてくる
if &runtimepath !~# '/dein.vim'
 if !isdirectory(s:dein_repo_dir)
  execute '!git clone https://github.com/Shougo/dein.vim' s:dein_repo_dir
 endif
 execute 'set runtimepath^=' . s:dein_repo_dir
endif

" 設定開始
if dein#load_state(s:dein_dir)
 call dein#begin(s:dein_dir)

 " プラグインリストを収めた TOML ファイル
 " ~/.vim/configs/plugins/dein.toml,deinlazy.tomlを用意する
 let g:rc_dir    = expand('~/dotfiles/.vim/configs/plugins/install')
 let s:toml      = g:rc_dir . '/dein.toml'
 let s:lazy_toml = g:rc_dir . '/dein_lazy.toml'

 " TOML を読み込み、キャッシュしておく
 call dein#load_toml(s:toml,      {'lazy': 0})
 call dein#load_toml(s:lazy_toml, {'lazy': 1})

 " 設定終了
 call dein#end()
 call dein#save_state()
endif

" もし、未インストールものものがあったらインストール
if dein#check_install()
 call dein#install()
endif

filetype plugin indent on
