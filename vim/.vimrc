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
  call dein#add('cohama/lexima.vim')
  call dein#add('ryanoasis/vim-devicons')
  call dein#add('airblade/vim-gitgutter')
  call dein#add('tpope/vim-fugitive')
  call dein#add('jmcantrell/vim-virtualenv')
  call dein#add('ervandew/supertab')
  " call dein#add('davidhalter/jedi-vim')
	" call dein#add('w0rp/ale')
  call dein#add('ctrlpvim/ctrlp.vim')
  call dein#add('posva/vim-vue')
	call dein#add('arcticicestudio/nord-vim')
	call dein#add('prabirshrestha/vim-lsp')
	call dein#add('mattn/vim-lsp-settings')
	call dein#add('prabirshrestha/asyncomplete.vim')
	call dein#add('prabirshrestha/asyncomplete-lsp.vim')

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
set tabstop=2 " tab
set incsearch " インクリメンタルサーチ
set pastetoggle=<F2> " set paste & set nopaste のトグル
set backspace=indent,eol,start  " macでbackspaceが使えるように
set wildmenu
" set clipboard+=unnamed  " ヤンク、プットでクリップボードが使えるようになる
hi Visual term=reverse cterm=reverse
nnoremap <C-k> :cprevious<CR>   " quickfix前へ
nnoremap <C-j> :cnext<CR>       " quickfix次へ
inoremap <C-o> <C-x><C-f>
nnoremap <ESC><ESC> :nohlsearch<CR><ESC> " esc2回でハイライトを消す
autocmd BufNewFile,BufRead *.py nnoremap <C-q> :!python3 %  
autocmd BufNewFile,BufRead * nnoremap <C-l> :so ~/.vimrc  
autocmd BufNewFile,BufRead * nnoremap <C-t> :term ++curwin <CR> 
autocmd BufNewFile,BufRead *.vue set filetype=html          " vueファイル
autocmd BufNewFile,BufRead *.html nnoremap <C-q> :!vivaldi % 
nmap sd :vert diffsplit 

"""""""""""""""""""""""""
"      インデント
""""""""""""""""""""""""
" set autoindent          "改行時に前の行のインデントを計測
" set smartindent         "改行時に入力された行の末尾に合わせて次の行のインデントを増減する 
" set smarttab            "新しい行を作った時に高度な自動インデントを行う
" set expandtab           "タブ入力を複数の空白に置き換える 
" set tabstop=2           "タブを含むファイルを開いた際, タブを何文字の空白に変換するか
" set shiftwidth=2        "自動インデントで入る空白数
" set softtabstop=0       "キーボードから入るタブの数
if has("autocmd")
  "ファイルタイプの検索を有効にする
  filetype plugin on
  "ファイルタイプに合わせたインデントを利用
  filetype indent on
  "sw=softtabstop, sts=shiftwidth, ts=tabstop, et=expandtabの略
  autocmd FileType c           setlocal sw=4 sts=4 ts=4 et
  autocmd FileType html        setlocal sw=2 sts=2 ts=2 et
  autocmd FileType js          setlocal sw=4 sts=4 ts=4 et
  autocmd FileType python      setlocal sw=4 sts=4 ts=4 et
  autocmd FileType json        setlocal sw=4 sts=4 ts=4 et
  autocmd FileType css         setlocal sw=4 sts=4 ts=4 et
  autocmd FileType javascript  setlocal sw=2 sts=2 ts=2 et
  autocmd FileType vue   			 setlocal sw=2 sts=2 ts=2 et
endif


" color scheme
syntax on
colorscheme nord
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


" " lightline
" set laststatus=2
" let g:lightline = {
"      \ 'colorscheme': 'seoul256'
"      \ }

" statusline
set laststatus=2  "statusline を常に表示
set statusline=%F
hi StatusLine ctermbg=10 ctermfg=black cterm=NONE
hi StatusLineNC ctermbg=66 ctermfg=black cterm=NONE
hi StatusLineTerm ctermbg=10 ctermfg=black cterm=NONE
hi StatusLineTermNC ctermbg=66 ctermfg=black cterm=NONE

" selected textの色
hi Visual term=reverse cterm=reverse

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
nnoremap s= <C-w>=
nnoremap sj <C-w>j
nnoremap sk <C-w>k
nnoremap sl <C-w>l
nnoremap sh <C-w>h
nnoremap sL <C-w>>
nnoremap sH <C-w><
nnoremap sK <C-w>+
nnoremap sJ <C-w>-
nnoremap s> <C-w>x<C-w>l
nnoremap s< <C-w>h<C-w><C-x>

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

" ctrlp
let g:ctrlp_max_height = 40
let g:ctrlp_show_hidden = 1
let g:ctrlp_match_window = 'order:ttb'


" vim-lsp[basic]
let g:lsp_diagnostics_echo_cursor = 1
nnoremap K :<C-u>LspHover<CR>
nnoremap <LocalLeader>s :<C-u>LspDocumentFormat<CR> " テキスト整形
nnoremap gd :<C-u>LspDefinition<CR>
nnoremap gD :<C-u>LspReferences<CR>
nnoremap gs :<C-u>LspDocumentSymbol<CR>
nnoremap gS :<C-u>LspWorkspaceSymbol<CR>
" inoremap <buffer> <expr><c-e> lsp#scroll(+4)
" inoremap <buffer> <expr><c-y> lsp#scroll(-4)
autocmd User lsp_float_opened inoremap <buffer> <expr><down> lsp#scroll(+2)
autocmd User lsp_float_opened inoremap <buffer> <expr><up> lsp#scroll(-2)
autocmd User lsp_float_opened nnoremap <buffer> <expr><down> lsp#scroll(+2)
autocmd User lsp_float_opened nnoremap <buffer> <expr><up> lsp#scroll(-2)

" vim-lsp[python]
" flake8のmax-line-length = 120 は ~/.config/flake8 に↓をかけばよい
" [flake8]
" max-line-length = 120 
let g:lsp_settings = {
\   'pyls-all': {
\     'workspace_config': {
\       'pyls': {
\         'configurationSources': ['flake8'],
\ 					},
\       },
\     },
\}
