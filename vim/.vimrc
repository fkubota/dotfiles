" 
" 
" 
" 
" 
"        _                    
" __   _(_)_ __ ___  _ __ ___ 
" \ \ / / | '_ ` _ \| '__/ __|
"  \ V /| | | | | | | | | (__ 
" (_)_/ |_|_| |_| |_|_|  \___|
"                             
"

" 
" ------------ dein start
" プラグインがインストールされるディレクトリ
let s:dein_dir = expand('~/.cache/dein')
" dein.vim 本体がインストールされるディレクトリ
let s:dein_repo_dir = s:dein_dir . '/repos/github.com/Shougo/dein.vim'

" dein.vim がなければ github から落としてくる
if &runtimepath !~# '/dein.vim'
  if !isdirectory(s:dein_repo_dir)
    execute '!git clone https://github.com/Shougo/dein.vim' s:dein_repo_dir
  endif
  execute 'set runtimepath^=' . fnamemodify(s:dein_repo_dir, ':p')
endif

" 設定開始
if dein#load_state(s:dein_dir)
  call dein#begin(s:dein_dir)

  " プラグインリストを収めた TOML ファイル
  " 予め TOML ファイル（後述）を用意しておく
  let g:rc_dir    = expand('~/.vim/rc')
  let s:toml      = g:rc_dir . '/dein.toml'
  let s:lazy_toml = g:rc_dir . '/dein_lazy.toml'

  " TOML を読み込み、キャッシュしておく
  call dein#load_toml(s:toml,      {'lazy': 0})
  call dein#load_toml(s:lazy_toml, {'lazy': 1})

  " Add or remove your plugins here:
  call dein#add('Shougo/neosnippet.vim')
  call dein#add('Shougo/neosnippet-snippets')
  call dein#add('davidhalter/jedi-vim')
  call dein#add('cohama/lexima.vim')
  call dein#add('scrooloose/syntastic')
  call dein#add('ryanoasis/vim-devicons')

  " 設定終了
  call dein#end()
  call dein#save_state()
endif

" もし、未インストールものものがあったらインストール
if dein#check_install()
  call dein#install()
endif

call map(dein#check_clean(), "delete(v:val, 'rf')")
" ------------ dein end


" ===== basics =====
set number " 行番号
set hlsearch " 検索結果をハイライト
set shiftwidth=2 " インデント幅
set tabstop=4 " tab
set incsearch " インクリメンタルサーチ
nnoremap <C-k> :cprevious<CR>   " quickfix前へ
nnoremap <C-j> :cnext<CR>       " quickfix次へ
set autoindent " indent補完
nnoremap <ESC><ESC> :nohlsearch<CR><ESC> " esc2回でハイライトを消す
autocmd BufNewFile,BufRead *.py nnoremap <C-q> :!python3 % 


" color scheme
syntax on
colorscheme molokai
set t_Co=256
set cursorline " 現在行番号に色をつける
hi clear CursorLine " 現在行に色をつける
highlight CursorLine ctermbg=238
if !has('gui_running') " これないと背景透明ならない
  augroup seiya
    autocmd!
    autocmd VimEnter,ColorScheme * highlight Normal ctermbg=none
    autocmd VimEnter,ColorScheme * highlight LineNr ctermbg=none
    autocmd VimEnter,ColorScheme * highlight SignColumn ctermbg=none
    autocmd VimEnter,ColorScheme * highlight VertSplit ctermbg=none
    autocmd VimEnter,ColorScheme * highlight NonText ctermbg=none
  augroup END
endif


" lightline
set laststatus=2

" caw.vim (コメントアウトトグル)
nmap <C-_> <Plug>(caw:hatpos:toggle)
vmap <C-_> <Plug>(caw:hatpos:toggle)

" コメントの色だけ、colorschemeから変更
hi Comment ctermfg=245

" カーソルの形
if has('vim_starting')
    " 挿入モード時に非点滅の縦棒タイプのカーソル
    let &t_SI .= "\e[6 q"
    " ノーマルモード時に非点滅のブロックタイプのカーソル
    let &t_EI .= "\e[2 q"
    " 置換モード時に非点滅の下線タイプのカーソル
    let &t_SR .= "\e[4 q"
endif

" split
nnoremap s <Nop>
nnoremap s\| :<C-u>vs<CR><C-w>l
nnoremap s- :<C-u>sp<CR><C-w>j
nnoremap sj <C-w>j
nnoremap sk <C-w>k
nnoremap sl <C-w>l
nnoremap sh <C-w>h
nnoremap sL <C-w>>
nnoremap sH <C-w><
nnoremap sK <C-w>+
nnoremap sJ <C-w>-

" tab
nnoremap st :<C-u>tabnew<CR>
nnoremap sn gt
nnoremap sp gT

" ----- vimfiler -----
nmap sf :VimFilerBufferDir<Return>
nmap sF :VimFilerExplorer -find<Return>
nmap sb :Unite buffer<Return>
let g:vimfiler_as_default_explorer = 1
let g:vimfiler_safe_mode_by_default = 0
let g:vimfiler_enable_auto_cd = 0
let g:vimfiler_tree_leaf_icon = ''
let g:vimfiler_tree_opened_icon = '▾'
let g:vimfiler_tree_closed_icon = '▸'
let g:vimfiler_marked_file_icon = '✓'


" ale
let g:ale_linters = { 'python': ['flake8'] }


" preview markdown
let g:preview_markdown_vertical = 1
