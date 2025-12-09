# alias
alias cl="xclip -in -sel clip"
alias rl="readlink -f"
alias lf="find (pwd) -name"
alias '..'='cd ..'
alias '...'='cd ../..'
alias '....'='cd ../../..'
alias '.....'='cd ../../../..'
alias d='cd ~/Git'

# color 
set fish_color_command '#A0DDFF'
set fish_color_param '#FFAA55'
set fish_color_autosuggestion '#999999'

# vim 
# fish_vi_key_bindings
# function fish_mode_prompt
# end

# key_bindings
fish_default_key_bindings

# autojump
# begin
#     set --local AUTOJUMP_PATH $HOME/.autojump/share/autojump/autojump.fish
#     if test -e $AUTOJUMP_PATH
#         source $AUTOJUMP_PATH
#     end
# end

# fzf
# set -gx FZF_LEGACY_KEYBINDINGS 0
# set -gx FZF_CTRL_T_OPTS "--preview 'bat --color=always --style=header,grid --line-range :200 {}'"
# set -gx FZF_DEFAULT_OPTS "--height 80% --reverse --border"
# set -gx FZF_ALT_C_OPTS   "--preview 'tree -F -C {} | head -200'"
# function fish_user_key_bindings
#   bind \cr __fzf_history
# end
# function __fzf_history
#   history | fzf-tmux -d40% +s +m --tiebreak=index --query=(commandline -b) \
#     > /tmp/fzf
#   and commandline (cat /tmp/fzf)
# end


# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/fumihiro.kubota/google-cloud-sdk/path.fish.inc' ]; . '/Users/fumihiro.kubota/google-cloud-sdk/path.fish.inc'; end

# osx or linux
switch (uname)
  case Darwin
    source (dirname (status --current-filename))/config-osx.fish
	case Linux
    # Do nothing
end

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
if test -f /opt/homebrew/Caskroom/miniforge/base/bin/conda
    eval /opt/homebrew/Caskroom/miniforge/base/bin/conda "shell.fish" "hook" $argv | source
else
    if test -f "/opt/homebrew/Caskroom/miniforge/base/etc/fish/conf.d/conda.fish"
        . "/opt/homebrew/Caskroom/miniforge/base/etc/fish/conf.d/conda.fish"
    else
        set -x PATH "/opt/homebrew/Caskroom/miniforge/base/bin" $PATH
    end
end
# <<< conda initialize <<<

